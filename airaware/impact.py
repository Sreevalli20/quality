"""Environmental Impact Calculator.

All factors are documented estimates with stated assumptions. Results are
labelled as estimates - never as measured reductions. CO2e savings from
transport are NOT the same as PM2.5 reductions; the UI states this
distinction explicitly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Emission factors (kg CO2e per vehicle-km unless noted)
# Sources/assumptions documented for transparency:
# - Tailpipe CO2 factors approximated from IPCC 2006 Guidelines default
#   fuel CO2 factors and typical Indian fuel economy; well-to-wheel
#   upstream emissions are partially included via multipliers.
# - Indian grid average CO2 intensity ~0.82 kg CO2/kWh (CEA generation
#   mix estimate); user may override with their DISCOM figure.
# ---------------------------------------------------------------------------

VEHICLE_FACTORS: dict[str, dict] = {
    "car_petrol": {"label": "Petrol car", "kg_co2e_per_km": 0.192,
                   "fuel": "petrol", "note": "Typical ~18 km/l, ~2.3 kg CO2/l petrol + upstream."},
    "car_diesel": {"label": "Diesel car", "kg_co2e_per_km": 0.171,
                   "fuel": "diesel", "note": "Typical ~20 km/l diesel."},
    "car_ev": {"label": "Electric car", "kg_co2e_per_km": 0.095,
               "fuel": "electricity", "note": "Grid-dependent; assumes ~0.82 kg CO2/kWh."},
    "bike_petrol": {"label": "Petrol scooter/bike", "kg_co2e_per_km": 0.075,
                    "fuel": "petrol", "note": "Typical ~45 km/l."},
    "auto_cng": {"label": "CNG auto-rickshaw", "kg_co2e_per_km": 0.055,
                 "fuel": "cng", "note": "Per vehicle-km; typically 1-3 passengers."},
    "bus": {"label": "Public bus", "kg_co2e_per_km": 0.040,
            "fuel": "diesel/cng", "note": "Per passenger-km at typical occupancy."},
    "metro": {"label": "Metro/suburban rail", "kg_co2e_per_km": 0.020,
              "fuel": "electricity", "note": "Per passenger-km; highly efficient."},
    "cycle": {"label": "Bicycle", "kg_co2e_per_km": 0.0, "fuel": "human", "note": "Zero tailpipe emissions."},
    "walk": {"label": "Walking", "kg_co2e_per_km": 0.0, "fuel": "human", "note": "Zero emissions."},
}

DEFAULT_FUEL_PRICE_INR_PER_LITRE = {
    "petrol": 104.0, "diesel": 90.0, "cng": 75.0, "electricity": None,
}

# Typical fuel economy (km per litre) used ONLY when the user does not
# supply their own - clearly an assumption.
DEFAULT_KM_PER_LITRE = {
    "car_petrol": 18.0, "car_diesel": 20.0, "bike_petrol": 45.0,
    "auto_cng": 30.0, "bus": None, "metro": None,
    "car_ev": None, "cycle": None, "walk": None,
}

# Electricity CO2 intensity for EVs / AC savings
INDIAN_GRID_KG_CO2_PER_KWH = 0.82
AC_TYPICAL_POWER_KW = 1.5   # typical 1.5-ton split AC draw at setpoint


@dataclass
class ImpactAction:
    """One logged sustainable action."""
    action_type: str        # 'trip' | 'energy'
    description: str
    vehicle: Optional[str] = None       # for trip actions
    distance_km: float = 0.0            # for trip actions
    avoided_vehicle: Optional[str] = None  # vehicle NOT used (for trip actions)
    kwh_saved: float = 0.0              # for energy actions
    cost_saved_inr: Optional[float] = None
    date: str = ""

    def co2e_kg(self) -> float:
        if self.action_type == "trip":
            if not self.vehicle or not self.avoided_vehicle:
                return 0.0
            new = VEHICLE_FACTORS.get(self.vehicle, {}).get("kg_co2e_per_km", 0)
            old = VEHICLE_FACTORS.get(self.avoided_vehicle, {}).get("kg_co2e_per_km", 0)
            return max(0.0, (old - new)) * self.distance_km
        if self.action_type == "energy":
            return self.kwh_saved * INDIAN_GRID_KG_CO2_PER_KWH
        return 0.0

    def as_dict(self):
        return asdict(self)


def estimate_trip_savings(new_mode: str, avoided_mode: str, distance_km: float,
                          fuel_price_inr_litre: Optional[float] = None,
                          km_per_litre: Optional[float] = None) -> dict:
    """Estimate CO2e and fuel-cost savings for replacing one trip mode."""
    if new_mode not in VEHICLE_FACTORS or avoided_mode not in VEHICLE_FACTORS:
        raise ValueError("Unknown vehicle mode.")
    if distance_km <= 0:
        raise ValueError("Distance must be positive.")

    new_f = VEHICLE_FACTORS[new_mode]["kg_co2e_per_km"]
    old_f = VEHICLE_FACTORS[avoided_mode]["kg_co2e_per_km"]
    co2e_saved = (old_f - new_f) * distance_km

    fuel_saving_litres: Optional[float] = None
    fuel_cost_saving: Optional[float] = None
    fuel = VEHICLE_FACTORS[avoided_mode].get("fuel")
    kpl = km_per_litre if km_per_litre else DEFAULT_KM_PER_LITRE.get(avoided_mode)
    price = fuel_price_inr_litre or DEFAULT_FUEL_PRICE_INR_PER_LITRE.get(fuel or "")
    if kpl and price and fuel not in ("electricity", "human", None):
        fuel_saving_litres = distance_km / kpl
        fuel_cost_saving = fuel_saving_litres * price

    return {
        "co2e_saved_kg": round(co2e_saved, 2),
        "fuel_saved_litres": (round(fuel_saving_litres, 2)
                              if fuel_saving_litres is not None else None),
        "fuel_cost_saved_inr": (round(fuel_cost_saving, 0)
                                if fuel_cost_saving is not None else None),
        "assumptions": {
            "avoided_mode": VEHICLE_FACTORS[avoided_mode]["label"],
            "new_mode": VEHICLE_FACTORS[new_mode]["label"],
            "distance_km": distance_km,
            "avoided_factor": old_f,
            "new_factor": new_f,
            "km_per_litre_used": kpl,
            "fuel_price_used": price,
            "note": ("Estimate based on generic factors; your real savings "
                     "depend on vehicle, driving style and occupancy. The "
                     "new mode's own cost (fare/toll/electricity) is NOT "
                     "subtracted - 'fuel saved' refers to the avoided "
                     "vehicle only."),
        },
    }


def estimate_ac_savings(hours_saved: float, ac_power_kw: float = AC_TYPICAL_POWER_KW
                        ) -> dict:
    """Estimate savings from running the AC 'hours_saved' fewer per day."""
    if hours_saved < 0:
        raise ValueError("Hours saved cannot be negative.")
    kwh_per_day = ac_power_kw * hours_saved
    kwh_per_year = kwh_per_day * 365
    co2e_kg_year = kwh_per_year * INDIAN_GRID_KG_CO2_PER_KWH
    # Indicative tariff ~ Rs 8/kWh (national average domestic slab varies)
    cost_inr_year = kwh_per_year * 8.0
    return {
        "kwh_saved_per_day": round(kwh_per_day, 2),
        "kwh_saved_per_year": round(kwh_per_year, 0),
        "co2e_saved_kg_per_year": round(co2e_kg_year, 0),
        "indicative_cost_saved_inr_per_year": round(cost_inr_year, 0),
        "assumptions": {
            "ac_power_kw": ac_power_kw,
            "grid_co2_kg_per_kwh": INDIAN_GRID_KG_CO2_PER_KWH,
            "tariff_rs_per_kwh": 8.0,
            "note": "AC power draw varies 0.8-2.5 kW by size/star rating; "
                    "tariff varies by DISCOM and slab.",
        },
    }


def summarise_actions(actions: list[ImpactAction]) -> dict:
    """Aggregate logged actions into a progress summary."""
    total_co2e = sum(a.co2e_kg() for a in actions)
    trip_km = sum(a.distance_km for a in actions if a.action_type == "trip")
    cost = sum(a.cost_saved_inr or 0 for a in actions)
    by_type: dict[str, int] = {}
    for a in actions:
        by_type[a.action_type] = by_type.get(a.action_type, 0) + 1
    return {
        "total_actions": len(actions),
        "total_co2e_saved_kg": round(total_co2e, 2),
        "total_co2e_saved_tonnes": round(total_co2e / 1000, 3),
        "trip_km": round(trip_km, 1),
        "indicative_cost_saved_inr": round(cost, 0),
        "by_type": by_type,
    }


def actions_to_csv(actions: list[ImpactAction]) -> str:
    """Serialise actions to CSV for download."""
    import csv
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(ImpactAction.__dataclass_fields__))
    writer.writeheader()
    for a in actions:
        writer.writerow(a.as_dict())
    return buf.getvalue()
