"""Tests for the day-ahead planning outlook (airaware.forecast).

The outlook is a labelled planning estimate: AQI *categories* per time
window, never fabricated hourly readings. These tests pin down the
modelling rules, honesty labelling and edge cases.
"""

from datetime import datetime, timedelta, timezone

import pytest

from airaware import forecast
from airaware.aqi import is_outdoor_safe
from airaware.data import MeasurementSet, record_measurement_history

NOW = datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc)


def _meas(aqi_pollutants=None, aqi=None, hours_ago=1.0,
          source="user", ts=None):
    ts = ts or (NOW - timedelta(hours=hours_ago))
    m = MeasurementSet(location="Test City", pollutants=aqi_pollutants or {},
                       aqi=aqi, timestamp=ts, source=source)
    return m.finalize()


def _idx(name: str) -> int:
    return forecast.CAT_ORDER.index(name)


class TestWindowStructure:
    def test_seven_windows_cover_day(self):
        m = _meas({"pm25": 60})
        o = forecast.build_outlook(m, now=NOW)
        assert len(o.windows) == 7
        labels = [w.label for w in o.windows]
        assert labels[0].startswith("Night")
        assert labels[-1].startswith("Late night")

    def test_window_hours_in_range(self):
        o = forecast.build_outlook(_meas({"pm25": 60}), now=NOW)
        for w in o.windows:
            assert 0 <= w.start_hour < 24
            assert 0 <= w.end_hour < 24

    def test_best_and_worst_exist(self):
        o = forecast.build_outlook(_meas({"pm25": 200}), now=NOW)
        assert o.best_window is not None
        assert o.worst_window is not None
        assert o.best_window.cat_mid_idx <= o.worst_window.cat_mid_idx


class TestDiurnalModel:
    def test_pm_dominant_evening_worse_than_midday(self):
        # PM2.5 200 ug/m3 -> Poor; evening rush should estimate worse
        # than the midday mixing window.
        m = _meas({"pm25": 200})
        o = forecast.build_outlook(m, now=NOW)
        by_key = {w.key: w for w in o.windows}
        assert (by_key["evening"].cat_mid_idx
                > by_key["midday"].cat_mid_idx)
        assert (by_key["early_morning"].cat_mid_idx
                > by_key["midday"].cat_mid_idx)

    def test_o3_dominant_afternoon_is_risk_window(self):
        m = _meas({"o3": 200})
        o = forecast.build_outlook(m, now=NOW)
        by_key = {w.key: w for w in o.windows}
        assert by_key["afternoon"].cat_mid_idx == max(
            w.cat_mid_idx for w in o.windows)
        assert any("afternoon" in n for n in o.notes)

    def test_good_air_stays_goodish_all_day(self):
        m = _meas({"pm25": 20})
        o = forecast.build_outlook(m, now=NOW)
        assert all(w.cat_high in ("Good", "Satisfactory")
                   for w in o.windows)

    def test_severe_reading_never_shows_good_window(self):
        m = _meas({"pm25": 400})
        o = forecast.build_outlook(m, now=NOW)
        assert all(_idx(w.cat_high) >= _idx("Poor") for w in o.windows)


class TestActivityAndVentilation:
    def test_activity_verdicts_match_is_outdoor_safe(self):
        o = forecast.build_outlook(_meas({"pm25": 200}), now=NOW)
        for w in o.windows:
            for act, verdict in w.activity.items():
                safe_hi, _ = is_outdoor_safe(w.cat_high, act)
                safe_lo, _ = is_outdoor_safe(w.cat_low, act)
                if safe_hi:
                    assert verdict == "good"
                elif safe_lo:
                    assert verdict == "caution"
                else:
                    assert verdict == "avoid"

    def test_poor_day_morning_ventilation_closed(self):
        m = _meas({"pm25": 250, "pm10": 300})
        o = forecast.build_outlook(m, now=NOW)
        by_key = {w.key: w for w in o.windows}
        assert by_key["evening"].ventilation == "closed"

    def test_clean_day_ventilation_open(self):
        m = _meas({"pm25": 15})
        o = forecast.build_outlook(m, now=NOW)
        assert all(w.ventilation == "open" for w in o.windows)


