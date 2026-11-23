"""Green Lifestyle Planner - practical sustainable-living options.

Each option states conditions, benefits and limitations honestly, and a
personalisation layer ranks options against the user's transport,
budget and priorities. No assumption that walking/cycling/transit is
available to everyone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .recommendations import UserProfile


@dataclass
class LifestyleOption:
    area: str            # Transport | Energy | Waste | Household
    title: str
    detail: str
    benefit: str
    limitation: str
    conditions: list[str] = field(default_factory=list)  # when it applies
    score_boost: dict[str, int] = field(default_factory=dict)  # profile->points


def all_options() -> list[LifestyleOption]:
    return [
        # ---- Transport ----
        LifestyleOption(
            area="Transport", title="Public transit for commute",
            detail="Bus, metro or suburban rail for regular work/study trips.",
            benefit="Lowest per-passenger emissions; frees you from driving stress; often cheaper than fuel+parking.",
            limitation="Fixed schedules and routes may not match your needs; crowded during peaks.",
            conditions=["Route covers your trip", "Schedule fits your timings"],
            score_boost={"environment": 3, "cost": 2, "transport_bus": 3, "transport_metro": 3}),
        LifestyleOption(
            area="Transport", title="Carpool / ride-share",
            detail="Share one vehicle with colleagues or neighbours for regular trips.",
            benefit="Cuts per-person fuel and emissions roughly in half; splits tolls/parking.",
            limitation="Requires compatible schedules and trust; detours add time.",
            conditions=["A compatible co-traveller exists", "You already drive"],
            score_boost={"environment": 3, "cost": 2, "transport_car": 3}),
        LifestyleOption(
            area="Transport", title="Walking for short trips",
            detail="Replace trips under ~1.5 km with walking.",
            benefit="Zero emissions, zero fuel cost, adds daily physical activity.",
            limitation="Weather, safety and distance constrain it; not for everyone.",
            conditions=["Distance under ~1.5 km", "Safe walking route exists"],
            score_boost={"environment": 3, "health": 2, "cost": 2}),
        LifestyleOption(
            area="Transport", title="Cycling for commute or errands",
            detail="Cycle for trips of 2-10 km where terrain and safety allow.",
            benefit="Near-zero emissions, cheap per km, reliable travel time in traffic.",
            limitation="Needs safe roads, reasonable fitness and weather gear; monsoon and summer heat are real constraints in India.",
            conditions=["Safe cycle route or low-traffic roads", "Physical ability"],
            score_boost={"environment": 3, "cost": 2, "health": 2}),
        LifestyleOption(
            area="Transport", title="Combine errands into one trip",
            detail="Plan a single loop for shopping, pickups and services instead of multiple trips.",
            benefit="Cuts km, cold-starts and exposure time; saves fuel.",
            limitation="Requires a bit of planning; less flexible for urgent trips.",
            conditions=["Trips are not time-critical"],
            score_boost={"environment": 2, "cost": 2}),
        LifestyleOption(
            area="Transport", title="Avoid engine idling",
            detail="Switch off the engine at signals and during long pickups.",
            benefit="Idling wastes fuel and emits exhaust directly where you sit.",
            limitation="None significant; brief restarts use negligible extra fuel in modern vehicles.",
            conditions=["You drive a petrol/diesel vehicle"],
            score_boost={"environment": 1, "cost": 2, "transport_car": 2, "transport_bike": 2}),
        # ---- Energy ----
        LifestyleOption(
            area="Energy", title="LED lighting everywhere",
            detail="Replace remaining incandescent/halogen bulbs with LEDs.",
            benefit="LEDs use ~75-80% less electricity for the same light; payback in months.",
            limitation="Small upfront cost; choose warm-white for living spaces.",
            conditions=["Any household"],
            score_boost={"cost": 3, "environment": 1}),
        LifestyleOption(
            area="Energy", title="AC discipline: 24-26°C, fan assist, clean filters",
            detail="Set AC at 24-26°C, use ceiling fans to spread cool air, clean filters monthly.",
            benefit="Each degree lower raises consumption noticeably; clean filters cut load ~10-15%.",
            limitation="Comfort trade-off in peak summer; fans alone may not suffice for everyone.",
            conditions=["You use AC"],
            score_boost={"cost": 3, "environment": 2}),
        LifestyleOption(
            area="Energy", title="Unplug standby devices and use power strips",
            detail="TVs, chargers, routers and appliances draw standby power; use a switched strip.",
            benefit="Standby load adds up to ~5-10% of household electricity.",
            limitation="Minor inconvenience; some devices need constant power (routers, DVRs).",
            conditions=["Any household"],
            score_boost={"cost": 2, "environment": 1}),
        LifestyleOption(
            area="Energy", title="Shift laundry and EV charging to off-peak",
            detail="Run washing machines/dishwashers late evening where the tariff rewards it.",
            benefit="Reduces grid strain; lowers bill under time-of-day tariffs.",
            limitation="Only helps if your DISCOM offers time-of-day pricing.",
            conditions=["Time-of-day tariff plan"],
            score_boost={"cost": 2}),
        # ---- Waste ----
        LifestyleOption(
            area="Waste", title="Segregate wet and dry waste at source",
            detail="Keep a separate bin for kitchen waste; dry waste goes to recycling.",
            benefit="Reduces landfill load; wet waste can be composted at home.",
            limitation="Needs municipal collection support to realise full benefit.",
            conditions=["Any household"],
            score_boost={"environment": 3}),
        LifestyleOption(
            area="Waste", title="Home composting of kitchen scraps",
            detail="A small aerobic bin or terracotta compost pot converts scraps to manure.",
            benefit="Cuts waste to landfill and gives free fertiliser for plants.",
            limitation="Odour and pests if unmanaged; needs 15-20 min/week attention.",
            conditions=["You cook at home", "Outdoor/balcony space"],
            score_boost={"environment": 3, "cost": 1}),
        LifestyleOption(
            area="Waste", title="Carry a reusable bag and bottle",
            detail="Refuse single-use bags and bottled water where feasible.",
            benefit="Cuts plastic waste and the emissions from producing/disposal.",
            limitation="Needs habit change; tap-water safety varies by locality.",
            conditions=["Any household"],
            score_boost={"environment": 2}),
        # ---- Household ----
        LifestyleOption(
            area="Household", title="Curtails/reflective film on sun-facing windows",
            detail="Block direct afternoon sun to reduce AC load.",
            benefit="Lowers indoor temperature a few degrees, cutting AC runtime.",
            limitation="Reduces natural light; choose light-coloured films.",
            conditions=["West/south-facing rooms", "You use AC"],
            score_boost={"cost": 2, "environment": 1}),
        LifestyleOption(
            area="Household", title="Grow herbs/vegetables on a balcony",
            detail="Basil, mint, chillies, tomatoes in containers.",
            benefit="Small food-mile reduction and fresher produce; greenery improves wellbeing.",
            limitation="Yield is small; requires sunlight and regular watering.",
            conditions=["Balcony/terrace with 4+ hours sun"],
            score_boost={"environment": 2}),
    ]


def personalised_options(profile: UserProfile) -> list[tuple[int, LifestyleOption]]:
    """Score options against the profile; returns sorted (score, option)."""
    scored: list[tuple[int, LifestyleOption]] = []
    for opt in all_options():
        score = 0
        key_transport = f"transport_{profile.transport}"
        for cond in opt.score_boost:
            if cond == "health" and "health" in profile.concerns:
                score += opt.score_boost[cond]
            elif cond == "cost" and ("cost" in profile.concerns or profile.budget in ("free", "low")):
                score += opt.score_boost[cond]
            elif cond == profile.priority:
                score += opt.score_boost[cond]
            elif cond == key_transport:
                score += opt.score_boost[cond]
        scored.append((score, opt))
    scored.sort(key=lambda t: -t[0])
    return scored


def options_by_area() -> dict[str, list[LifestyleOption]]:
    out: dict[str, list[LifestyleOption]] = {}
    for opt in all_options():
        out.setdefault(opt.area, []).append(opt)
    return out
