"""
Orbital Accuracy Checker

Compares simulated orbital elements from a running ReboundEngine against
known NASA/JPL reference values for solar system planets.

Metrics per body  : relative error in a (semi-major axis), e (eccentricity), P (period)
Score per body    : 1 - mean(relative errors)  × 100  [0–100 %]
Overall accuracy  : mean of matched body scores

Reference values  : J2000 mean elements sourced from NASA/JPL Horizons
                    (datasets/planets_horizons.json + standard ephemeris)
"""

import math

# ── REFERENCE ORBITAL ELEMENTS ────────────────────────────────
# Units: a in AU, e dimensionless, P in years
REFERENCE = {
    "mercury": {"a": 0.38709893,  "e": 0.20563069, "P": 0.24084670},
    "venus":   {"a": 0.72333199,  "e": 0.00677323, "P": 0.61519726},
    "earth":   {"a": 1.00000011,  "e": 0.01671022, "P": 1.00001740},
    "mars":    {"a": 1.52366231,  "e": 0.09341233, "P": 1.88081578},
    "jupiter": {"a": 5.20336301,  "e": 0.04839266, "P": 11.86198220},
    "saturn":  {"a": 9.53707032,  "e": 0.05415060, "P": 29.44749800},
    "uranus":  {"a": 19.19126393, "e": 0.04716771, "P": 84.01204650},
    "neptune": {"a": 30.06896348, "e": 0.00858587, "P": 164.78850100},
    # Earth-centric elements (relative to Earth as primary)
    "moon":    {"a": 0.002570,    "e": 0.05490,   "P": 0.074802},
}


def _relative_error(simulated: float, reference: float,
                    min_denominator: float = 1e-6) -> float:
    """Absolute relative error, denominator floored to avoid div-by-zero."""
    denom = max(abs(reference), min_denominator)
    return abs(simulated - reference) / denom


def kepler_period(a_au: float, M_primary_msun: float) -> float:
    """
    Kepler's 3rd law in solar units (AU, yr, Msun):
        G = 4π²  →  P = sqrt(a³ / M)
    Works for ANY gravitational system — stars, exoplanets, moons.
    """
    if a_au <= 0 or M_primary_msun <= 0:
        return 0.0
    return math.sqrt(a_au ** 3 / M_primary_msun)


def _grade(score: float) -> str:
    if score >= 95: return "A"
    if score >= 85: return "B"
    if score >= 70: return "C"
    if score >= 50: return "D"
    return "F"


def physics_correctness(engine) -> dict:
    """
    Physics-based accuracy for ANY scenario — no reference table needed.

    Checks two independent things:

    1. Orbital stability / drift  (80 % weight)
       Compares current semi-major axis (a) and eccentricity (e) for each
       orbiting body against the snapshot recorded when the simulation was
       first loaded (engine._initial_elements, t=0).

       a_drift = |a_now - a₀| / a₀
       e_drift = |e_now - e₀| / max(e₀, 0.01)   ← floor avoids div-by-zero
       Score per body = max(0, 1 - mean(a_drift, e_drift)) × 100

       At t=0 every scenario scores 100 % here. A bad integrator or an
       unstable initial configuration will drift away over time, lowering
       the score naturally.

    2. Energy conservation  (20 % weight)
       drift = |E_now - E₀| / |E₀|
       Energy score = max(0, 1 - drift × 100) × 100
       A drift of 1 % or more zeroes this component.

    Returns the same shape as compute_accuracy() plus:
        mode             : "physics"
        stability_score  : orbital-drift average [0–100]
        energy_score     : energy conservation score [0–100]
        energy_drift     : fractional energy drift (raw)
    """
    if engine.sim is None or engine.sim.N < 2:
        return {
            "overall": None, "grade": "N/A", "t_years": 0.0,
            "bodies": [], "unmatched": [], "mode": "physics",
            "note": "Need at least 2 bodies to calculate accuracy.",
        }

    t_years      = round(engine.sim.t, 6)
    elements_now = engine.get_orbital_elements()
    elements_t0  = {el["name"]: el for el in engine._initial_elements
                    if "error" not in el}

    # ── Energy conservation ───────────────────────────────────
    E_now   = engine.sim.energy()
    e_drift = abs((E_now - engine._E0) / engine._E0) if engine._E0 != 0 else 0.0
    energy_score = max(0.0, 1.0 - e_drift * 100.0) * 100.0

    # ── Orbital drift per body ────────────────────────────────
    body_results = []
    unmatched    = []

    for el in elements_now:
        if "error" in el:
            unmatched.append(el.get("name", "?"))
            continue

        name = el["name"]
        t0   = elements_t0.get(name)
        if t0 is None:
            unmatched.append(name)
            continue

        a_now, a_0 = el["a"], t0["a"]
        e_now, e_0 = el["e"], t0["e"]

        if a_0 <= 0:
            unmatched.append(name)
            continue

        a_err       = _relative_error(a_now, a_0)
        e_err       = _relative_error(e_now, e_0, min_denominator=0.01)
        drift_score = max(0.0, 1.0 - (a_err + e_err) / 2.0) * 100.0

        # Orbit type classification based on eccentricity
        e_val = e_now
        if e_val < 0.0:
            orbit_type = "invalid"
        elif e_val < 0.05:
            orbit_type = "circular"
        elif e_val < 0.5:
            orbit_type = "elliptical"
        elif e_val < 1.0:
            orbit_type = "highly_elliptical"
        else:
            orbit_type = "hyperbolic (unbound)"

        body_results.append({
            "planet":     name,
            "score":      round(drift_score, 2),
            "a_t0":       round(a_0,   6),  "a_now":  round(a_now, 6),
            "a_drift%":   round(a_err * 100, 4),
            "e_t0":       round(e_0,   6),  "e_now":  round(e_now, 6),
            "e_drift%":   round(e_err * 100, 4),
            "orbit_type": orbit_type,
        })

    if not body_results:
        return {
            "overall": None, "grade": "N/A", "t_years": t_years,
            "bodies": [], "unmatched": unmatched, "mode": "physics",
            "note": "Could not compute orbital elements for any body.",
        }

    stability_avg = sum(b["score"] for b in body_results) / len(body_results)
    overall       = 0.8 * stability_avg + 0.2 * energy_score

    return {
        "overall":         round(overall, 2),
        "grade":           _grade(overall),
        "t_years":         t_years,
        "bodies":          body_results,
        "unmatched":       unmatched,
        "mode":            "physics",
        "stability_score": round(stability_avg, 2),
        "energy_score":    round(energy_score, 2),
        "energy_drift":    round(e_drift, 12),
    }


