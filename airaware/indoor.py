"""Indoor Air Guardian - curated, practical indoor air quality guidance.

Content is organised by room and budget tier. All recommendations are
qualitative and practical; no unsupported health claims are made.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Budget tiers (indicative INR ranges, clearly labelled as approximate)
# ---------------------------------------------------------------------------

BUDGET_TIERS = {
    "free": {
        "label": "Free improvements",
        "range": "Rs 0",
        "items": [
            "Ventilate smartly: open windows only when outdoor AQI is Good/Satisfactory; time it for 10-15 minutes.",
            "Use exhaust fans while cooking; keep the kitchen door closed if possible.",
            "Switch to LPG or induction cooking if you currently burn wood/coal/kerosene indoors.",
            "Wet-mop and damp-dust weekly instead of dry sweeping.",
            "Avoid smoking, incense, candles and aerosol sprays indoors.",
            "Keep doors/windows closed during dust storms and peak traffic hours.",
            "Choose fragrance-free, low-VOC cleaning products.",
            "Let fresh-air enter via windows away from roads and construction sites.",
        ],
    },
    "low": {
        "label": "Low-cost improvements",
        "range": "~Rs 500 - 5,000",
        "items": [
            "Door draft excluders to reduce infiltration of polluted outdoor air.",
            "Washable HVAC/pre-filter wraps for window AC units.",
            "Bamboo or HEPA-type DIY box-fan filter (Corsi-Rosenthal style) for single rooms.",
            "Microfibre cloths and a good vacuum with a HEPA filter bag.",
            "Indoor herb garden (basil, mint) for cooking - culinary, not an air purifier.",
        ],
    },
    "moderate": {
        "label": "Moderate investments",
        "range": "~Rs 5,000 - 25,000",
        "items": [
            "HEPA air purifier sized to the room (check CADR vs room volume).",
            "Kitchen chimney/exhaust upgrade if cooking generates smoke.",
            "MERV-13 or higher filter upgrade for central AC systems.",
            "Dehumidifier if dampness/mould is an issue.",
        ],
    },
    "high": {
        "label": "Higher-cost equipment",
        "range": "~Rs 25,000+",
        "items": [
            "Whole-home ventilation with heat recovery (HRV/ERV).",
            "Commercial-grade HEPA filtration for large open spaces.",
            "Continuous indoor PM2.5 monitor to verify what actually works.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Room-specific recommendations
# ---------------------------------------------------------------------------

@dataclass
class RoomAdvice:
    name: str
    icon: str
    priorities: list[str]
    notes: str


ROOMS: list[RoomAdvice] = [
    RoomAdvice(
        name="Bedroom",
        icon="bed",
        priorities=[
            "This is your longest exposure window - prioritise a purifier here.",
            "Keep the door closed at night to limit hallway dust and kitchen fumes.",
            "Wash bedding weekly in hot water; encase pillows/mattresses if dust-mite allergy is a concern.",
            "Avoid candles, incense and essential-oil diffusers in the sleeping space.",
            "On clean-air days, ventilate before sleep rather than overnight if outdoor levels are rising.",
        ],
        notes="Sleep occupies ~8 hours/day; particle dose here is cumulative.",
    ),
    RoomAdvice(
        name="Living room",
        icon="sofa",
        priorities=[
            "High-traffic area: place a doormat and remove shoes at the door - shoes track in dust and particles.",
            "Vacuum upholstery and curtains regularly; they hold resuspendable dust.",
            "If using a fireplace/space heater, ensure it is vented and never burn treated wood indoors.",
            "Keep electronic devices dust-free; clean vents with a damp cloth.",
        ],
        notes="Shared space - habits of every member affect the air everyone breathes.",
    ),
    RoomAdvice(
        name="Kitchen",
        icon="pot",
        priorities=[
            "Use the exhaust fan/chimney every time you cook - frying generates the most particles.",
            "Prefer pressure cooking, steaming or boiling over deep frying.",
            "Never use the oven/stove for room heating; combustion without venting is dangerous.",
            "Switch biomass/kerosene cooking to LPG or induction where possible.",
            "Keep the kitchen door closed while cooking if the rest of the home is being kept clean.",
        ],
        notes="Cooking can be the single largest indoor PM2.5 source in Indian homes.",
    ),
    RoomAdvice(
        name="Study room",
        icon="book",
        priorities=[
            "Long study sessions = sustained breathing zone exposure; place a purifier near the desk.",
            "Ensure good task lighting so windows are not opened just for light on polluted days.",
            "Store books/papers in closed shelves to reduce settled dust resuspension.",
            "A small indoor plant (e.g. money plant) may improve wellbeing but will NOT purify air - do not rely on it.",
        ],
        notes="Concentration and productivity drop with elevated CO2 and particles; a purifier helps comfort.",
    ),
    RoomAdvice(
        name="Children's room",
        icon="child",
        priorities=[
            "Children are more vulnerable: keep this room as clean and filtered as possible.",
            "Remove plush toys from the bed during pollution episodes or wash them weekly.",
            "Avoid aerosol air fresheners, scented candles and mosquito coils in this room.",
            "Check that the purifier's airflow does not blow directly on the child's face.",
        ],
        notes="Children breathe more air per kilogram of body weight than adults.",
    ),
]


# ---------------------------------------------------------------------------
# Ventilation decision guidance
# ---------------------------------------------------------------------------

def ventilation_advice(category_name: str | None) -> tuple[str, str]:
    """Return (headline, detail) for whether to ventilate now."""
    clean = category_name in ("Good", "Satisfactory", None)
    if clean:
        return (
            "Ventilation is helpful now",
            ("Outdoor air is relatively clean. Open windows for 10-15 minutes "
            "to flush accumulated indoor pollutants (cooking fumes, dust, "
            "cleaning-product vapours). Cross-ventilation works best."),
        )
    if category_name == "Moderate":
        return (
            "Ventilate selectively",
            ("Outdoor air is Moderate. Short ventilation bursts (5-10 min) in "
            "the cleanest part of the day are acceptable; otherwise rely on "
            "filtration and recirculated air."),
        )
    return (
        "Keep windows closed",
        (f"Outdoor AQI is {category_name}. Opening windows imports polluted "
        "air faster than indoor sources are removed. Use filtration "
        "(purifier/AC filter) and recirculated air instead."),
    )
