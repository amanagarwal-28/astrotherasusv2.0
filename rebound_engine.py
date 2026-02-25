"""
STEP 2 — REBOUND Simulation Engine (FIXED)
This is the core physics layer. It:
  - Accepts ANY scenario description as a Python dict
  - Uses REBOUND's IAS15 integrator (adaptive timestep, near machine precision)
  - Supports: solar system, custom bodies, Horizons NASA data, exoplanets
  - Returns frame-by-frame state for the frontend
  
FIX: Added proper None checks to prevent 'NoneType' object has no attribute 'particles' error
"""

import rebound
import numpy as np
import json
import math

# ── INTEGRATORS AVAILABLE IN REBOUND ────────────────────────
# "ias15"    — Default. Adaptive timestep. Near machine precision. Best for most cases.
# "whfast"   — Fast symplectic. Best for long-term planetary systems (no close encounters).
# "mercurius" — Hybrid: WHFast for far bodies, IAS15 for close encounters.
# "leapfrog" — Simple symplectic. Fast but lower accuracy.
# "saba"     — Higher-order symplectic. Good for planetary systems.
# "bs"       — Bulirsch-Stoer. Great for high-accuracy short integrations.

INTEGRATOR_GUIDE = {
    "solar_system":      "whfast",     # fast, stable, long-term
    "close_encounter":   "mercurius",  # hybrid, handles close passes
    "three_body":        "ias15",      # chaotic — needs adaptive step
    "binary":            "ias15",      # precise
    "default":           "ias15",      # safest default
}

# ── UNIT SYSTEMS ─────────────────────────────────────────────
# REBOUND is unit-free — you pick consistent units.
# Common choices:
#   AU / yr  / Msun  → G = 4π² ≈ 39.48  (default for solar system)
#   AU / day / Msun  → G = 2.959e-4
#   m  / s   / kg    → G = 6.674e-11

