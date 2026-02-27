"""
Orbital Physics Helper Functions
Ensures correct orbital velocities to prevent bodies from falling or escaping
"""

import math

# Physical constants in solar units (AU, yr, Msun)
G_SOLAR = 4 * math.pi**2  # AU^3 yr^-2 Msun^-1

def circular_orbit_velocity(mass_central, radius):
    """
    Calculate circular orbital velocity for a body orbiting at given radius.
    
    Args:
        mass_central: Mass of central body (solar masses)
        radius: Orbital radius (AU)
    
    Returns:
        Orbital velocity (AU/yr)
    
    Formula: v = sqrt(GM/r)
    """
    return math.sqrt(G_SOLAR * mass_central / radius)


def orbital_period(mass_central, radius):
    """
    Calculate orbital period for circular orbit.
    
    Args:
        mass_central: Mass of central body (solar masses)
        radius: Orbital radius (AU)
    
    Returns:
        Period in years
    
    Formula: T = 2π * sqrt(r³/GM)
    """
    return 2 * math.pi * math.sqrt(radius**3 / (G_SOLAR * mass_central))


def velocity_from_period(radius, period_years):
    """
    Calculate velocity from known orbital period.
    
    Args:
        radius: Orbital radius (AU)
        period_years: Orbital period (years)
    
    Returns:
        Orbital velocity (AU/yr)
    """
    return 2 * math.pi * radius / period_years


def binary_velocities(mass1, mass2, separation, eccentricity=0.0):
    """
    Calculate velocities for two bodies in binary orbit.
    
    Args:
        mass1: Mass of first body (solar masses)
        mass2: Mass of second body (solar masses)
        separation: Distance between bodies (AU)
        eccentricity: Orbital eccentricity (0 = circular)
    
    Returns:
        (v1, v2): Velocities for body 1 and body 2 (AU/yr)
    """
    mu = G_SOLAR * (mass1 + mass2)
    
    # For circular orbit
    if eccentricity == 0:
        r = separation
    else:
        # At periastron
        r = separation * (1 - eccentricity)
    
    # Total velocity
    v_total = math.sqrt(mu * (2/r - 1/separation))
    
    # Velocities proportional to mass ratio (momentum conservation)
    v1 =  v_total * mass2 / (mass1 + mass2)
    v2 = -v_total * mass1 / (mass1 + mass2)
    
    return v1, v2


def escape_velocity(mass_central, radius):
    """
    Calculate escape velocity at given radius.
    
    Args:
        mass_central: Mass of central body (solar masses)
        radius: Distance from central body (AU)
    
    Returns:
        Escape velocity (AU/yr)
    
    Formula: v_esc = sqrt(2GM/r)
    """
    return math.sqrt(2 * G_SOLAR * mass_central / radius)


def check_orbit_stability(mass_central, radius, velocity):
    """
    Check if an orbit is stable (circular, elliptical, parabolic, or hyperbolic).
    
    Args:
        mass_central: Mass of central body (solar masses)
        radius: Distance from central body (AU)
        velocity: Orbital velocity (AU/yr)
    
    Returns:
        dict with orbit type and parameters
    """
    v_circ = circular_orbit_velocity(mass_central, radius)
    v_esc = escape_velocity(mass_central, radius)
    
    # Specific orbital energy
    energy = 0.5 * velocity**2 - G_SOLAR * mass_central / radius
    
    if velocity < v_circ * 0.5:
        orbit_type = "WILL CRASH (too slow)"
    elif abs(velocity - v_circ) < v_circ * 0.05:
        orbit_type = "circular"
    elif velocity < v_esc:
        orbit_type = "elliptical"
    elif abs(velocity - v_esc) < v_esc * 0.01:
        orbit_type = "parabolic (barely bound)"
    else:
        orbit_type = "hyperbolic (unbound)"
    
    return {
        "type": orbit_type,
        "velocity": velocity,
        "v_circular": v_circ,
        "v_escape": v_esc,
        "ratio_to_circular": velocity / v_circ,
        "energy": energy,
        "is_stable": velocity >= v_circ * 0.5 and velocity < v_esc * 1.5
    }


# ── COMMON SYSTEMS ────────────────────────────────────────────

def earth_moon_system():
    """
    Returns correct Earth-Moon orbital parameters.
    
    Real values:
    - Moon orbital radius: 384,400 km = 0.00257 AU
    - Moon orbital period: 27.32 days = 0.0748 years
    - Moon mass: 7.342e22 kg = 3.694e-8 Msun
    - Earth mass: 5.972e24 kg = 3.003e-6 Msun
    """
    M_earth = 3.003e-6  # Msun
    M_moon = 3.694e-8   # Msun
    r_moon = 0.00257    # AU
    
    # Calculate correct velocity
    v_moon = circular_orbit_velocity(M_earth, r_moon)
    period_days = orbital_period(M_earth, r_moon) * 365.25
    
    return {
        "name": "Earth-Moon System",
        "description": f"Earth and Moon (T={period_days:.1f} days)",
        "units": "solar",
        "integrator": "ias15",
        "t_per_frame": 0.0001,  # ~0.037 days per frame
        "scale": 3000,
        "bodies": [
            {
                "name": "Earth",
                "mass": M_earth,
                "x": 0,
                "y": 0,
                "vx": 0,
                "vy": 0,
                "color": "#4fffb0",
                "radius": 14,
                "type": "planet"
            },
            {
                "name": "Moon",
                "mass": M_moon,
                "x": r_moon,
                "y": 0,
                "vx": 0,
                "vy": v_moon,
                "color": "#cccccc",
                "radius": 7,
                "type": "moon"
            }
        ],
        "_physics_notes": {
            "moon_velocity": f"{v_moon:.4f} AU/yr",
            "orbital_period": f"{period_days:.2f} days",
            "distance_km": 384400,
        }
    }