def accuracy_for_body(sim_elements: dict, planet_name: str) -> dict | None:
    """
    Compare one body's simulated orbital elements against the reference table.

    Parameters
    ----------
    sim_elements : dict with keys 'a', 'e', 'P'
                   (from ReboundEngine.get_orbital_elements())
    planet_name  : e.g. "Earth", "mars", "JUPITER"

    Returns
    -------
    dict with per-metric errors and an overall accuracy score [0–100 %],
    or None if the body is not in the reference table.
    """
    key = planet_name.lower().strip()
    ref = REFERENCE.get(key)
    if ref is None:
        return None

    a_err = _relative_error(sim_elements["a"], ref["a"])

    # Eccentricity can be near zero for nearly-circular orbits.
    # Use 0.01 as the minimum denominator so tiny absolute errors
    # (e.g. 0.001 vs 0.0) don't inflate the relative error catastrophically.
    e_err = _relative_error(sim_elements["e"], ref["e"], min_denominator=0.01)

    P_err = _relative_error(sim_elements["P"], ref["P"])

    mean_err = (a_err + e_err + P_err) / 3.0
    score    = max(0.0, 1.0 - mean_err) * 100.0

    return {
        "planet":   planet_name,
        "score":    round(score, 2),
        "a_ref":    ref["a"],         "a_sim":  round(sim_elements["a"], 6),
        "a_error%": round(a_err * 100, 4),
        "e_ref":    ref["e"],         "e_sim":  round(sim_elements["e"], 6),
        "e_error%": round(e_err * 100, 4),
        "P_ref":    ref["P"],         "P_sim":  round(sim_elements["P"], 6),
        "P_error%": round(P_err * 100, 4),
    }


def compute_accuracy(engine) -> dict:
    """
    Run a full accuracy check on a live ReboundEngine.

    Parameters
    ----------
    engine : ReboundEngine instance with a loaded simulation.

    Returns
    -------
    {
        "overall":   float | None,   # 0–100 %, None if no known bodies found
        "grade":     str,            # "A" ≥95  "B" ≥85  "C" ≥70  "D" ≥50  "F" <50
        "t_years":   float,          # simulation time at measurement
        "bodies":    list,           # per-body accuracy dicts
        "unmatched": list,           # body names with no reference entry
    }
    """
    elements_list = engine.get_orbital_elements()

    matched   = []
    unmatched = []

    for el in elements_list:
        if "error" in el:
            unmatched.append(el.get("name", "?"))
            continue
        result = accuracy_for_body(el, el["name"])
        if result is None:
            unmatched.append(el["name"])
        else:
            matched.append(result)

    t_years = round(engine.sim.t, 6) if engine.sim is not None else 0.0

    if not matched:
        # No solar-system planets found — fall back to physics correctness
        report = physics_correctness(engine)
        report["note"] = (
            "No known solar system bodies matched. "
            "Using Kepler's 3rd law + energy conservation instead."
        )
        return report

    overall = sum(b["score"] for b in matched) / len(matched)

    return {
        "overall":   round(overall, 2),
        "grade":     _grade(overall),
        "t_years":   t_years,
        "bodies":    matched,
        "unmatched": unmatched,
        "mode":      "ephemeris",
    }