class ReboundEngine:
    """
    Universal N-body simulation engine wrapping REBOUND.
    
    Usage:
        engine = ReboundEngine()
        engine.load_scenario(scenario_dict)
        
        for _ in range(1000):
            frame = engine.step()
            # frame contains x,y positions of all bodies for rendering
    """

    def __init__(self):
        self.sim = None
        self.meta = {}        # scenario metadata
        self.bodies = []
        self.initial_scenario = None
        self.body_info = []   # colors, radii, types for rendering
        self.t_per_frame = 0.01   # simulation time per frame
        self.scale = 1.0      # AU → canvas pixels
        self._E0 = 0.0        # Initial energy
    
    def reset(self):
        """Reset simulation to initial state."""
        if self.initial_scenario:
            self.load_scenario(self.initial_scenario)
        else:
            # Clear everything if no initial scenario
            self.sim = None
            self.bodies = []
            self.body_info = []
            self._E0 = 0.0

    # ── LOAD SCENARIO ────────────────────────────────────────

    def load_scenario(self, scenario: dict) -> dict:
        """
        Load a scenario from a dict. Scenario format:
        {
          "name": "Solar System",
          "description": "...",
          "units": "solar",          # "solar" | "normalized" | "custom"
          "integrator": "whfast",
          "t_per_frame": 0.01,       # simulation time per rendered frame
          "scale": 200,              # AU to canvas pixels (for solar system)
          "bodies": [
            {
              "name": "Sun",
              "mass": 1.0,           # in chosen units
              "x": 0.0, "y": 0.0,   # AU
              "vx": 0.0, "vy": 0.0, # AU/yr
              "color": "#fff200",
              "radius": 20,          # pixels for display
              "type": "star"
            },
            ...
          ]
        }
        Returns: metadata dict with initial state
        """
        self.sim = rebound.Simulation()

        units = scenario.get("units", "solar")
        if units == "solar":
            self.sim.units = ('AU', 'yr', 'Msun')

        integrator = scenario.get("integrator", "ias15")
        self.sim.integrator = integrator

        # Softening for close encounters (optional)
        softening = scenario.get("softening", 0.0)
        if softening > 0:
            self.sim.softening = softening

        # Timestep (only for fixed-step integrators)
        if integrator in ("whfast", "leapfrog", "saba"):
            self.sim.dt = scenario.get("dt", 0.001)

        self.t_per_frame = scenario.get("t_per_frame", 0.01)
        self.scale       = scenario.get("scale", 200.0)
        self.meta        = {
            "name":        scenario.get("name", "Simulation"),
            "description": scenario.get("description", ""),
            "integrator":  integrator,
            "units":       units,
            "N":           len(scenario["bodies"]),
        }
        self.body_info = []

        # Add bodies to REBOUND
        for b in scenario["bodies"]:
            self.sim.add(
                m   = b.get("mass", 1.0),
                x   = b.get("x",  0.0),
                y   = b.get("y",  0.0),
                z   = 0.0,
                vx  = b.get("vx", 0.0),
                vy  = b.get("vy", 0.0),
                vz  = 0.0,
            )
            self.body_info.append({
                "name":   b.get("name", f"Body-{len(self.body_info)}"),
                "color":  b.get("color",  "#ffffff"),
                "radius": b.get("radius", 5),
                "type":   b.get("type",   "planet"),
            })

        self.sim.move_to_com()

        # Record initial energy for conservation monitoring
        self._E0 = self.sim.energy()
        
        # Store scenario for reset functionality
        self.initial_scenario = scenario

        return self.get_frame()

    def load_from_horizons(self, body_names: list, integrator="whfast") -> dict:
        """
        Load real solar system bodies from NASA JPL Horizons via REBOUND's built-in fetcher.
        This gets ACTUAL current positions and velocities!

        Example: load_from_horizons(["Sun", "Mercury", "Venus", "Earth", "Mars"])
        """
        self.sim = rebound.Simulation()
        self.sim.units = ('AU', 'yr', 'Msun')
        self.sim.integrator = integrator
        if integrator == "whfast":
            self.sim.dt = 0.001  # 1/1000 yr ≈ 0.365 days

        # Color/size lookup for known bodies
        BODY_STYLES = {
            "Sun":     {"color": "#fff200", "radius": 22, "type": "star",   "mass_hint": 1.0},
            "Mercury": {"color": "#b5b5b5", "radius": 4,  "type": "planet"},
            "Venus":   {"color": "#e8cda0", "radius": 6,  "type": "planet"},
            "Earth":   {"color": "#4fffb0", "radius": 7,  "type": "planet"},
            "Mars":    {"color": "#ff6b35", "radius": 5,  "type": "planet"},
            "Jupiter": {"color": "#c88b3a", "radius": 14, "type": "planet"},
            "Saturn":  {"color": "#e4d191", "radius": 12, "type": "planet"},
            "Uranus":  {"color": "#7de8e8", "radius": 9,  "type": "planet"},
            "Neptune": {"color": "#3f54ba", "radius": 9,  "type": "planet"},
            "Pluto":   {"color": "#c9a87c", "radius": 3,  "type": "planet"},
        }

        self.body_info = []
        for name in body_names:
            self.sim.add(name)   # REBOUND fetches from Horizons automatically!
            style = BODY_STYLES.get(name, {"color": "#aaaaaa", "radius": 5, "type": "planet"})
            self.body_info.append({"name": name, **style})

        self.sim.move_to_com()
        self._E0 = self.sim.energy()
        self.t_per_frame = 0.005
        self.scale = 200.0
        self.meta = {
            "name": " + ".join(body_names),
            "description": "Real NASA Horizons data",
            "integrator": integrator,
            "units": "solar",
            "N": len(body_names),
        }
        
        # Store for reset (simplified - won't re-fetch from Horizons)
        self.initial_scenario = {
            "use_horizons": body_names,
            "integrator": integrator
        }
        
        return self.get_frame()

    # ── STEP & GET FRAME ─────────────────────────────────────

    def step(self, n_frames=1) -> dict:
        """Advance simulation by n_frames and return current state."""
        if self.sim is None:
            raise RuntimeError("No simulation loaded. Call load_scenario() or load_from_horizons() first.")
        
        self.sim.integrate(self.sim.t + self.t_per_frame * n_frames)
        return self.get_frame()

    def get_frame(self) -> dict:
        """
        Returns current state as a dict ready for JSON serialization.
        Positions are in simulation units (AU for solar system).
        Frontend scales them to canvas pixels using self.scale.
        """
        if self.sim is None:
            return {
                "t": 0.0,
                "N": 0,
                "bodies": [],
                "energy_drift": 0.0,
            }
        
        bodies = []
        for i, p in enumerate(self.sim.particles):
            info = self.body_info[i] if i < len(self.body_info) else {}
            speed = math.sqrt(p.vx**2 + p.vy**2)
            bodies.append({
                "name":   info.get("name",   f"Body-{i}"),
                "x":      round(p.x,  6),
                "y":      round(p.y,  6),
                "vx":     round(p.vx, 6),
                "vy":     round(p.vy, 6),
                "speed":  round(speed, 6),
                "mass":   round(p.m, 9),
                "color":  info.get("color",  "#ffffff"),
                "radius": info.get("radius", 5),
                "type":   info.get("type",   "planet"),
            })

        # Energy conservation check
        E_now = self.sim.energy()
        drift = abs((E_now - self._E0) / self._E0) if self._E0 != 0 else 0.0

        return {
            "t":      round(self.sim.t, 6),
            "N":      self.sim.N,
            "bodies": bodies,
            "energy_drift": round(drift, 12),
        }

    def get_orbital_elements(self) -> list:
        """
        Compute orbital elements for all bodies orbiting the primary (first body).
        Returns list of dicts with: a, e, i, Omega, omega, f
        """
        if self.sim is None or self.sim.N < 2:
            return []
        
        elements = []
        primary = self.sim.particles[0]
        
        for i in range(1, self.sim.N):
            p = self.sim.particles[i]
            try:
                orb = p.orbit(primary=primary)
                elements.append({
                    "name":      self.body_info[i]["name"] if i < len(self.body_info) else f"Body-{i}",
                    "a":         round(orb.a, 6),       # semi-major axis
                    "e":         round(orb.e, 6),       # eccentricity
                    "inc":       round(orb.inc * 180/math.pi, 3),  # inclination (degrees)
                    "Omega":     round(orb.Omega * 180/math.pi, 3), # longitude of ascending node
                    "omega":     round(orb.omega * 180/math.pi, 3), # argument of periapsis
                    "f":         round(orb.f * 180/math.pi, 3),     # true anomaly
                    "P":         round(orb.P, 6),       # orbital period
                    "n":         round(orb.n, 6),       # mean motion
                })
            except Exception as e:
                # Some bodies might not have well-defined orbits (e.g., unbound)
                elements.append({
                    "name": self.body_info[i]["name"] if i < len(self.body_info) else f"Body-{i}",
                    "error": str(e)
                })
        
        return elements

    def get_trajectories(self, duration, n_points=200):
        """
        Compute future trajectories for all bodies without modifying current simulation.
        Returns list of trajectory arrays (one per body).
        """
        if self.sim is None:
            return []
        
        # Save current state
        sim_copy = self.sim.copy()
        
        dt = duration / n_points
        trajectories = [[] for _ in range(self.sim.N)]
        
        t_copy = sim_copy.t
        for step in range(n_points):
            sim_copy.integrate(t_copy + step * dt)
            for i, p in enumerate(sim_copy.particles):
                trajectories[i].append((round(p.x, 4), round(p.y, 4)))
        
        return trajectories


