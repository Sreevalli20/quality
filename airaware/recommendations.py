"""Transparent, rule-based personal recommendation engine.

No external AI service is used. Recommendations are derived deterministically
from the CPCB AQI category, dominant pollutant and user profile. Every
recommendation carries an explicit reason so the logic is auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .aqi import is_outdoor_safe
from .data import MeasurementSet


@dataclass
class UserProfile:
    """Context collected from the user in the assistant page."""

    city: str = ""
    lifestyle: str = "office"          # office | student | runner | parent | shift_worker | retired
    transport: str = "car"             # car | bike | bus | metro | cycle | walk | mixed
    household: str = "alone"           # alone | family | children | elderly
    outdoor_pref: str = "moderate"     # light | moderate | heavy
    concerns: list[str] = field(default_factory=list)  # health | commute | kids | cost | exercise
    budget: str = "low"                # free | low | moderate | high
    priority: str = "health"           # health | cost | convenience | environment

    def summary(self) -> str:
        return (f"{self.lifestyle.replace('_', ' ')} in {self.city or 'your area'}, "
                f"mainly {self.transport.replace('_', ' ')}, household: "
                f"{self.household.replace('_', ' ')}.")


@dataclass
class Recommendation:
    title: str
    detail: str
    reason: str
    group: str = "today"   # today | avoid | alternatives | indoor | why | next_steps
    priority: int = 2      # 1 high, 2 medium, 3 low

    def as_dict(self):
        return {"title": self.title, "detail": self.detail,
                "reason": self.reason, "group": self.group,
                "priority": self.priority}


_CATEGORY_ORDER = ["Good", "Satisfactory", "Moderate", "Poor",
                   "Very Poor", "Severe", "Severe+"]


def _cat_index(name: Optional[str]) -> int:
    try:
        return _CATEGORY_ORDER.index(name or "Good")
    except ValueError:
        return 0


def _idx_ge(category: Optional[str], target: str) -> bool:
    return _cat_index(category) >= _cat_index(target)


def generate_recommendations(m: MeasurementSet,
                             profile: UserProfile) -> dict[str, list[Recommendation]]:
    """Build grouped recommendations for a measurement + profile."""
    cat_name = m.category_name or "Good"
    aqi = m.display_aqi or 0
    dominant = m.result.dominant_pollutant if m.result else None
    recs: dict[str, list[Recommendation]] = {
        "understanding": [], "today": [], "avoid": [],
        "alternatives": [], "indoor": [], "next_steps": [],
    }

    # ---- A. Understanding the situation ------------------------------------
    recs["understanding"].append(Recommendation(
        title=f"Current air quality: {cat_name}",
        detail=(f"AQI ≈ {aqi:.0f} for {m.location or 'your location'} "
                f"(source: {m.source_label})."),
        reason="Summary of the measurement used for all recommendations.",
        group="understanding", priority=1))
    if dominant and m.result:
        dom = next(r for r in m.result.pollutant_results
                   if r.pollutant == dominant)
        recs["understanding"].append(Recommendation(
            title=f"Dominant pollutant: {dom.label}",
            detail=(f"{dom.concentration:g} {dom.unit} is producing the highest "
                    f"sub-index ({dom.sub_index:.0f}), so it drives the overall AQI."),
            reason="CPCB defines overall AQI as the maximum pollutant sub-index.",
            group="understanding", priority=2))
    if m.is_sample:
        recs["understanding"].append(Recommendation(
            title="This is demonstration data",
            detail=("The numbers shown come from the labelled sample dataset, "
                    "not a live monitor. Enter your own measurements or import a "
                    "CSV for personalised guidance."),
            reason="Transparency about data provenance.",
            group="understanding", priority=1))

    # ---- B. What to do today ----------------------------------------------
    safe, safe_msg = is_outdoor_safe(cat_name, profile.outdoor_pref)
    if safe:
        recs["today"].append(Recommendation(
            title="Outdoor activity is acceptable",
            detail=safe_msg,
            reason=f"AQI category '{cat_name}' is within the safe range for "
                   f"{profile.outdoor_pref} activity.",
            group="today", priority=2))
    else:
        recs["today"].append(Recommendation(
            title="Move exercise and long outdoor stays indoors",
            detail=(f"{safe_msg} Indoor workouts, gyms or home exercise are "
                    "the healthier choice today."),
            reason="Higher ventilation rates during exercise increase the dose "
                   "of pollutants inhaled per minute.",
            group="today", priority=1))

    if _idx_ge(cat_name, "Moderate"):
        recs["today"].append(Recommendation(
            title="Keep windows closed during peak pollution hours",
            detail=("If outdoor AQI is Moderate or worse, opening windows "
                    "imports polluted air. Use fans/AC in recirculation mode "
                    "instead."),
            reason="Outdoor PM2.5 readily penetrates indoors through open "
                   "windows and doors.",
            group="today", priority=2))
    if _idx_ge(cat_name, "Poor"):
        recs["today"].append(Recommendation(
            title="Wear an N95/KN95 mask for unavoidable outdoor exposure",
            detail=("A properly fitted N95 or KN95 respirator reduces "
                    "inhaled particle exposure. Cloth masks help with large "
                    "particles only; surgical masks are not rated for PM2.5."),
            reason="Fine particles (PM2.5) pass through loose-fitting masks; "
                   "N95/KN95 filter at least 95% of 0.3-micron particles.",
            group="today", priority=1))
    if _idx_ge(cat_name, "Very Poor"):
        recs["today"].append(Recommendation(
            title="Vulnerable members should stay indoors",
            detail=("Children, elderly, pregnant women and people with asthma, "
                    "heart or lung disease should minimise all outdoor time "
                    "today, even for short trips."),
            reason="CPCB health advisories flag severe risk for sensitive "
                   "groups at Very Poor and above.",
            group="today", priority=1))

    # ---- C. What to avoid -----------------------------------------------
    if _idx_ge(cat_name, "Moderate"):
        recs["avoid"].append(Recommendation(
            title="Avoid burning waste, leaves or incense indoors",
            detail=("Combustion adds PM2.5 directly to your indoor air - the "
                    "worst possible time to add to the load."),
            reason="Incomplete combustion produces fine particles that are "
                   "especially harmful indoors where exposure is concentrated.",
            group="avoid", priority=2))
        recs["avoid"].append(Recommendation(
            title="Do not add outdoor exercise 'to get fresh air'",
            detail="On polluted days, outdoor air is not 'fresh' - it is the "
                   "main exposure source.",
            reason="The 'fresh air' intuition fails when ambient PM2.5 is high.",
            group="avoid", priority=2))
    if _idx_ge(cat_name, "Poor"):
        recs["avoid"].append(Recommendation(
            title="Avoid morning/evening walks near traffic corridors",
            detail=("Vehicle exhaust peaks near roads during commute hours; "
                    "choose indoor or park settings if you must go out."),
            reason="Proximity to traffic raises ultrafine particle and NO2 "
                   "exposure substantially.",
            group="avoid", priority=2))
        recs["avoid"].append(Recommendation(
            title="Do not rely on decorative plants as air purifiers",
            detail=("Houseplants have negligible effect on PM2.5. A few plants "
                    "will not measurably clean a room."),
            reason="Published studies show plant-based removal rates far below "
                   "what a person inhales in a room.",
            group="avoid", priority=3))
    if _idx_ge(cat_name, "Very Poor"):
        recs["avoid"].append(Recommendation(
            title="Avoid all non-essential outdoor trips",
            detail="Combine errands into one short trip if you must go out; "
                   "each extra trip adds exposure and emissions.",
            reason="Dose of pollution scales with time spent outdoors.",
            group="avoid", priority=1))

    # ---- D. Lower-emission alternatives ----------------------------------
    if profile.transport == "car":
        recs["alternatives"].append(Recommendation(
            title="Replace short car trips with transit, walking or cycling",
            detail=("Trips under ~3 km produce disproportionately high "
                    "emissions per km because engines run cold. Transit, "
                    "walking or cycling cut both pollution and fuel cost."),
            reason="Cold-start enrichment and stop-go traffic multiply "
                   "per-km emissions on short trips.",
            group="alternatives", priority=2))
    if profile.transport in ("car", "bike"):
        recs["alternatives"].append(Recommendation(
            title="Carpool or use shared mobility for commute days",
            detail="Sharing one vehicle halves per-person emissions and "
                   "fuel cost for the same trip.",
            reason="Per-passenger emissions fall roughly in proportion to "
                   "occupancy.",
            group="alternatives", priority=2))
    if profile.transport == "bus" or profile.priority == "environment":
        recs["alternatives"].append(Recommendation(
            title="Keep using shared transit - it is already the low-emission choice",
            detail="A bus or metro trip emits far less per passenger-km than "
                   "a solo car.",
            reason="High occupancy distributes emissions across many riders.",
            group="alternatives", priority=3))
    if profile.concerns and "cost" in profile.concerns:
        recs["alternatives"].append(Recommendation(
            title="Trip-chain errands to cut fuel and exposure",
            detail="Plan one loop covering all errands instead of several "
                   "separate trips.",
            reason="Fewer cold starts and fewer km directly reduce fuel use "
                   "and inhaled dose.",
            group="alternatives", priority=2))
    recs["alternatives"].append(Recommendation(
        title="Shift discretionary trips to off-peak or combine with work trips",
        detail="Every avoided kilometre avoids roughly 0.15-0.25 kg CO2 for "
               "a typical petrol car (estimate; see Impact Tracker).",
        reason="Transport is the largest controllable urban emission source "
               "for most households.",
        group="alternatives", priority=3))

    # ---- E. Indoor protection ------------------------------------------------
    if _idx_ge(cat_name, "Moderate"):
        recs["indoor"].append(Recommendation(
            title="Run an air purifier with a HEPA filter in the room you occupy most",
            detail=("A HEPA purifier reduces indoor PM2.5 substantially when "
                    "windows must stay closed. Size it to the room (CADR "
                    "matched to room volume)."),
            reason="HEPA media capture >99% of 0.3-micron particles; this is "
                   "the most effective single indoor intervention.",
            group="indoor", priority=1))
        recs["indoor"].append(Recommendation(
            title="Use kitchen exhaust fans while cooking",
            detail="Cooking - especially frying and biomass use - is a major "
                   "indoor PM2.5 source.",
            reason="Cooking emissions can rival or exceed ambient pollution "
                   "indoors during meal times.",
            group="indoor", priority=2))
    if _idx_ge(cat_name, "Poor"):
        recs["indoor"].append(Recommendation(
            title="Create a 'clean room' for sleep",
            detail=("Keep one bedroom sealed, with a purifier running, for "
                    "the most vulnerable family member."),
            reason="Sleep is the longest continuous exposure period; a clean "
                   "room caps overnight dose.",
            group="indoor", priority=1))
        recs["indoor"].append(Recommendation(
            title="Wet-mop and damp-dust instead of dry sweeping",
            detail="Dry sweeping resuspends settled particles; damp methods "
                   "capture them.",
            reason="Resuspended dust adds to the particle load you breathe.",
            group="indoor", priority=3))
    else:
        recs["indoor"].append(Recommendation(
            title="Ventilate smartly",
            detail=("On Good/Satisfactory days, open windows for 10-15 minutes "
                    "to flush indoor pollutants (cooking, cleaning products)."),
            reason="Ventilation clears accumulated indoor pollutants when "
                   "outdoor air is clean.",
            group="indoor", priority=2))

    # ---- F/G. Why & next steps ---------------------------------------------
    if _idx_ge(cat_name, "Poor"):
        recs["next_steps"].append(Recommendation(
            title="Check tomorrow's forecast before planning outdoor time",
            detail="Pollution episodes typically persist for days; plan indoor "
                   "alternatives in advance.",
            reason="PM2.5 episodes are meteorologically persistent.",
            group="next_steps", priority=2))
    recs["next_steps"].append(Recommendation(
        title="Track one sustainable action daily in the Impact Tracker",
        detail="Log avoided trips, transit use or energy savings to see your "
               "cumulative contribution.",
        reason="Measuring progress sustains behaviour change.",
        group="next_steps", priority=3))
    recs["next_steps"].append(Recommendation(
        title="Share the Indoor Air Guardian checklist with family",
        detail="Most indoor gains come from consistent small habits shared "
               "across the household.",
        reason="Household behaviour, not individual effort, sets indoor levels.",
        group="next_steps", priority=3))

    # Lifestyle-specific additions
    if profile.lifestyle == "runner" and not safe:
        recs["today"].insert(0, Recommendation(
            title="Swap today's run for an indoor session",
            detail="Running increases minute ventilation ~10x vs rest, "
                   "amplifying pollutant dose even on Moderate days.",
            reason="Dose = concentration x ventilation rate x duration.",
            group="today", priority=1))
    if profile.lifestyle == "parent" and _idx_ge(cat_name, "Moderate"):
        recs["today"].append(Recommendation(
            title="Limit children's outdoor playtime today",
            detail="Children breathe more air per kg body weight and their "
                   "lungs are still developing.",
            reason="Children's higher ventilation-to-body-weight ratio raises "
                   "their effective dose.",
            group="today", priority=1))
    if profile.household in ("children", "elderly", "family") and _idx_ge(cat_name, "Poor"):
        recs["indoor"].append(Recommendation(
            title="Ask sensitive family members to keep rescue medication accessible",
            detail="On Very Poor days, keep inhalers/medication handy even "
                   "indoors, as indoor levels can remain elevated.",
            reason="PM2.5 penetrates buildings; sensitive individuals may "
                   "still react indoors.",
            group="indoor", priority=2))

    return recs


def recommendation_counts(recs: dict[str, list[Recommendation]]) -> dict[str, int]:
    return {k: len(v) for k, v in recs.items()}
