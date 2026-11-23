"""Tests for the optional Gemini integration and personal report."""

import json
import urllib.error

import pytest

from airaware import ai, report
from airaware.data import SAMPLE_MEASUREMENTS, MeasurementSet
from airaware.recommendations import UserProfile, generate_recommendations


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._payload


@pytest.fixture
def fake_key(monkeypatch):
    monkeypatch.setattr(ai, "_secrets_get",
                        lambda key, default=None: "fake-key"
                        if key == "GEMINI_API_KEY" else default)


class TestGeminiOptional:
    def test_not_configured_without_secrets(self):
        # Outside a Streamlit runtime st.secrets is unavailable -> False
        assert ai.gemini_configured() is False

    def test_generate_returns_none_without_key(self):
        assert ai.generate_text("hello") is None

    def test_model_default(self):
        assert ai.gemini_model()

    def test_prompt_builder(self):
        p = ai.build_assistant_prompt("AQI 250 (Poor)", "office worker",
                                      ["Close windows", "Use transit"])
        assert "AQI 250" in p and "Close windows" in p


class TestGeminiFailureHandling:
    """Every failure mode must degrade to None, never raise or fabricate."""

    def test_network_error_returns_none(self, fake_key, monkeypatch):
        def boom(req, timeout=None):
            raise urllib.error.URLError("no route to host")
        monkeypatch.setattr(ai.urllib.request, "urlopen", boom)
        assert ai.generate_text("hi") is None

    def test_http_error_returns_none(self, fake_key, monkeypatch):
        def boom(req, timeout=None):
            raise urllib.error.HTTPError("u", 429, "quota", {}, None)
        monkeypatch.setattr(ai.urllib.request, "urlopen", boom)
        assert ai.generate_text("hi") is None

    def test_malformed_json_returns_none(self, fake_key, monkeypatch):
        monkeypatch.setattr(
            ai.urllib.request, "urlopen",
            lambda req, timeout=None: _FakeResponse(b"not json{{{"))
        assert ai.generate_text("hi") is None

    def test_non_utf8_response_returns_none(self, fake_key, monkeypatch):
        monkeypatch.setattr(
            ai.urllib.request, "urlopen",
            lambda req, timeout=None: _FakeResponse(b"\xff\xfe\x00bad"))
        assert ai.generate_text("hi") is None

    def test_empty_candidates_returns_none(self, fake_key, monkeypatch):
        payload = json.dumps({"candidates": []}).encode()
        monkeypatch.setattr(
            ai.urllib.request, "urlopen",
            lambda req, timeout=None: _FakeResponse(payload))
        assert ai.generate_text("hi") is None

    def test_valid_response_returns_text(self, fake_key, monkeypatch):
        payload = json.dumps({
            "candidates": [{"content": {"parts": [{"text": "Stay indoors."}]}}]
        }).encode()
        monkeypatch.setattr(
            ai.urllib.request, "urlopen",
            lambda req, timeout=None: _FakeResponse(payload))
        assert ai.generate_text("hi") == "Stay indoors."


class TestReport:
    def _meas(self):
        return MeasurementSet(location="Pune", pollutants={"pm25": 150},
                              source="user").finalize()

    def test_empty_report(self):
        md = report.build_report(None, None)
        assert "No air-quality measurement" in md

    def test_full_report(self):
        m = self._meas()
        profile = UserProfile(city="Pune", lifestyle="office",
                              transport="car", household="alone")
        recs = generate_recommendations(m, profile)
        md = report.build_report(m, profile, recs,
                                 plan_guidance={"morning": "Keep windows shut"})
        assert "AirAware AI" in md
        assert "PM2.5" in md
        assert "Your profile" in md
        assert "Recommendations" in md
        assert "Keep windows shut" in md
        assert "rule engine" in md.lower()

    def test_sample_marked_in_report(self):
        m = SAMPLE_MEASUREMENTS[0]
        md = report.build_report(m, None)
        assert "SAMPLE DEMONSTRATION DATA" in md

    def test_report_has_provenance(self):
        m = self._meas()
        md = report.build_report(m, None)
        assert "user-provided" in md.lower() or "User-provided" in md