# ── SCENARIO TEMPLATES ───────────────────────────────────────
# These are the "starter" scenarios. The AI can generate ANY variation.

def solar_system_real():
    """Real solar system from NASA Horizons data."""
    engine = ReboundEngine()
    engine.load_from_horizons(
        ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn"],
        integrator="whfast"
    )
    engine.scale = 180.0
    engine.t_per_frame = 0.004  # ~1.5 days per frame
    return engine

def three_body_figure8():
    """
    Chenciner & Montgomery (2000) figure-8 choreography.
    Three equal masses chasing each other in a figure-8.
    """
    engine = ReboundEngine()
    engine.load_scenario({
        "name": "Figure-8 Choreography",
        "description": "Three equal masses in perfect figure-8 (Chenciner & Montgomery 2000)",
        "units": "normalized",
        "integrator": "ias15",
        "t_per_frame": 0.005,
        "scale": 200.0,
        "bodies": [
            # Exact initial conditions from Chenciner & Montgomery
            {"name": "Body A", "mass": 1.0,
             "x":  0.9700436, "y": -0.2430870,
             "vx": 0.4662036/2, "vy":  0.4323657/2,
             "color": "#ff6b35", "radius": 9, "type": "star"},
            {"name": "Body B", "mass": 1.0,
             "x": -0.9700436, "y":  0.2430870,
             "vx": 0.4662036/2, "vy":  0.4323657/2,
             "color": "#4fffb0", "radius": 9, "type": "star"},
            {"name": "Body C", "mass": 1.0,
             "x":  0.0,       "y":  0.0,
             "vx":-0.4662036, "vy": -0.4323657,
             "color": "#bf7fff", "radius": 9, "type": "star"},
        ]
    })
    return engine

