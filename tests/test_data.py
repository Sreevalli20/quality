
import pytest

from airaware.data import (
    MeasurementSet,
    parse_measurements_csv,
    validate_aqi_value,
    validate_pollutant_value,
)


class TestValidation:
    def test_valid_pollutant(self):
        assert validate_pollutant_value("pm25", 55) is None

    def test_negative(self):
        assert validate_pollutant_value("pm25", -1) is not None

    def test_implausible(self):
        assert validate_pollutant_value("pm25", 99999) is not None

    def test_aqi_range(self):
        assert validate_aqi_value(250) is None
        assert validate_aqi_value(-5) is not None
        assert validate_aqi_value(5000) is not None


class TestMeasurementSet:
    def test_pollutants_take_priority(self):
        m = MeasurementSet(location="X", pollutants={"pm25": 60}, aqi=999,
                           source="user").finalize()
        assert m.display_aqi == 100  # computed, not the bogus 999

    def test_aqi_only_fallback(self):
        m = MeasurementSet(location="X", aqi=250, source="user").finalize()
        assert m.display_aqi == 250
        assert m.category_name == "Poor"

    def test_empty(self):
        m = MeasurementSet(location="X", source="user").finalize()
        assert m.display_aqi is None


class TestCsvImport:
    def _csv(self, text):
        return text.encode()

    def test_basic_pollutants(self):
        csv = self._csv("location,pm25,pm10\nDelhi,55,120\nMumbai,40,80")
        ms, _warns = parse_measurements_csv(csv)
        assert len(ms) == 2
        assert ms[0].source == "import"
        assert ms[0].display_aqi is not None

    def test_aliases(self):
        csv = self._csv("city,PM2.5,Carbon Monoxide\nPune,45,0.8")
        ms, _ = parse_measurements_csv(csv)
        assert len(ms) == 1
        assert "pm25" in ms[0].pollutants
        assert "co" in ms[0].pollutants

    def test_aqi_only_column(self):
        csv = self._csv("location,aqi\nDelhi,310")
        ms, _ = parse_measurements_csv(csv)
        assert ms[0].display_aqi == 310
        assert ms[0].category_name == "Very Poor"

    def test_no_recognised_columns(self):
        csv = self._csv("foo,bar\n1,2")
        with pytest.raises(ValueError, match="recognised pollutant"):
            parse_measurements_csv(csv)

    def test_empty_file(self):
        with pytest.raises(ValueError):
            parse_measurements_csv(b"")

    def test_bad_values_skipped_with_warning(self):
        csv = self._csv("location,pm25,pm10\nX,abc,100")
        ms, warns = parse_measurements_csv(csv)
        assert len(warns) >= 1
        # pm25 invalid -> only pm10 used
        assert ms[0].pollutants == {"pm10": 100.0}

    def test_garbage_csv(self):
        # Either unparseable or no recognised columns - both raise ValueError
        with pytest.raises(ValueError):
            parse_measurements_csv(b"\x00\x01\x02not,a,csv\x00")
