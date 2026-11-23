"""Streamlit AppTest smoke tests across all nine pages and key journeys."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from airaware.data import SAMPLE_MEASUREMENTS, MeasurementSet
from airaware.impact import ImpactAction
from airaware.recommendations import UserProfile

APP = str(Path(__file__).resolve().parent.parent / "app.py")

ALL_PAGES = [
    "Home", "Air Quality Explorer", "Personal AI Assistant",
    "My Daily Air Plan", "Indoor Air Guardian", "Green Lifestyle Planner",
    "Environmental Impact", "Family & Community", "About & Data Sources",
]


def _app(**session_state) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, f"initial run failed: {at.exception}"
    for k, v in session_state.items():
        at.session_state[k] = v
    return at


def _goto(at: AppTest, page: str):
    at.session_state["nav_page"] = page
    at.run()
    assert not at.exception, f"{page} raised: {at.exception}"


class TestAllPagesRender:
    """Every page renders without exceptions in the EMPTY state."""

    @pytest.mark.parametrize("page", ALL_PAGES)
    def test_page_empty_state(self, page):
        at = _app()
        _goto(at, page)

    @pytest.mark.parametrize("page", ALL_PAGES[1:], ids=ALL_PAGES[1:])
    def test_page_with_measurement(self, page):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0])
        _goto(at, page)


class TestHomeJourneys:
    def test_entry_choice_buttons_exist(self):
        at = _app()
        keys = {b.key for b in at.button}
        assert {"entry_manual", "entry_csv", "entry_sample"} <= keys

    def test_manual_entry_journey(self):
        at = _app()
        at.button(key="entry_manual").click().run()
        assert not at.exception
        at.number_input(key="homep_pm25").set_value(150.0)
        at.number_input(key="homep_pm10").set_value(280.0)
        at.button(key="homeapply").click().run()
        assert not at.exception
        m = at.session_state["measurement"]
        assert m is not None and m.display_aqi is not None
        assert at.session_state["nav_page"] == "Air Quality Explorer"

    def test_manual_entry_requires_input(self):
        at = _app()
        at.button(key="entry_manual").click().run()
        at.button(key="homeapply").click().run()
        assert not at.exception
        assert at.session_state.get("measurement") is None
        assert any("at least one" in e.value.lower()
                   for e in at.error)

    def test_sample_journey_labels_provenance(self):
        at = _app()
        at.button(key="entry_sample").click().run()
        at.button(key="home_sample_use").click().run()
        assert not at.exception
        m = at.session_state["measurement"]
        assert m is not None and m.is_sample
        assert at.session_state["nav_page"] == "Air Quality Explorer"

    def test_sidebar_nav_all_pages(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[1])
        for page in ALL_PAGES:
            _goto(at, page)


class TestAssistantJourney:
    def test_profile_and_recommendations(self):
        profile = UserProfile(city="Pune", lifestyle="office",
                              transport="car", household="children",
                              outdoor_pref="moderate", concerns=["health"],
                              budget="low", priority="health")
        at = _app(measurement=SAMPLE_MEASUREMENTS[0], profile=profile)
        _goto(at, "Personal AI Assistant")
        text = "\n".join(m.value for m in at.markdown)
        assert "Priority" in text or "Suggested" in text
        assert any(b.key == "report_dl" for b in at.download_button)

    def test_no_gemini_without_key(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0],
                  profile=UserProfile())
        _goto(at, "Personal AI Assistant")
        assert any("GEMINI_API_KEY" in c.value
                   for c in at.caption)


class TestImpactJourney:
    def test_logged_actions_render(self):
        acts = [ImpactAction(
            action_type="trip", description="Metro instead of petrol car",
            vehicle="metro", avoided_vehicle="car_petrol", distance_km=10.0,
            cost_saved_inr=95.0, date="2026-11-23")]
        at = _app(impact_actions=acts)
        _goto(at, "Environmental Impact")
        text = "\n".join(m.value for m in at.markdown)
        assert "CO₂e vs air pollution" in text


class TestPlannerAndCommunity:
    def test_plan_textareas_render(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[2])
        _goto(at, "My Daily Air Plan")
        assert len(at.text_area) >= 6

    def test_checklist_interaction(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0])
        _goto(at, "Family & Community")
        boxes = at.checkbox
        assert len(boxes) >= 9
        boxes[0].check().run()
        assert not at.exception
        assert at.session_state["community_checklist"].get(0) is True