def binary_star_system(mass1=1.0, mass2=1.0, separation=2.0, eccentricity=0.0):
    """Configurable binary star system."""
    # Compute velocities for circular/elliptical orbit
    G = 4 * math.pi**2  # AU/yr/Msun
    mu = G * (mass1 + mass2)
    a  = separation / 2.0
    
    # Vis-viva for elliptical orbit
    r  = separation * (1 - eccentricity) if eccentricity > 0 else separation
    v_total = math.sqrt(mu * (2/r - 1/separation))
    
    v1 =  v_total * mass2 / (mass1 + mass2)
    v2 = -v_total * mass1 / (mass1 + mass2)
    
    engine = ReboundEngine()
    engine.load_scenario({
        "name": f"Binary e={eccentricity}",
        "description": f"Binary stars M1={mass1} M2={mass2} e={eccentricity}",
        "units": "solar",
        "integrator": "ias15",
        "t_per_frame": 0.002,
        "scale": 120.0,
        "bodies": [
            {"name": "Star A", "mass": mass1,
             "x":  separation/2, "y": 0, "vx": 0, "vy": v1,
             "color": "#fff200", "radius": 14, "type": "star"},
            {"name": "Star B", "mass": mass2,
             "x": -separation/2, "y": 0, "vx": 0, "vy": v2,
             "color": "#44aaff", "radius": 14, "type": "star"},
        ]
    })
    return engine

