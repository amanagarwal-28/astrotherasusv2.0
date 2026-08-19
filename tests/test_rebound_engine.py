"""
Validates the REBOUND N-body wrapper's energy conservation and orbital
element recovery for scenarios that don't require network access.
"""
import math

import pytest

from rebound_engine import (
    ReboundEngine,
    binary_star_system,
    hohmann_transfer,
    lagrange_point_scenario,
    orbital_resonance_scenario,
    three_body_figure8,
)

G_SOLAR = 4 * math.pi ** 2


def _circular_two_body_scenario(integrator="ias15"):
    v_circ = math.sqrt(G_SOLAR * 1.0 / 1.0)
    scenario = {
        "name": "Sun-Earth analogue",
        "units": "solar",
        "integrator": integrator,
        "t_per_frame": 0.01,
        "scale": 200,
        "bodies": [
            {"name": "Star", "mass": 1.0, "x": 0, "y": 0, "vx": 0, "vy": 0},
            {"name": "Planet", "mass": 3e-6, "x": 1.0, "y": 0, "vx": 0, "vy": v_circ},
        ],
    }
    engine = ReboundEngine()
    engine.load_scenario(scenario)
    return engine


@pytest.mark.parametrize("integrator", ["ias15", "whfast"])
def test_energy_conserved_over_ten_orbits(integrator):
    engine = _circular_two_body_scenario(integrator)
    engine.sim.integrate(10.0)  # 10 years == 10 orbits for a 1 AU circular orbit
    frame = engine.get_frame()
    # High-quality integrators should hold energy drift near machine precision.
    assert abs(frame["energy_drift"]) < 1e-6


def test_circular_orbit_recovers_correct_semi_major_axis_and_eccentricity():
    engine = _circular_two_body_scenario("ias15")
    elements = engine.get_orbital_elements()
    assert len(elements) == 1
    assert elements[0]["a"] == pytest.approx(1.0, rel=1e-3)
    assert elements[0]["e"] == pytest.approx(0.0, abs=1e-3)


def test_circular_orbit_period_matches_keplers_third_law():
    engine = _circular_two_body_scenario("ias15")
    elements = engine.get_orbital_elements()
    assert elements[0]["P"] == pytest.approx(1.0, rel=1e-3)


def test_reset_restores_initial_energy():
    engine = _circular_two_body_scenario("ias15")
    e0 = engine.sim.energy()
    engine.sim.integrate(5.0)
    engine.reset()
    assert engine.sim.energy() == pytest.approx(e0, rel=1e-9)


def test_figure8_choreography_conserves_energy():
    engine = three_body_figure8()
    engine.sim.integrate(2.0)
    frame = engine.get_frame()
    assert abs(frame["energy_drift"]) < 1e-4


def test_binary_star_system_conserves_total_momentum():
    engine = binary_star_system(mass1=1.0, mass2=0.8, separation=3.0, eccentricity=0.3)
    p1, p2 = engine.sim.particles[0], engine.sim.particles[1]
    total_px = p1.m * p1.vx + p2.m * p2.vx
    total_py = p1.m * p1.vy + p2.m * p2.vy
    assert total_px == pytest.approx(0.0, abs=1e-9)
    assert total_py == pytest.approx(0.0, abs=1e-9)


def test_lagrange_l4_trojan_stays_near_60_degrees_from_secondary():
    # The defining feature of a stable Lagrange point: a test body placed
    # there should co-orbit indefinitely rather than drifting away.
    import math as _math
    engine = lagrange_point_scenario(point="L4", secondary="Jupiter")
    engine.sim.integrate(50.0)  # ~4 Jupiter orbital periods (P=11.86 yr)
    trojan, jup = engine.sim.particles[2], engine.sim.particles[1]
    r_trojan = _math.hypot(trojan.x, trojan.y)
    r_jup = _math.hypot(jup.x, jup.y)
    angle = _math.degrees(_math.acos(
        (trojan.x * jup.x + trojan.y * jup.y) / (r_trojan * r_jup)
    ))
    assert r_trojan == pytest.approx(r_jup, rel=0.02)
    assert angle == pytest.approx(60.0, abs=2.0)


def test_orbital_resonance_produces_exact_period_ratio():
    engine = orbital_resonance_scenario(resonance="3:2")
    elements = engine.get_orbital_elements()
    inner, outer = elements[0], elements[1]
    assert outer["P"] / inner["P"] == pytest.approx(1.5, rel=1e-3)


def test_hohmann_transfer_scenario_has_sun_two_planets_and_spacecraft():
    engine = hohmann_transfer("Earth", "Mars")
    names = [b["name"] for b in engine.body_info]
    assert names == ["Sun", "Earth", "Mars", "Spacecraft"]
    # Spacecraft starts on the departure planet's orbit (r = 1 AU for Earth)
    spacecraft = engine.sim.particles[3]
    assert math.hypot(spacecraft.x, spacecraft.y) == pytest.approx(1.0, rel=1e-3)