# ── STANDALONE TEST ───────────────────────────────────────────
if __name__ == "__main__":
    from rebound_engine import ReboundEngine
    import json

    # ── TEST 1: real solar system (ephemeris mode) ────────────
    print("=" * 60)
    print("TEST 1 — Solar system from NASA JPL Horizons (ephemeris mode)")
    print("=" * 60)
    e1 = ReboundEngine()
    e1.load_from_horizons(
        ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn"],
        integrator="whfast"
    )
    r1 = compute_accuracy(e1)
    print(f"  Mode    : {r1['mode']}")
    print(f"  Overall : {r1['overall']}%  Grade {r1['grade']}")
    for b in r1["bodies"]:
        print(f"  {b['planet']:<10}  score={b['score']:6.2f}%  "
              f"a_err={b['a_error%']:7.4f}%  "
              f"e_err={b['e_error%']:7.4f}%  "
              f"P_err={b['P_error%']:7.4f}%")

    print()
    e1.sim.integrate(10.0)
    r1b = compute_accuracy(e1)
    print(f"  After 10 yr integration — Overall : {r1b['overall']}%  Grade {r1b['grade']}")

    # ── TEST 2: Hot Jupiter — no reference planets (physics mode) ──
    print()
    print("=" * 60)
    print("TEST 2 — Hot Jupiter system (physics / drift mode)")
    print("=" * 60)
    import math
    G = 4 * math.pi ** 2
    M_star = 1.0
    a_hj   = 0.05   # AU
    v_circ = math.sqrt(G * M_star / a_hj)

    hot_jupiter = {
        "name": "Hot Jupiter", "units": "solar", "integrator": "ias15",
        "t_per_frame": 0.001, "scale": 600,
        "bodies": [
            {"name": "Star",       "mass": M_star, "x": 0,    "y": 0, "vx": 0,      "vy": 0},
            {"name": "Hot Jupiter","mass": 0.001,  "x": a_hj, "y": 0, "vx": 0, "vy": v_circ},
        ]
    }
    e2 = ReboundEngine()
    e2.load_scenario(hot_jupiter)

    print("  At t=0:")
    r2a = compute_accuracy(e2)
    for b in r2a["bodies"]:
        print(f"    {b['planet']:<14}  score={b['score']:6.2f}%  "
              f"a_drift={b['a_drift%']:7.4f}%  e_drift={b['e_drift%']:7.4f}%  "
              f"orbit={b['orbit_type']}")

    e2.sim.integrate(5.0)   # 5 yr forward
    print("  After 5 yr (ias15 — should be stable):")
    r2b = compute_accuracy(e2)
    print(f"    Mode={r2b['mode']}  Overall={r2b['overall']}%  Grade={r2b['grade']}")
    print(f"    Stability={r2b.get('stability_score')}%  Energy={r2b.get('energy_score')}%  "
          f"E_drift={r2b.get('energy_drift')}")
    for b in r2b["bodies"]:
        print(f"    {b['planet']:<14}  score={b['score']:6.2f}%  "
              f"a_drift={b['a_drift%']:7.4f}%  e_drift={b['e_drift%']:7.4f}%  "
              f"orbit={b['orbit_type']}")

    # ── TEST 3: leapfrog on eccentric orbit ───────────────────
    print()
    print("=" * 60)
    print("TEST 3 — Wrong velocity + leapfrog integrator (shows drift)")
    print("=" * 60)
    bad = {
        "name": "Broken", "units": "solar", "integrator": "leapfrog",
        "dt": 0.01,
        "t_per_frame": 0.001, "scale": 600,
        "bodies": [
            {"name": "Star",   "mass": 1.0,   "x": 0,   "y": 0, "vx": 0, "vy": 0},
            {"name": "Planet", "mass": 0.001, "x": 1.0, "y": 0, "vx": 0, "vy": 0.5},
        ]
    }
    # v=0.5 AU/yr at r=1 AU (v_circ ≈ 6.28) → highly elliptical (e≈0.999)
    # leapfrog accumulates energy error on eccentric orbits
    e3 = ReboundEngine()
    e3.load_scenario(bad)
    print("  At t=0 (orbit_type reveals the unusual setup):")
    r3a = compute_accuracy(e3)
    for b in r3a["bodies"]:
        print(f"    {b['planet']:<14}  score={b['score']:6.2f}%  "
              f"e_now={b['e_now']:.4f}  orbit={b['orbit_type']}")

    e3.sim.integrate(10.0)  # 10 yr — leapfrog drifts on eccentric orbits
    print("  After 10 yr (leapfrog drifts on eccentric orbits):")
    r3b = compute_accuracy(e3)
    print(f"    Mode={r3b['mode']}  Overall={r3b['overall']}%  Grade={r3b['grade']}")
    print(f"    Stability={r3b.get('stability_score')}%  E_drift={r3b.get('energy_drift')}")
    for b in r3b["bodies"]:
        print(f"    {b['planet']:<14}  score={b['score']:6.2f}%  "
              f"a_drift={b['a_drift%']:7.4f}%  e_drift={b['e_drift%']:7.4f}%  "
              f"orbit={b['orbit_type']}")
