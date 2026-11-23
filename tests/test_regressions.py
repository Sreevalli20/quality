"""Regression tests for bugs found in the engineering review."""


import pytest

from airaware.aqi import category_for
from airaware.data import MeasurementSet, parse_measurements_csv


class TestCategoryBoundaryGaps:
    """CPCB category bounds are integers; interpolated or user-supplied AQI
    can be fractional. Gap values must not fall through to 'Severe+'."""

    @pytest.mark.parametrize("aqi,expected", [
        (50.4, "Satisfactory"), (50.5, "Satisfactory"), (50.9, "Satisfactory"),
        (100.5, "Moderate"), (200.5, "Poor"), (300.5, "Very Poor"),
        (400.5, "Severe"),
    ])
    def test_fractional_aqi_maps_to_lower_category(self, aqi, expected):
        assert category_for(aqi)["name"] == expected

    def test_non_finite_aqi(self):
        assert category_for(float("nan"))["name"] == "Good"
        assert category_for(float("inf"))["name"] == "Good"
        assert category_for(None)["name"] == "Good"

    def test_user_supplied_fractional_aqi(self):
        m = MeasurementSet(location="X", aqi=50.5, source="user").finalize()
        assert m.display_aqi == 50.5
        assert m.category_name == "Satisfactory"

    def test_negative_aqi_rejected(self):
        m = MeasurementSet(location="X", aqi=-10, source="user").finalize()
        assert m.display_aqi is None


class TestCsvAqiValidation:
    def test_out_of_range_aqi_warned_and_skipped(self):
        csv = b"location,aqi\nGood,250\nBad,99999\n"
        ms, warns = parse_measurements_csv(csv)
        assert len(ms) == 1
        assert ms[0].display_aqi == 250
        assert any("aqi" in w.lower() for w in warns)

    def test_only_invalid_rows_raise(self):
        csv = b"location,aqi\nBad,-5\nWorse,abc\n"
        with pytest.raises(ValueError, match="No usable"):
            parse_measurements_csv(csv)

    def test_negative_aqi_row_dropped(self):
        csv = b"location,aqi\nX,-20\n"
        with pytest.raises(ValueError, match="No usable"):
            parse_measurements_csv(csv)

    def test_fractional_aqi_category(self):
        csv = b"location,aqi\nX,50.5\n"
        ms, _ = parse_measurements_csv(csv)
        assert ms[0].category_name == "Satisfactory"


class TestSubIndexBoundaries:
    @pytest.mark.parametrize("pollutant,conc,expected", [
        ("pm25", 30, 50), ("pm25", 60, 100), ("pm25", 90, 200),
        ("pm10", 50, 50), ("pm10", 100, 100), ("pm10", 250, 200),
        ("no2", 40, 50), ("so2", 40, 50), ("co", 1.0, 50),
        ("o3", 50, 50), ("nh3", 200, 50),
    ])
    def test_upper_bound_of_each_first_band(self, pollutant, conc, expected):
        from airaware.aqi import pollutant_sub_index
        assert pollutant_sub_index(pollutant, conc) == pytest.approx(expected)

    def test_zero_concentration(self):
        from airaware.aqi import pollutant_sub_index
        for p in ("pm25", "pm10", "no2", "so2", "co", "o3", "nh3"):
            assert pollutant_sub_index(p, 0) == 0
