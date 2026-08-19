"""
Validates orbital_accuracy.py's three scoring modes.

The offline tests formalize the manual checks that used to live in
orbital_accuracy.py's __main__ block: a stable integrator (ias15) on a
sensible orbit should score high, while a poor integrator/orbit
combination (leapfrog on a highly eccentric orbit) should score
measurably lower — demonstrating the checker actually discriminates
between good and bad physics rather than always reporting "OK".

The network-marked tests hit NASA JPL Horizons for ground-truth
positions and are skipped automatically when offline.
"""
import math

import pytest

from orbital_accuracy import compute_accuracy, physics_correctness
from rebound_engine import ReboundEngine

G_SOLAR = 4 * math.pi ** 2


def test_hot_jupiter_under_ias15_stays_accurate():
    v_circ = math.sqrt(G_SOLAR * 1.0 / 0.05)
    scenario = {
        "name": "Hot Jupiter", "units": "solar", "integrator": "ias15",
        "t_per_frame": 0.001, "scale": 600,
        "bodies": [
            {"name": "Star", "mass": 1.0, "x": 0, "y": 0, "vx": 0, "vy": 0},
            {"name": "Hot Jupiter", "mass": 0.001, "x": 0.05, "y": 0, "vx": 0, "vy": v_circ},
        ],
    }
    engine = ReboundEngine()
    engine.load_scenario(scenario)
    engine.sim.integrate(5.0)
    result = compute_accuracy(engine)
    assert result["mode"] == "physics"
    assert result["overall"] > 95


def test_leapfrog_on_highly_eccentric_orbit_scores_worse_than_ias15():
    # v = 0.5 AU/yr at r = 1 AU is far below circular velocity (~6.28 AU/yr)
    # for a 1 Msun primary, producing e ~ 0.999 — a regime where a low-order
    # symplectic integrator accumulates visible drift over 10 years.
    bad_scenario = {
        "name": "Eccentric", "units": "solar", "integrator": "leapfrog", "dt": 0.01,
        "t_per_frame": 0.001, "scale": 600,
        "bodies": [
            {"name": "Star", "mass": 1.0, "x": 0, "y": 0, "vx": 0, "vy": 0},
            {"name": "Planet", "mass": 0.001, "x": 1.0, "y": 0, "vx": 0, "vy": 0.5},
        ],
    }
    good_scenario = {**bad_scenario, "integrator": "ias15"}

    bad_engine = ReboundEngine()
    bad_engine.load_scenario(bad_scenario)
    bad_engine.sim.integrate(10.0)
    bad_result = physics_correctness(bad_engine)

    good_engine = ReboundEngine()
    good_engine.load_scenario(good_scenario)
    good_engine.sim.integrate(10.0)
    good_result = physics_correctness(good_engine)

    assert bad_result["overall"] < good_result["overall"]


def test_physics_correctness_at_t0_is_perfect_by_construction():
    v_circ = math.sqrt(G_SOLAR)
    scenario = {
        "name": "Circular", "units": "solar", "integrator": "ias15",
        "t_per_frame": 0.01, "scale": 200,
        "bodies": [
            {"name": "Star", "mass": 1.0, "x": 0, "y": 0, "vx": 0, "vy": 0},
            {"name": "Planet", "mass": 1e-6, "x": 1.0, "y": 0, "vx": 0, "vy": v_circ},
        ],
    }
    engine = ReboundEngine()
    engine.load_scenario(scenario)
    result = physics_correctness(engine)
    assert result["overall"] == pytest.approx(100.0, abs=0.01)


@pytest.mark.network
def test_ephemeris_accuracy_for_real_solar_system_is_high():
    engine = ReboundEngine()
    engine.load_from_horizons(["Sun", "Mercury", "Venus", "Earth", "Mars"], integrator="whfast")
    result = compute_accuracy(engine)
    assert result["mode"] in ("predictive", "ephemeris")
    assert result["overall"] > 90


@pytest.mark.network
def test_predictive_accuracy_reflects_two_body_approximation_error():
    # A bare Sun+Earth two-body model omits Jupiter/Venus/Moon perturbations.
    # Its position error relative to the real (perturbed) ephemeris is
    # therefore bounded but non-trivial — nowhere near the ~100% score the
    # full 5-body system gets in test_ephemeris_accuracy_for_real_solar_system_is_high,
    # yet still a well-formed, finite score. This is a useful regression
    # signal: if this ever scores >95%, predictive_accuracy() is silently
    # comparing a sim against itself instead of a real Horizons query.
    engine = ReboundEngine()
    engine.load_from_horizons(["Sun", "Earth"], integrator="ias15")
    engine.sim.integrate(1.0)

    result = compute_accuracy(engine)
    assert result["mode"] == "predictive"
    assert 0 <= result["overall"] < 95
    # ias15 is high-precision; energy conservation itself should still be excellent
    # even though the two-body *model* diverges from the perturbed real orbit.
    assert abs(result["energy_drift"]) < 1e-8
