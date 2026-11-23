from airaware.data import MeasurementSet
from airaware.recommendations import UserProfile, generate_recommendations


def _mse(cat_pollutants):
    return MeasurementSet(location="Test", pollutants=cat_pollutants,
                          source="user").finalize()


def _profile(**kw):
    defaults = dict(city="Delhi", lifestyle="office", transport="car",
                    household="alone", outdoor_pref="moderate",
                    concerns=[], budget="low", priority="health")
    defaults.update(kw)
    return UserProfile(**defaults)


def _all_titles(recs):
    return [r.title for group in recs.values() for r in group]


class TestEngine:
    def test_good_air_allows_outdoor(self):
        m = _mse({"pm25": 20, "pm10": 30})
        recs = generate_recommendations(m, _profile())
        titles = _all_titles(recs)
        assert any("acceptable" in t.lower() for t in titles)

    def test_poor_air_warns(self):
        m = _mse({"pm25": 200})  # Very Poor band
        recs = generate_recommendations(m, _profile(outdoor_pref="heavy"))
        titles = _all_titles(recs)
        assert any("indoors" in t.lower() or "indoor" in t.lower()
                   for t in titles)
        # avoid group should have entries
        assert len(recs["avoid"]) > 0

    def test_runner_gets_swap_advice(self):
        m = _mse({"pm25": 150})  # Moderate
        recs = generate_recommendations(m, _profile(lifestyle="runner"))
        assert any("run" in r.title.lower() for r in recs["today"])

    def test_parent_gets_kids_advice(self):
        m = _mse({"pm25": 150})
        recs = generate_recommendations(
            m, _profile(lifestyle="parent", household="children"))
        assert any("children" in r.title.lower() for r in recs["today"])

    def test_sample_flagged(self):
        m = MeasurementSet(location="S", pollutants={"pm25": 50},
                           source="sample").finalize()
        recs = generate_recommendations(m, _profile())
        assert any("demonstration" in r.title.lower()
                   for r in recs["understanding"])

    def test_every_rec_has_reason(self):
        m = _mse({"pm25": 250, "no2": 300})
        recs = generate_recommendations(m, _profile())
        for group in recs.values():
            for r in group:
                assert r.reason.strip()
                assert r.detail.strip()
