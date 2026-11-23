"""Tests for the optional Gemini integration and personal report."""

from airaware import ai, report
from airaware.data import MeasurementSet, SAMPLE_MEASUREMENTS
from airaware.recommendations import UserProfile, generate_recommendations


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
