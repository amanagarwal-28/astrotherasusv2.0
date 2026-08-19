"""
Smoke tests for the reproducible offline integrator benchmark used to
generate the paper's energy-conservation figure (benchmarks/integrator_comparison.py).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "benchmarks"))
import integrator_comparison as bench  # noqa: E402


def test_build_solar_system_has_nine_bodies():
    sim = bench.build_solar_system("ias15")
    assert sim.N == 9  # Sun + 8 planets


@pytest.mark.parametrize("integrator", bench.INTEGRATORS)
def test_build_solar_system_starts_with_finite_energy(integrator):
    sim = bench.build_solar_system(integrator)
    E0 = sim.energy()
    assert E0 == E0  # not NaN
    assert E0 != 0.0


def test_ias15_energy_drift_is_tiny_after_short_integration():
    sim = bench.build_solar_system("ias15")
    E0 = sim.energy()
    sim.integrate(2.0)
    drift = abs((sim.energy() - E0) / E0)
    assert drift < 1e-9
