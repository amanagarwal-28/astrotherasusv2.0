import numpy as np
import json

# Real orbital elements for all 8 planets
SOLAR_SYSTEM = {
    "mercury": {"a":0.387,"e":0.2056,"i":7.00, "period":87.97,  "color":"#b5b5b5","mass":0.055},
    "venus":   {"a":0.723,"e":0.0067,"i":3.39, "period":224.70, "color":"#e8cda0","mass":0.815},
    "earth":   {"a":1.000,"e":0.0167,"i":0.00, "period":365.25, "color":"#4fffb0","mass":1.000},
    "mars":    {"a":1.524,"e":0.0934,"i":1.85, "period":686.97, "color":"#ff6b35","mass":0.107},
    "jupiter": {"a":5.203,"e":0.0489,"i":1.30, "period":4332.59,"color":"#c88b3a","mass":317.8},
    "saturn":  {"a":9.537,"e":0.0565,"i":2.49, "period":10759.2,"color":"#e4d191","mass":95.2},
    "uranus":  {"a":19.19,"e":0.0457,"i":0.77, "period":30688.5,"color":"#7de8e8","mass":14.5},
    "neptune": {"a":30.07,"e":0.0113,"i":1.77, "period":60182.0,"color":"#3f54ba","mass":17.1},
}

def solve_kepler(M, e, tol=1e-10):
    """Solve Kepler's equation M = E - e*sin(E) using Newton-Raphson"""
    E = M.copy()
    for _ in range(100):
        dE = (M - E + e * np.sin(E)) / (1 - e * np.cos(E))
        E += dE
        if np.max(np.abs(dE)) < tol:
            break
    return E

def compute_orbit(body_name, duration_days=365, steps=500):
    """
    Compute real Keplerian orbital trajectory
    Returns x, y coordinates in AU plus orbital data
    """
    body = SOLAR_SYSTEM.get(body_name.lower())
    if not body:
        return None

    a = body["a"]
    e = body["e"]
    period = body["period"]

    # Time array
    t = np.linspace(0, duration_days, steps)

    # Mean anomaly
    M = 2 * np.pi * t / period

    # Eccentric anomaly (solve Kepler equation)
    E = solve_kepler(M, e)

    # True anomaly
    nu = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )

    # Distance in AU
    r = a * (1 - e**2) / (1 + e * np.cos(nu))

    # Cartesian coordinates
    x = r * np.cos(nu)
    y = r * np.sin(nu)

    # Orbital speed via vis-viva (AU/day)
    GM = 4 * np.pi**2  # AU^3/yr^2
    v = np.sqrt(GM * (2/r - 1/a)) * (365.25 / (2 * np.pi))

    return {
        "body": body_name,
        "x": x.tolist(),
        "y": y.tolist(),
        "r": r.tolist(),
        "v": v.tolist(),
        "t": t.tolist(),
        "color": body["color"],
        "elements": {
            "semi_major_axis_au": a,
            "eccentricity": e,
            "period_days": round(period, 2),
            "perihelion_au": round(a * (1 - e), 4),
            "aphelion_au": round(a * (1 + e), 4),
            "max_speed_au_day": round(float(np.max(v)), 6),
            "min_speed_au_day": round(float(np.min(v)), 6)
        }
    }

def compute_hohmann(body1="earth", body2="mars"):
    """Compute Hohmann transfer between two planets"""
    b1 = SOLAR_SYSTEM.get(body1)
    b2 = SOLAR_SYSTEM.get(body2)
    if not b1 or not b2:
        return None

    r1 = b1["a"]
    r2 = b2["a"]
    GM = 4 * np.pi**2

    # Circular velocities
    v1 = np.sqrt(GM / r1)
    v2 = np.sqrt(GM / r2)

    # Transfer orbit
    a_t = (r1 + r2) / 2
    v_t1 = np.sqrt(GM * (2/r1 - 1/a_t))
    v_t2 = np.sqrt(GM * (2/r2 - 1/a_t))

    dv1 = abs(v_t1 - v1)
    dv2 = abs(v2 - v_t2)

    # Transfer time in days
    T = np.pi * np.sqrt(a_t**3 / GM) * 365.25

    # Transfer orbit path
    e_t = (r2 - r1) / (r2 + r1)
    nu = np.linspace(0, np.pi, 300)
    r_t = a_t * (1 - e_t**2) / (1 + e_t * np.cos(nu))
    x_t = (r_t * np.cos(nu)).tolist()
    y_t = (r_t * np.sin(nu)).tolist()

    return {
        "from": body1,
        "to": body2,
        "r1_au": r1,
        "r2_au": r2,
        "delta_v1": round(dv1, 4),
        "delta_v2": round(dv2, 4),
        "total_delta_v": round(dv1 + dv2, 4),
        "transfer_days": round(T, 1),
        "transfer_x": x_t,
        "transfer_y": y_t
    }

def compute_multi_orbit(bodies, duration_days=365, steps=500):
    """Compute orbits for multiple bodies at once"""
    results = []
    for body in bodies:
        orbit = compute_orbit(body, duration_days, steps)
        if orbit:
            results.append(orbit)
    return results

# ── TEST ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Mars orbit computation...")
    orbit = compute_orbit("mars", duration_days=687)
    if orbit:
        e = orbit["elements"]
        print(f"Mars semi-major axis: {e['semi_major_axis_au']} AU")
        print(f"Mars period: {e['period_days']} days")
        print(f"Mars eccentricity: {e['eccentricity']}")
        print(f"Perihelion: {e['perihelion_au']} AU")
        print(f"Aphelion: {e['aphelion_au']} AU")
        print(f"Max speed: {e['max_speed_au_day']} AU/day")
        print(f"Data points: {len(orbit['x'])}")

    print("\nTesting Hohmann transfer Earth-Mars...")
    h = compute_hohmann("earth", "mars")
    if h:
        print(f"Transfer time: {h['transfer_days']} days")
        print(f"Delta-v1: {h['delta_v1']} AU/yr")
        print(f"Delta-v2: {h['delta_v2']} AU/yr")
        print(f"Total delta-v: {h['total_delta_v']} AU/yr")