class TestHonestyAndConfidence:
    def test_basis_and_limitations_always_present(self):
        o = forecast.build_outlook(_meas({"pm25": 100}), now=NOW)
        assert "diurnal model" in o.basis
        assert len(o.limitations) >= 3
        assert any("NOT an official" in l or "not an official" in l
                   for l in o.limitations)

    def test_sample_data_low_confidence(self):
        m = _meas({"pm25": 100}, source="sample")
        o = forecast.build_outlook(m, now=NOW)
        assert o.confidence == "low"

    def test_stale_reading_low_confidence(self):
        m = _meas({"pm25": 100}, hours_ago=30)
        o = forecast.build_outlook(m, now=NOW)
        assert o.confidence == "low"
        assert o.measurement_age_hours == pytest.approx(30)

    def test_fresh_complete_reading_high_confidence(self):
        m = _meas({"pm25": 60, "pm10": 90, "no2": 40, "so2": 10,
                   "co": 0.5, "o3": 60, "nh3": 150}, hours_ago=1)
        o = forecast.build_outlook(m, now=NOW)
        assert o.confidence == "high"

    def test_partial_data_drops_confidence(self):
        m = _meas({"pm25": 60}, hours_ago=1)
        o = forecast.build_outlook(m, now=NOW)
        assert o.confidence == "moderate"

    def test_no_fabricated_numbers(self):
        # Windows expose categories and verdicts only - no AQI floats
        # that could be mistaken for measured readings.
        o = forecast.build_outlook(_meas({"pm25": 200}), now=NOW)
        for w in o.windows:
            assert w.cat_low in forecast.CAT_ORDER
            assert w.cat_high in forecast.CAT_ORDER
            assert not hasattr(w, "aqi")


class TestSessionTrend:
    def _history(self, aqi_values, hours):
        return [_meas({"pm25": v}, hours_ago=h)
                for v, h in zip(aqi_values, hours)]

    def test_rising_trend_shifts_windows_up(self):
        m = _meas({"pm25": 150}, hours_ago=1)
        hist = [m] + self._history([100, 120, 140], [5, 3, 1])
        with_trend = forecast.build_outlook(m, history=hist, now=NOW)
        without = forecast.build_outlook(m, history=[], now=NOW)
        assert "session trend" in with_trend.basis
        assert with_trend.trend_aqi_per_hour is not None
        assert with_trend.trend_aqi_per_hour > 0
        assert (with_trend.windows[3].cat_mid_idx
                > without.windows[3].cat_mid_idx)

    def test_falling_trend_shifts_windows_down(self):
        m = _meas({"pm25": 150}, hours_ago=1)
        hist = [m] + self._history([300, 250, 200], [5, 3, 1])
        o = forecast.build_outlook(m, history=hist, now=NOW)
        without = forecast.build_outlook(m, history=[], now=NOW)
        assert (o.windows[3].cat_mid_idx
                < without.windows[3].cat_mid_idx)

    def test_too_few_points_ignored(self):
        m = _meas({"pm25": 150}, hours_ago=1)
        hist = [m, _meas({"pm25": 100}, hours_ago=3)]
        o = forecast.build_outlook(m, history=hist, now=NOW)
        assert "session trend" not in o.basis
        assert o.trend_aqi_per_hour is None

    def test_short_span_ignored(self):
        m = _meas({"pm25": 150}, hours_ago=0.2)
        hist = [m,
                _meas({"pm25": 100}, hours_ago=0.5),
                _meas({"pm25": 200}, hours_ago=0.8)]
        o = forecast.build_outlook(m, history=hist, now=NOW)
        # span < TREND_MIN_SPAN_H -> no trend
        assert o.trend_aqi_per_hour is None

    def test_slope_helper_edge_cases(self):
        assert forecast._aqi_slope([])[0] == 0.0
        slope, n, span = forecast._aqi_slope(
            self._history([100, 200, 300], [5, 3, 1]))
        assert slope > 0 and n == 3 and span == pytest.approx(4.0)


class TestMeasurementHistory:
    def test_appends_and_dedupes(self):
        m1 = _meas({"pm25": 50}, hours_ago=2)
        m2 = _meas({"pm25": 80}, hours_ago=1)
        hist = record_measurement_history([], m1)
        hist = record_measurement_history(hist, m2)
        hist = record_measurement_history(hist, m1)
        assert len(hist) == 2
        assert hist[0] is m1 and hist[1] is m2

    def test_history_capped(self):
        hist = []
        for i in range(10):
            hist = record_measurement_history(
                hist, _meas({"pm25": 50 + i}, hours_ago=0.1 + i * 0.01),
                cap=5)
        assert len(hist) == 5
        assert hist[-1].pollutants["pm25"] == 59

    def test_input_list_not_mutated(self):
        m = _meas({"pm25": 50})
        hist = [m]
        out = record_measurement_history(hist, _meas({"pm25": 60}))
        assert len(hist) == 1 and len(out) == 2
