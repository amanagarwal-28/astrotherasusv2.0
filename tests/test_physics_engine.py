"""
Validates physics_engine.py's Keplerian propagator and Hohmann transfer
calculator against known two-body results.

Hohmann reference values (Curtis, "Orbital Mechanics for Engineering
Students"; also NASA mission-design literature): an Earth->Mars heliocentric
Hohmann transfer takes ~259 days with a combined heliocentric delta-v of
~5.6 km/s (excluding planetary escape/capture delta-v).
"""
import numpy as np
import pytest

from physics_engine import SOLAR_SYSTEM, compute_hohmann, compute_orbit, solve_kepler

AU_YR_TO_KM_S = 4.740


def test_solve_kepler_satisfies_keplers_equation():
    M = np.linspace(0, 2 * np.pi, 50)
    e = 0.6
    E = solve_kepler(M, e)
    # By definition M = E - e*sin(E); the solver must satisfy this to its tolerance.
    residual = np.abs(M - (E - e * np.sin(E)))
    assert np.max(residual) < 1e-8


def test_compute_orbit_radius_matches_perihelion_and_aphelion_bounds():
    orbit = compute_orbit("mars", duration_days=687, steps=500)
    r = np.array(orbit["r"])
    body = SOLAR_SYSTEM["mars"]
    a, e = body["a"], body["e"]
    assert r.min() == pytest.approx(a * (1 - e), rel=0.02)
    assert r.max() == pytest.approx(a * (1 + e), rel=0.02)


def test_compute_orbit_is_periodic():
    body = SOLAR_SYSTEM["earth"]
    orbit = compute_orbit("earth", duration_days=body["period"], steps=1000)
    x, y = np.array(orbit["x"]), np.array(orbit["y"])
    # Position one full period later must return to the starting point.
    assert x[-1] == pytest.approx(x[0], abs=1e-3)
    assert y[-1] == pytest.approx(y[0], abs=1e-3)


def test_compute_orbit_unknown_body_returns_none():
    assert compute_orbit("planet-nine") is None


def test_hohmann_earth_mars_transfer_time_matches_textbook_value():
    h = compute_hohmann("earth", "mars")
    assert h["transfer_days"] == pytest.approx(259, abs=5)


def test_hohmann_earth_mars_delta_v_matches_textbook_value():
    h = compute_hohmann("earth", "mars")
    total_km_s = h["total_delta_v"] * AU_YR_TO_KM_S
    assert total_km_s == pytest.approx(5.6, abs=0.3)


def test_hohmann_transfer_orbit_lies_between_departure_and_arrival_radii():
    h = compute_hohmann("earth", "mars")
    r_t = np.sqrt(np.array(h["transfer_x"]) ** 2 + np.array(h["transfer_y"]) ** 2)
    assert r_t.min() >= h["r1_au"] - 1e-6
    assert r_t.max() <= h["r2_au"] + 1e-6


def test_hohmann_unknown_body_returns_none():
    assert compute_hohmann("earth", "planet-nine") is None
