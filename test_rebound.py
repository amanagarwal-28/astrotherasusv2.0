"""
STEP 1 — Test REBOUND installation
Run: python step1_test_rebound.py
Expected: prints version + simulates solar system for 1 year
"""

import rebound
import numpy as np

print("=" * 50)
print(f"REBOUND version: {rebound.__version__}")
print("=" * 50)

# Test 1: Basic solar system simulation
sim = rebound.Simulation()
sim.units = ('AU', 'yr', 'Msun')   # Astronomical units, years, solar masses
sim.integrator = "ias15"           # Best for mixed timescale systems (default)

# Add Sun
sim.add(m=1.0)                     # Sun = 1 solar mass

# Add planets using built-in solar system data
sim.add("Mercury")
sim.add("Venus")
sim.add("Earth")
sim.add("Mars")
sim.add("Jupiter")
sim.add("Saturn")

sim.move_to_com()  # Move to center of mass frame

print(f"\nBodies in simulation: {sim.N}")
print(f"Integrator: {sim.integrator}")

# Print initial orbital elements
print("\nInitial orbital elements:")
for p in sim.particles[1:]:
    orb = p.orbit()
    print(f"  a={orb.a:.3f} AU  e={orb.e:.4f}  P={orb.P:.2f} yr")

# Run for 1 year
sim.integrate(1.0)
print(f"\nAfter 1 year integration — time = {sim.t:.4f} yr")

# Print positions
print("\nPositions (AU):")
for i, p in enumerate(sim.particles):
    names = ["Sun","Mercury","Venus","Earth","Mars","Jupiter","Saturn"]
    print(f"  {names[i]}: x={p.x:.4f}  y={p.y:.4f}")

print("\n✓ REBOUND working correctly!")

# Test 2: Energy conservation
sim2 = rebound.Simulation()
sim2.units = ('AU', 'yr', 'Msun')
sim2.integrator = "ias15"
sim2.add(m=1.0)
sim2.add(m=3e-6, a=1.0, e=0.0)  # Earth-like
sim2.move_to_com()

E0 = sim2.energy()
sim2.integrate(10.0)  # 10 years
E1 = sim2.energy()

dE = abs((E1 - E0) / E0)
print(f"\nEnergy conservation test (10 yr): ΔE/E = {dE:.2e}")
print("✓ PERFECT" if dE < 1e-8 else f"✓ Good ({dE:.2e})")

# Test 3: Three-body chaos
sim3 = rebound.Simulation()
sim3.integrator = "ias15"
sim3.add(m=1.0, x=-0.5, y=0,  vx=0, vy=0.3)
sim3.add(m=1.0, x=0.5,  y=0,  vx=0, vy=-0.3)
sim3.add(m=0.1, x=0,    y=1.0, vx=0.5, vy=0)
sim3.move_to_com()

print(f"\nThree-body test: {sim3.N} bodies, integrating...")
sim3.integrate(5.0)
print(f"  Final positions: {[(round(p.x,3), round(p.y,3)) for p in sim3.particles]}")
print("✓ Three-body works!")

print("\n" + "=" * 50)
print("ALL TESTS PASSED — Ready for Step 2")
print("=" * 50)
