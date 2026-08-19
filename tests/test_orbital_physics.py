"""
Validates orbital_physics.py against textbook two-body results.

Reference values (Curtis, "Orbital Mechanics for Engineering Students"):
  - Earth orbital period: 365.25 days by definition of the year
  - Moon orbital period: 27.32 days (sidereal month)
  - Momentum conservation must hold exactly for any binary pair
"""
import math

import pytest

from orbital_physics import (
    G_SOLAR,
    binary_velocities,
    check_orbit_stability,
    circular_orbit_velocity,
    escape_velocity,
    orbital_period,
    velocity_from_period,
)

M_SUN = 1.0
M_EARTH = 3.003e-6


def test_earth_orbital_period_is_one_year():
    period = orbital_period(M_SUN, radius=1.0)
    assert period == pytest.approx(1.0, rel=1e-3)


def test_moon_orbital_period_matches_sidereal_month():
    period_days = orbital_period(M_EARTH, radius=0.00257) * 365.25
    assert period_days == pytest.approx(27.32, abs=0.5)


def test_circular_velocity_and_period_are_consistent():
    r = 2.5
    v = circular_orbit_velocity(M_SUN, r)
    period = orbital_period(M_SUN, r)
    v_from_period = velocity_from_period(r, period)
    assert v == pytest.approx(v_from_period, rel=1e-9)


def test_escape_velocity_is_sqrt2_times_circular():
    r = 1.0
    v_circ = circular_orbit_velocity(M_SUN, r)
    v_esc = escape_velocity(M_SUN, r)
    assert v_esc == pytest.approx(v_circ * math.sqrt(2), rel=1e-9)


def test_binary_velocities_conserve_momentum():
    m1, m2 = 1.0, 0.8
    v1, v2 = binary_velocities(m1, m2, separation=3.0, eccentricity=0.0)
    assert m1 * v1 + m2 * v2 == pytest.approx(0.0, abs=1e-9)


def test_binary_velocities_scale_inversely_with_mass():
    # Momentum conservation (m1*v1 = m2*v2 in magnitude): the lighter body
    # moves faster. Here m1=1 is half of m2=2, so v1 must be twice |v2|.
    v1, v2 = binary_velocities(1.0, 2.0, separation=3.0)
    assert abs(v1) == pytest.approx(abs(v2) * 2, rel=1e-9)


def test_orbit_stability_flags_too_slow_as_crash():
    v_circ = circular_orbit_velocity(M_SUN, 1.0)
    result = check_orbit_stability(M_SUN, 1.0, velocity=v_circ * 0.3)
    assert result["type"] == "WILL CRASH (too slow)"
    assert result["is_stable"] is False


def test_orbit_stability_flags_circular_orbit():
    v_circ = circular_orbit_velocity(M_SUN, 1.0)
    result = check_orbit_stability(M_SUN, 1.0, velocity=v_circ)
    assert result["type"] == "circular"
    assert result["is_stable"] is True


def test_orbit_stability_flags_hyperbolic_escape():
    v_esc = escape_velocity(M_SUN, 1.0)
    result = check_orbit_stability(M_SUN, 1.0, velocity=v_esc * 2.0)
    assert result["type"] == "hyperbolic (unbound)"


def test_g_solar_matches_four_pi_squared():
    assert G_SOLAR == pytest.approx(4 * math.pi ** 2, rel=1e-12)
