# Integrator Benchmark Summary

9-body Sun + 8-planets system, integrated for 50 years.
Initial conditions: each planet at perihelion with vis-viva perihelion speed,
derived analytically from physics_engine.SOLAR_SYSTEM (a, e, period). No network access used.

| Integrator | Final \|ΔE/E\| | Max \|ΔE/E\| | Wall time (s) |
|---|---|---|---|
| ias15 | 5.86e-16 | 2.35e-15 | 0.165 |
| whfast | 2.91e-10 | 3.63e-10 | 0.016 |
| leapfrog | 1.78e-07 | 3.60e-06 | 0.003 |
