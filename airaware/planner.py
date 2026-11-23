"""Personalised daily routine planner.

Generates time-of-day guidance from the current AQI category. It never
claims a specific hour has lower pollution unless time-stamped
measurements support it - guidance is framed as "given current
conditions" rather than predicted hourly levels.
"""

from __future__ import annotations

from dataclasses import dataclass

from .aqi import is_outdoor_safe
from .data import MeasurementSet

TIME_SLOTS = [
    ("morning", "Morning (6-9 AM)", "Wake-up & breakfast"),
    ("commute_am", "Commute to work/study (9-11 AM)", "Travel to work or college"),
    ("midday", "Midday (12-3 PM)", "Work/study or outdoor activity window"),
    ("commute_pm", "Return commute (5-7 PM)", "Travel home"),
    ("evening", "Evening (7-9 PM)", "Exercise, errands, family time"),
    ("night", "Night (9 PM - 6 AM)", "Sleep & recovery"),
]


@dataclass
class PlanItem:
    slot_key: str
    slot_label: str
    focus: str
    guidance: str
    indoor_friendly: bool = True


def build_daily_plan(m: MeasurementSet, outdoor_pref: str = "moderate",
                     has_children: bool = False) -> list[PlanItem]:
    """Return an ordered list of PlanItems for the day."""
    cat = m.category_name or "Good"
    heavy_ok, heavy_msg = is_outdoor_safe(cat, "heavy")
    mod_ok, mod_msg = is_outdoor_safe(cat, "moderate")
    light_ok, _ = is_outdoor_safe(cat, "light")

    poor_plus = cat in ("Poor", "Very Poor", "Severe", "Severe+")
    moderate_plus = cat in ("Moderate", "Poor", "Very Poor", "Severe", "Severe+")

    plan: list[PlanItem] = []

    # Morning
    if moderate_plus:
        g = ("Keep windows closed overnight if pollution is elevated; use "
             "recirculated AC/fans. Check today's AQI before planning outdoor "
             "chores like sweeping or gardening.")
    else:
        g = ("Good conditions for airing out rooms - open windows 10-15 min "
             "to flush overnight indoor pollutants.")
    plan.append(PlanItem("morning", TIME_SLOTS[0][1], TIME_SLOTS[0][2], g))

    # Morning commute
    if poor_plus:
        g = ("If you must travel, use closed windows with AC recirculation, "
             "prefer metro/bus over two-wheeler (less direct exhaust "
             "exposure), and avoid stopping in traffic longer than needed. "
             "If travel is optional, defer it.")
    else:
        g = ("Normal commute fine. For two-wheeler riders, a well-fitted "
             "mask is still sensible near traffic.")
    plan.append(PlanItem("commute_am", TIME_SLOTS[1][1], TIME_SLOTS[1][2], g))

    # Midday - outdoor activity window
    if heavy_ok:
        g = (f"Outdoor exercise is fine today ({heavy_msg}). This is the best "
             "window for runs or sports.")
    elif mod_ok:
        g = ("Moderate-intensity outdoor activity is acceptable; save "
             "high-intensity sessions for a cleaner day or move indoors.")
    else:
        g = ("Move planned exercise indoors (home workout, gym, yoga). "
             "Outdoor exertion now means inhaling several times more "
             "pollutant per minute than at rest.")
    plan.append(PlanItem("midday", TIME_SLOTS[2][1], TIME_SLOTS[2][2], g,
                         indoor_friendly=not heavy_ok))

    # Afternoon / return commute
    if moderate_plus:
        g = ("Keep vehicle windows up in traffic; combine any remaining "
             "errands into this trip rather than making a separate one - "
             "fewer trips means less exposure and emissions.")
    else:
        g = ("Standard commute. Walking or cycling short segments is a good "
             "choice - conditions are fine for active travel.")
    plan.append(PlanItem("commute_pm", TIME_SLOTS[3][1], TIME_SLOTS[3][2], g))

    # Evening
    if has_children and poor_plus:
        g = ("Keep children's outdoor play indoors or in a well-ventilated "
             "but filtered space. Indoor games, reading or screen-free "
             "activities work well.")
    elif poor_plus:
        g = ("Evening is typically when people are outdoors - choose indoor "
             "alternatives today: cooking together, indoor hobbies, family "
             "time inside.")
    elif moderate_plus:
        g = ("Short gentle outdoor time is fine (walking, sitting in a park "
             "away from traffic), but skip strenuous evening exercise.")
    else:
        g = ("Enjoy the outdoors - conditions are good for walking, cycling "
             "or playground time.")
    plan.append(PlanItem("evening", TIME_SLOTS[4][1], TIME_SLOTS[4][2], g,
                         indoor_friendly=poor_plus))

    # Night
    if moderate_plus:
        g = ("Sleep is your longest exposure window. Keep bedroom windows "
             "closed, run a purifier if you have one, and keep the room "
             "cool with recirculated AC rather than open windows.")
    else:
        g = ("Normal ventilation overnight is fine. A slightly cooler, "
             "well-ventilated room supports better sleep.")
    plan.append(PlanItem("night", TIME_SLOTS[5][1], TIME_SLOTS[5][2], g))

    return plan


def plan_summary(plan: list[PlanItem]) -> tuple[int, int]:
    """Return (indoor_friendly_slots, total_slots) counts."""
    return sum(1 for p in plan if p.indoor_friendly), len(plan)
