import pytest

from airaware.impact import (estimate_ac_savings, estimate_trip_savings,
                             summarise_actions, ImpactAction)


class TestTripSavings:
    def test_car_to_metro_saves(self):
        est = estimate_trip_savings("metro", "car_petrol", 10)
        assert est["co2e_saved_kg"] > 0
        assert est["fuel_saved_litres"] is not None

    def test_walk_zero_new_emissions(self):
        est = estimate_trip_savings("walk", "car_petrol", 5)
        # walking has 0 factor -> full avoided emissions counted
        assert est["co2e_saved_kg"] == pytest.approx(0.192 * 5, abs=0.01)

    def test_reverse_direction_negative(self):
        est = estimate_trip_savings("car_petrol", "metro", 10)
        assert est["co2e_saved_kg"] < 0

    def test_invalid_mode(self):
        with pytest.raises(ValueError):
            estimate_trip_savings("spaceship", "car_petrol", 5)

    def test_zero_distance(self):
        with pytest.raises(ValueError):
            estimate_trip_savings("walk", "car_petrol", 0)


class TestAcSavings:
    def test_positive_hours(self):
        r = estimate_ac_savings(2)
        assert r["kwh_saved_per_day"] == pytest.approx(3.0)
        assert r["co2e_saved_kg_per_year"] > 0

    def test_negative_hours(self):
        with pytest.raises(ValueError):
            estimate_ac_savings(-1)


class TestSummarise:
    def test_aggregation(self):
        acts = [
            ImpactAction(action_type="trip", description="t",
                         vehicle="walk", avoided_vehicle="car_petrol",
                         distance_km=4, cost_saved_inr=50),
            ImpactAction(action_type="energy", description="e",
                         kwh_saved=3.0, cost_saved_inr=30),
        ]
        s = summarise_actions(acts)
        assert s["total_actions"] == 2
        assert s["total_co2e_saved_kg"] > 0
        assert s["trip_km"] == 4
        assert s["indicative_cost_saved_inr"] == 80
        assert s["by_type"]["trip"] == 1
