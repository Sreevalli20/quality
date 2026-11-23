from airaware.data import MeasurementSet
from airaware.planner import build_daily_plan


def _mse(pollutants):
    return MeasurementSet(location="T", pollutants=pollutants,
                          source="user").finalize()


def test_plan_has_six_slots():
    plan = build_daily_plan(_mse({"pm25": 20}))
    assert len(plan) == 6
    keys = [p.slot_key for p in plan]
    assert keys == ["morning", "commute_am", "midday", "commute_pm",
                    "evening", "night"]


def test_poor_air_indoor_midday():
    plan = build_daily_plan(_mse({"pm25": 250}))
    midday = next(p for p in plan if p.slot_key == "midday")
    assert "indoor" in midday.guidance.lower()
    assert midday.indoor_friendly is False or "indoors" in midday.guidance.lower()


def test_good_air_outdoor_ok():
    plan = build_daily_plan(_mse({"pm25": 15}))
    midday = next(p for p in plan if p.slot_key == "midday")
    assert "fine" in midday.guidance.lower() or "best window" in midday.guidance.lower()


def test_children_evening_advice():
    plan = build_daily_plan(_mse({"pm25": 250}), has_children=True)
    evening = next(p for p in plan if p.slot_key == "evening")
    assert "children" in evening.guidance.lower()
