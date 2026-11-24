"""Tests for user-timezone handling (airaware.tzutil).

The planning outlook and the plan's "now" marker must reflect the user's
clock, not the server's (Streamlit Cloud runs UTC).
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from airaware import forecast, tzutil
from airaware.data import MeasurementSet
from airaware.planner import current_time_slot


class TestTzUtil:
    def test_default_is_ist(self):
        # No Streamlit runtime in unit tests -> documented default.
        assert tzutil.user_timezone_name() == "Asia/Kolkata"

    def test_unknown_name_falls_back(self, monkeypatch):
        monkeypatch.setattr(tzutil, "_session_get",
                            lambda k, d=None: "Not/AZone")
        assert tzutil.user_timezone_name() == "Asia/Kolkata"

    def test_local_now_is_aware(self):
        now = tzutil.local_now()
        assert now.tzinfo is not None

    def test_tz_label_mentions_utc_offset(self):
        assert "UTC" in tzutil.tz_label()


class TestOutlookTimezone:
    def _meas(self):
        m = MeasurementSet(location="Pune", pollutants={"pm25": 150},
                           timestamp=datetime(2026, 11, 24, 6, 0,
                                              tzinfo=timezone.utc),
                           source="user")
        return m.finalize()

    def _hist(self, now):
        # Three readings over >3h with a clear rising trend.
        out = []
        for i, aqi in enumerate((100.0, 130.0, 160.0)):
            h = now - timedelta(hours=6 - 2 * i)
            out.append(MeasurementSet(
                location="Pune", pollutants={"pm25": aqi}, timestamp=h,
                source="user").finalize())
        return out

    def test_explicit_utc_changes_window_math(self):
        # With a rising session trend, "hours from now to each window
        # centre" depends on the timezone the windows are expressed in:
        # 12:00 UTC is 17:30 IST, so the projection differs.
        now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
        m = self._meas()
        hist = self._hist(now)
        utc = forecast.build_outlook(m, history=hist, now=now,
                                     tz=ZoneInfo("UTC"))
        ist = forecast.build_outlook(m, history=hist, now=now,
                                     tz=ZoneInfo("Asia/Kolkata"))
        assert [w.cat_mid_idx for w in utc.windows] != \
            [w.cat_mid_idx for w in ist.windows]

    def test_default_tz_does_not_crash(self):
        m = self._meas()
        o = forecast.build_outlook(m)
        assert o.windows


class TestPlannerTimezone:
    def test_current_time_slot_explicit_hour_unchanged(self):
        assert current_time_slot(7) == "morning"
        assert current_time_slot(23) == "night"
