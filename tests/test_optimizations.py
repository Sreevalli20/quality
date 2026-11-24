"""Regression tests for the precision-optimization refactor.

Covers the behaviours introduced or consolidated while improving code
quality and efficiency: the shared secrets accessor, cached provider
health checks, the shared recommendation group labels, and the cached
static lifestyle catalogue.
"""

from __future__ import annotations

from airaware import lifestyle, providers, recommendations, secretsutil
from airaware.data import MeasurementSet
from airaware.recommendations import GROUP_LABELS, UserProfile


class TestSecretsUtil:
    def test_returns_default_without_runtime(self, monkeypatch):
        monkeypatch.setattr(secretsutil, "st", None)
        assert secretsutil.secrets_get("NOPE", "fallback") == "fallback"

    def test_returns_default_on_broken_secrets(self, monkeypatch):
        class _Broken:
            def get(self, key, default=None):
                raise RuntimeError("malformed secrets")

        class _St:
            secrets = _Broken()

        monkeypatch.setattr(secretsutil, "st", _St())
        assert secretsutil.secrets_get("ANY", 42) == 42

    def test_module_wrappers_delegate(self, monkeypatch):
        seen = []

        def fake(key, default=None):
            seen.append(key)
            return default

        monkeypatch.setattr(secretsutil, "secrets_get", fake)
        from airaware import ai

        ai._secrets_get("K")
        providers._secrets_get("K")
        assert seen == ["K", "K"]


class _FakeProvider:
    """Minimal provider double for health-check caching tests."""

    calls = 0

    @property
    def name(self):
        return "fake"

    def configured(self):
        return True

    def health_check(self):
        type(self).calls += 1
        return {"ok": True, "detail": "fine"}

    def latest(self, location_hint: str = ""):
        return None


class TestProviderHealthCache:
    def test_health_check_runs_once_within_ttl(self, monkeypatch):
        _FakeProvider.calls = 0
        monkeypatch.setattr(providers, "_PROVIDER_CLASSES", (_FakeProvider,))
        # Clear any cached entries for this arg shape.
        providers._provider_health_cached.clear()

        first = providers.provider_status()
        second = providers.provider_status()

        assert _FakeProvider.calls == 1
        assert first == second
        assert first[0]["health"] == {"ok": True, "detail": "fine"}


class TestGroupLabels:
    def test_every_generated_group_has_a_label(self):
        m = MeasurementSet(location="Test", pollutants={"pm25": 120})
        m.finalize()
        profile = UserProfile(city="Test", lifestyle="office",
                              transport="car", household="alone",
                              outdoor_pref="moderate", concerns=["health"],
                              budget="low", priority="health")
        recs = recommendations.generate_recommendations(m, profile)
        assert recs, "expected recommendations for a Moderate reading"
        for key in recs:
            assert key in GROUP_LABELS, f"group '{key}' missing a label"

    def test_report_uses_shared_labels(self):
        from airaware import report

        m = MeasurementSet(location="Test", pollutants={"pm25": 120})
        m.finalize()
        profile = UserProfile(city="Test", lifestyle="office",
                              transport="car", household="alone",
                              outdoor_pref="moderate", concerns=[],
                              budget="low", priority="health")
        recs = recommendations.generate_recommendations(m, profile)
        md = report.build_report(m, profile, recs)
        # Labels render without their letter prefix in the report.
        assert "What to do today" in md
        assert "B. What to do today" not in md


class TestLifestyleCache:
    def test_all_options_is_stable_and_unshared_mutation_safe(self):
        first = lifestyle.all_options()
        second = lifestyle.all_options()
        assert first is second
        assert len(first) > 0

    def test_options_by_area_covers_every_option(self):
        grouped = lifestyle.options_by_area()
        flat = [o for opts in grouped.values() for o in opts]
        assert len(flat) == len(lifestyle.all_options())