def hohmann_transfer(from_body="Earth", to_body="Mars"):
    """Earth-to-Mars (or any two planets) Hohmann transfer with spacecraft."""
    PLANETS = {
        "Mercury": {"a": 0.387, "color": "#b5b5b5"},
        "Venus":   {"a": 0.723, "color": "#e8cda0"},
        "Earth":   {"a": 1.000, "color": "#4fffb0"},
        "Mars":    {"a": 1.524, "color": "#ff6b35"},
        "Jupiter": {"a": 5.203, "color": "#c88b3a"},
        "Saturn":  {"a": 9.537, "color": "#e4d191"},
    }
    p1 = PLANETS[from_body]
    p2 = PLANETS[to_body]
    r1, r2 = p1["a"], p2["a"]

    G_sun = 4 * math.pi**2  # AU^3 yr^-2 Msun^-1

    # Circular orbital velocities
    v1_circ = math.sqrt(G_sun / r1)
    v2_circ = math.sqrt(G_sun / r2)

    # Transfer orbit semi-major axis
    a_t = (r1 + r2) / 2.0

    # Velocities on transfer ellipse
    v_t1 = math.sqrt(G_sun * (2/r1 - 1/a_t))
    v_t2 = math.sqrt(G_sun * (2/r2 - 1/a_t))

    dv1 = v_t1 - v1_circ
    dv2 = v2_circ - v_t2

    # Transfer time
    T_transfer = math.pi * math.sqrt(a_t**3 / G_sun)

    engine = ReboundEngine()
    engine.load_scenario({
        "name": f"Hohmann: {from_body} → {to_body}",
        "description": f"Δv₁={dv1:.4f} AU/yr  Δv₂={dv2:.4f} AU/yr  T={T_transfer:.3f} yr",
        "units": "solar",
        "integrator": "ias15",
        "t_per_frame": 0.003,
        "scale": 150.0 if r2 < 3 else 80.0,
        "bodies": [
            # Sun
            {"name": "Sun", "mass": 1.0,
             "x": 0, "y": 0, "vx": 0, "vy": 0,
             "color": "#fff200", "radius": 20, "type": "star"},
            # Departure planet
            {"name": from_body, "mass": 3e-6,
             "x": r1, "y": 0, "vx": 0, "vy": v1_circ,
             "color": p1["color"], "radius": 7, "type": "planet"},
            # Arrival planet (positioned ~180° ahead for rendezvous)
            {"name": to_body, "mass": 3.2e-7,
             "x": -r2, "y": 0, "vx": 0, "vy": -v2_circ,
             "color": p2["color"], "radius": 5, "type": "planet"},
            # Spacecraft — given transfer orbit injection velocity
            {"name": "Spacecraft", "mass": 1e-15,
             "x": r1, "y": 0, "vx": 0, "vy": v_t1,
             "color": "#ffffff", "radius": 3, "type": "debris"},
        ]
    })

    print(f"\nHohmann Transfer {from_body} → {to_body}:")
    print(f"  Δv₁ = {dv1:.4f} AU/yr ({dv1*4740:.0f} m/s)")
    print(f"  Δv₂ = {dv2:.4f} AU/yr ({dv2*4740:.0f} m/s)")
    print(f"  Transfer time = {T_transfer:.3f} yr ({T_transfer*365.25:.0f} days)")

    return engine


# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing ReboundEngine...")

    # Test 1: Solar system from Horizons
    print("\n[1] Real solar system (NASA Horizons)...")
    try:
        eng = solar_system_real()
        frame = eng.get_frame()
        print(f"    Bodies: {frame['N']}")
        for b in frame['bodies']:
            print(f"    {b['name']:10s} x={b['x']:8.4f} AU  y={b['y']:8.4f} AU  v={b['speed']:.4f} AU/yr")
        frame2 = eng.step(100)
        print(f"    After 100 frames: t={frame2['t']:.4f} yr  ΔE/E={frame2['energy_drift']:.2e}")
        print("    ✓ Solar system OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Test 2: Figure-8
    print("\n[2] Figure-8 choreography...")
    try:
        eng8 = three_body_figure8()
        f = eng8.step(200)
        print(f"    t={f['t']:.4f}  ΔE/E={f['energy_drift']:.2e}")
        print("    ✓ Figure-8 OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Test 3: Hohmann transfer
    print("\n[3] Hohmann transfer Earth → Mars...")
    try:
        eng_h = hohmann_transfer("Earth", "Mars")
        f = eng_h.step(50)
        print(f"    t={f['t']:.4f} yr  {f['N']} bodies")
        print("    ✓ Hohmann OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    # Test 4: Binary star
    print("\n[4] Binary star system e=0.5...")
    try:
        eng_b = binary_star_system(mass1=1.0, mass2=0.8, separation=3.0, eccentricity=0.5)
        f = eng_b.step(100)
        print(f"    t={f['t']:.4f} yr  ΔE/E={f['energy_drift']:.2e}")
        print("    ✓ Binary OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    # Test 5: Error handling
    print("\n[5] Testing error handling...")
    try:
        eng_empty = ReboundEngine()
        frame = eng_empty.get_frame()
        print(f"    Empty engine returns: {frame['N']} bodies")
        print("    ✓ Error handling OK")
    except Exception as e:
        print(f"    ✗ Error: {e}")

    print("\n" + "=" * 50)
    print("All tests complete!")