def sun_earth_moon_system():
    """
    Sun-Earth-Moon system with correct three-body dynamics.
    Note: This is actually quite complex due to Sun's influence on Moon!
    """
    M_sun = 1.0
    M_earth = 3.003e-6
    M_moon = 3.694e-8
    
    r_earth = 1.0  # AU (Earth's orbit)
    r_moon = 0.00257  # AU relative to Earth
    
    # Earth's velocity around Sun
    v_earth = circular_orbit_velocity(M_sun, r_earth)
    
    # Moon's velocity relative to Earth
    v_moon_rel = circular_orbit_velocity(M_earth, r_moon)
    
    # Moon's total velocity = Earth's velocity + Moon's velocity relative to Earth
    v_moon_total = v_earth + v_moon_rel
    
    return {
        "name": "Sun-Earth-Moon",
        "description": "Three-body system with actual Moon orbit",
        "units": "solar",
        "integrator": "ias15",
        "t_per_frame": 0.002,
        "scale": 300,
        "bodies": [
            {
                "name": "Sun",
                "mass": M_sun,
                "x": 0,
                "y": 0,
                "vx": 0,
                "vy": 0,
                "color": "#fff200",
                "radius": 20,
                "type": "star"
            },
            {
                "name": "Earth",
                "mass": M_earth,
                "x": r_earth,
                "y": 0,
                "vx": 0,
                "vy": v_earth,
                "color": "#4fffb0",
                "radius": 8,
                "type": "planet"
            },
            {
                "name": "Moon",
                "mass": M_moon,
                "x": r_earth + r_moon,  # Position Moon relative to Earth
                "y": 0,
                "vx": 0,
                "vy": v_moon_total,  # Total velocity in Sun's frame
                "color": "#cccccc",
                "radius": 4,
                "type": "moon"
            }
        ]
    }


# ── TESTING ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("ORBITAL PHYSICS HELPER - TESTS")
    print("=" * 60)
    
    # Test 1: Earth orbit around Sun
    print("\n[Test 1] Earth's orbit around Sun")
    M_sun = 1.0
    r_earth = 1.0
    v_earth = circular_orbit_velocity(M_sun, r_earth)
    T_earth = orbital_period(M_sun, r_earth)
    print(f"  Radius:   {r_earth} AU")
    print(f"  Velocity: {v_earth:.4f} AU/yr")
    print(f"  Period:   {T_earth:.4f} years = {T_earth*365.25:.1f} days")
    print(f"  Expected: ~365 days ✓" if abs(T_earth - 1.0) < 0.01 else "  ERROR!")
    
    # Test 2: Moon's orbit around Earth
    print("\n[Test 2] Moon's orbit around Earth")
    M_earth = 3.003e-6
    r_moon = 0.00257
    v_moon = circular_orbit_velocity(M_earth, r_moon)
    T_moon = orbital_period(M_earth, r_moon)
    T_moon_days = T_moon * 365.25
    print(f"  Radius:   {r_moon} AU ({r_moon*149597871:.0f} km)")
    print(f"  Velocity: {v_moon:.4f} AU/yr")
    print(f"  Period:   {T_moon_days:.2f} days")
    print(f"  Expected: ~27.3 days ✓" if abs(T_moon_days - 27.3) < 1 else "  ERROR!")
    
    # Test 3: Check the WRONG velocity from the file
    print("\n[Test 3] Check original (WRONG) Moon velocity")
    v_wrong = 6.396
    check = check_orbit_stability(M_earth, r_moon, v_wrong)
    print(f"  Original velocity: {v_wrong} AU/yr")
    print(f"  Orbit type:        {check['type']}")
    print(f"  Ratio to circular: {check['ratio_to_circular']:.1f}x")
    print(f"  Escape velocity:   {check['v_escape']:.4f} AU/yr")
    print(f"  Is stable:         {check['is_stable']}")
    
    # Test 4: Check the CORRECT velocity
    print("\n[Test 4] Check correct Moon velocity")
    check = check_orbit_stability(M_earth, r_moon, v_moon)
    print(f"  Correct velocity:  {v_moon:.4f} AU/yr")
    print(f"  Orbit type:        {check['type']}")
    print(f"  Ratio to circular: {check['ratio_to_circular']:.2f}x")
    print(f"  Is stable:         {check['is_stable']}")
    
    # Test 5: Binary star system
    print("\n[Test 5] Binary star system (1 + 0.8 Msun, 3 AU apart)")
    v1, v2 = binary_velocities(1.0, 0.8, 3.0, eccentricity=0.0)
    print(f"  Star 1 velocity: {v1:.4f} AU/yr")
    print(f"  Star 2 velocity: {v2:.4f} AU/yr")
    print(f"  Momentum check:  {abs(1.0*v1 + 0.8*v2) < 0.0001} (should be ~0)")
    
    # Test 6: Generate Earth-Moon system
    print("\n[Test 6] Generate Earth-Moon system")
    em_system = earth_moon_system()
    moon = em_system["bodies"][1]
    print(f"  Moon velocity in scenario: {moon['vy']:.4f} AU/yr")
    print(f"  Period: {em_system['_physics_notes']['orbital_period']}")
    print(f"  ✓ Correct!" if abs(moon['vy'] - v_moon) < 0.001 else "  ERROR!")
    
    print("\n" + "=" * 60)
    print("All tests complete!")
    print("=" * 60)
