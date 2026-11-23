import math

import pytest

from airaware.aqi import (calculate_aqi, category_for, is_outdoor_safe,
                          pollutant_sub_index)


class TestSubIndex:
    def test_pm25_good_boundary(self):
        assert pollutant_sub_index("pm25", 30) == 50

    def test_pm25_moderate_midpoint(self):
        # 75 ug/m3 sits in the 61-90 -> 101-200 band
        idx = pollutant_sub_index("pm25", 75)
        assert 101 < idx < 200

    def test_pm10_zero(self):
        assert pollutant_sub_index("pm10", 0) == 0

    def test_invalid_values(self):
        assert pollutant_sub_index("pm25", -5) is None
        assert pollutant_sub_index("pm25", float("nan")) is None
        assert pollutant_sub_index("pm25", float("inf")) is None
        assert pollutant_sub_index("unknown", 10) is None
        assert pollutant_sub_index("pm25", None) is None

    def test_above_worst_breakpoint_extrapolates(self):
        idx = pollutant_sub_index("pm25", 600)
        assert idx is not None and idx > 500


class TestCategories:
    @pytest.mark.parametrize("aqi,expected", [
        (0, "Good"), (50, "Good"), (51, "Satisfactory"), (100, "Satisfactory"),
        (101, "Moderate"), (200, "Moderate"), (201, "Poor"), (300, "Poor"),
        (301, "Very Poor"), (400, "Very Poor"), (401, "Severe"), (500, "Severe"),
        (501, "Severe+"), (999, "Severe+"),
    ])
    def test_category_boundaries(self, aqi, expected):
        assert category_for(aqi)["name"] == expected


class TestCalculateAqi:
    def test_empty(self):
        r = calculate_aqi({})
        assert r.aqi is None and r.category is None
        assert r.pollutant_results == []

    def test_none_values_ignored(self):
        r = calculate_aqi({"pm25": None, "pm10": None})
        assert r.aqi is None

    def test_single_pollutant(self):
        r = calculate_aqi({"pm25": 60})  # top of Satisfactory band
        assert r.aqi == 100
        assert r.dominant_pollutant == "pm25"
        assert r.is_partial

    def test_max_wins(self):
        # pm25=60 -> 100 ; pm10=520 -> extrapolates above AQI 500
        r = calculate_aqi({"pm25": 60, "pm10": 520})
        assert r.dominant_pollutant == "pm10"
        assert r.aqi > 500

    def test_invalid_entries_rejected_with_note(self):
        r = calculate_aqi({"pm25": -10, "pm10": 100})
        assert r.aqi is not None
        assert any("pm25" in n.lower() or "PM2.5" in n for n in r.notes)

    def test_partial_flag_when_not_all_pollutants(self):
        r = calculate_aqi({"pm25": 40, "pm10": 80, "no2": 50})
        assert r.is_partial


class TestOutdoorSafety:
    def test_good_allows_heavy(self):
        safe, _ = is_outdoor_safe("Good", "heavy")
        assert safe

    def test_severe_blocks_heavy(self):
        safe, msg = is_outdoor_safe("Severe", "heavy")
        assert not safe and "Severe" in msg

    def test_light_allowed_on_poor(self):
        safe, _ = is_outdoor_safe("Poor", "light")
        assert safe

    def test_unknown_category(self):
        safe, _ = is_outdoor_safe("Bogus", "light")
        assert not safe
