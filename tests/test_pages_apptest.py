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


class TestSecurityAndLiveFetch:
    def test_malicious_location_is_escaped(self):
        evil = MeasurementSet(
            location='<img src=x onerror="alert(1)">',
            pollutants={"pm25": 120}, source="user").finalize()
        at = _app(measurement=evil)
        at.run()
        html_out = "\n".join(m.value for m in at.markdown)
        assert "<img src=x" not in html_out
        assert "&lt;img" in html_out

    def test_live_entry_hidden_without_provider(self):
        at = _app()
        keys = {b.key for b in at.button}
        assert "entry_live" not in keys

    def test_live_fetch_journey(self, monkeypatch):
        from airaware import providers
        fake = MeasurementSet(
            location="OpenAQ Station 7", pollutants={"pm25": 90, "pm10": 140},
            timestamp=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc),
            source="external", notes="Live data from OpenAQ station 'S7'")
        fake.finalize()
        monkeypatch.setattr(providers, "available_providers",
                            lambda: [providers.OpenAQProvider()])
        monkeypatch.setattr(providers.OpenAQProvider, "configured",
                            lambda self: True)
        monkeypatch.setattr(providers, "fetch_latest",
                            lambda hint="": fake)
        at = _app()
        at.session_state["home_entry"] = "live"
        at.run()
        assert not at.exception
        at.button(key="home_live_go").click().run()
        assert not at.exception
        m = at.session_state["measurement"]
        assert m is not None and m.source == "external"
        assert at.session_state["nav_page"] == "Air Quality Explorer"


class TestDesignSystemRegression:
    """Guard the redesigned presentation layer: nav groups, AQI summary,
    illustrations and new page compositions must keep rendering."""

    def test_nav_groups_render(self):
        at = _app()
        labels = [m.value for m in at.sidebar.markdown]
        joined = "\n".join(labels)
        for group in ("DISCOVER", "UNDERSTAND YOUR AIR",
                      "IMPROVE YOUR ENVIRONMENT", "TRACK YOUR IMPACT"):
            assert group in joined

    def test_home_shows_illustrations_and_sample_label(self):
        at = _app()
        at.run()
        html_out = "\n".join(m.value for m in at.markdown)
        assert 'class="scene"' in html_out
        assert "Sample reading" in html_out
        assert "not a live reading" in html_out.lower()

    def test_sidebar_aqi_summary_with_measurement(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[1])
        at.run()
        labels = [m.value for m in at.sidebar.markdown]
        joined = "\n".join(labels)
        assert SAMPLE_MEASUREMENTS[1].category_name in joined
        assert SAMPLE_MEASUREMENTS[1].location.split(" (")[0] in joined

    def test_entry_cards_have_sample_preview(self):
        at = _app()
        at.run()
        html_out = "\n".join(m.value for m in at.markdown)
        assert "Sample cities" in html_out

    def test_planner_timeline_steps(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0])
        _goto(at, "My Daily Air Plan")
        html_out = "\n".join(m.value for m in at.markdown)
        assert html_out.count('class="aw-tstep"') >= 6

    def test_community_checklist_in_border(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0])
        _goto(at, "Family & Community")
        assert len(at.checkbox) >= 9

    def test_impact_dashboard_sections(self):
        at = _app(measurement=SAMPLE_MEASUREMENTS[0])
        _goto(at, "Environmental Impact")
        text = "\n".join(m.value for m in at.markdown)
        assert "Compare a trip" in text
        assert "impact dashboard" in text


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
