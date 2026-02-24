"""
STEP 3 — AI Scenario Generator
User types ANYTHING → Ollama parses it → returns a valid REBOUND scenario dict.
This is what makes the simulation unlimited.
"""

import requests
import json
import math

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1"

# ── SYSTEM PROMPT ─────────────────────────────────────────────
# This is the core prompt that makes "simulate anything" work.
# It teaches the LLM exactly what REBOUND needs.

SCENARIO_SYSTEM_PROMPT = """You are a physics simulation expert. Convert any user request into a REBOUND N-body simulation.

Return ONLY valid JSON. No explanation. No markdown. Just the JSON object.

JSON FORMAT:
{
  "name": "Short name",
  "description": "One line description",
  "units": "solar",
  "integrator": "ias15",
  "t_per_frame": 0.005,
  "scale": 180,
  "bodies": [
    {
      "name": "Body name",
      "mass": 1.0,
      "x": 0.0,
      "y": 0.0,
      "vx": 0.0,
      "vy": 0.0,
      "color": "#fff200",
      "radius": 15,
      "type": "star"
    }
  ]
}

UNITS: always use "solar" (AU, years, solar masses). G=4π²≈39.48 in these units.

INTEGRATOR RULES:
- "ias15" for: three-body chaos, close encounters, unknown systems (safest)
- "whfast" for: stable planetary systems, long runs, solar system
- "mercurius" for: systems with occasional close flybys

T_PER_FRAME: simulation time per rendered frame
- 0.001-0.003 for fast inner orbits (Mercury, hot Jupiters)
- 0.003-0.008 for Earth-like orbits
- 0.01-0.05 for outer planets / binary stars
- 0.1-1.0 for galactic-scale / very slow systems

SCALE: AU → canvas pixels
- Inner solar system (< 2 AU): scale=180
- Full solar system (< 10 AU): scale=50
- Binary stars (1-5 AU apart): scale=100
- Close exoplanet systems (< 0.5 AU): scale=400
- Wide binaries / galactic: scale=20

MASS REFERENCE (solar masses):
- Sun: 1.0
- Jupiter: 0.001 (9.5e-4)
- Earth: 3e-6
- Moon: 3.7e-8
- Spacecraft: 1e-15 (massless)
- Neutron star: 1.4
- Black hole: 5-50
- White dwarf: 0.6
- Red dwarf: 0.1-0.5
- Massive star: 10-100

VELOCITY FORMULA for circular orbit:
  v_circ = 2π * sqrt(1/a)    [AU/yr around 1 Msun star]
  Example: a=1 AU → v=6.28 AU/yr
  Example: a=0.1 AU → v=19.86 AU/yr
  Example: a=5 AU → v=2.81 AU/yr

CIRCULAR ORBIT SETUP (body orbiting at radius r from central mass M):
  vy = 2π * sqrt(M/r)   [body at (r, 0) moving in +y direction]

ALWAYS place the primary body (star/BH) at (0,0) or use move_to_com offset.
For MULTIPLE stars (binary/trinary): place at ±separation/2, give equal/opposite velocities.

BODY TYPES: "star", "planet", "debris", "blackhole", "neutron", "dwarf", "giant", "moon", "comet", "spacecraft"

COLOR GUIDE:
- Yellow star: "#fff200"   Blue star: "#aaddff"   Red star: "#ff4444"
- Orange giant: "#ff8844"  White dwarf: "#eeeeff"  Neutron star: "#aaffff"
- Black hole: "#220022"    Earth-like: "#4fffb0"   Mars-like: "#ff6b35"
- Gas giant: "#c88b3a"     Ice giant: "#7de8e8"    Comet: "#aaddff"
- Spacecraft: "#ffffff"

EXAMPLE SCENARIOS:

User: "hot jupiter system"
{
  "name": "Hot Jupiter System",
  "description": "Gas giant in 3-day orbit, rocky super-Earth further out",
  "units": "solar", "integrator": "ias15", "t_per_frame": 0.001, "scale": 500,
  "bodies": [
    {"name": "Host Star", "mass": 1.1, "x": 0, "y": 0, "vx": 0, "vy": 0, "color": "#ffcc88", "radius": 18, "type": "star"},
    {"name": "Hot Jupiter", "mass": 0.001, "x": 0.05, "y": 0, "vx": 0, "vy": 28.06, "color": "#ff9933", "radius": 11, "type": "planet"},
    {"name": "Super Earth", "mass": 1e-5, "x": 0.5, "y": 0, "vx": 0, "vy": 8.89, "color": "#44aaff", "radius": 6, "type": "planet"}
  ]
}

User: "black hole with stars orbiting it"
{
  "name": "Black Hole Stellar Cluster",
  "description": "Stellar mass black hole with 4 orbiting stars",
  "units": "solar", "integrator": "ias15", "t_per_frame": 0.002, "scale": 120, "softening": 0.01,
  "bodies": [
    {"name": "Black Hole", "mass": 20.0, "x": 0, "y": 0, "vx": 0, "vy": 0, "color": "#110011", "radius": 16, "type": "blackhole"},
    {"name": "Star A", "mass": 1.0, "x": 2.0, "y": 0, "vx": 0, "vy": 14.05, "color": "#fff200", "radius": 8, "type": "star"},
    {"name": "Star B", "mass": 0.8, "x": -3.0, "y": 0, "vx": 0, "vy": -11.47, "color": "#aaddff", "radius": 7, "type": "star"},
    {"name": "Star C", "mass": 1.2, "x": 0, "y": 4.0, "vx": -9.93, "vy": 0, "color": "#ff8844", "radius": 9, "type": "star"},
    {"name": "Star D", "mass": 0.6, "x": 0, "y": -1.5, "vx": 16.22, "vy": 0, "color": "#ffaaaa", "radius": 6, "type": "star"}
  ]
}

User: "simulate the TRAPPIST-1 system"
{
  "name": "TRAPPIST-1",
  "description": "7 Earth-sized planets in tight resonance chain around red dwarf",
  "units": "solar", "integrator": "whfast", "t_per_frame": 0.0003, "scale": 2000,
  "dt": 0.00002,
  "bodies": [
    {"name": "TRAPPIST-1", "mass": 0.089, "x": 0, "y": 0, "vx": 0, "vy": 0, "color": "#ff4400", "radius": 14, "type": "star"},
    {"name": "b", "mass": 2.5e-6, "x": 0.01154, "y": 0, "vx": 0, "vy": 17.68, "color": "#4fffb0", "radius": 4, "type": "planet"},
    {"name": "c", "mass": 2.3e-6, "x": 0.01580, "y": 0, "vx": 0, "vy": 15.10, "color": "#44aaff", "radius": 4, "type": "planet"},
    {"name": "d", "mass": 8.3e-7, "x": 0.02227, "y": 0, "vx": 0, "vy": 12.71, "color": "#ff9955", "radius": 3, "type": "planet"},
    {"name": "e", "mass": 1.9e-6, "x": 0.02925, "y": 0, "vx": 0, "vy": 11.09, "color": "#bf7fff", "radius": 4, "type": "planet"},
    {"name": "f", "mass": 2.5e-6, "x": 0.03849, "y": 0, "vx": 0, "vy": 9.67, "color": "#ffcc44", "radius": 4, "type": "planet"},
    {"name": "g", "mass": 4.8e-6, "x": 0.04683, "y": 0, "vx": 0, "vy": 8.77, "color": "#ff6688", "radius": 5, "type": "planet"},
    {"name": "h", "mass": 6.3e-7, "x": 0.06189, "y": 0, "vx": 0, "vy": 7.63, "color": "#aaffcc", "radius": 3, "type": "planet"}
  ]
}
"""

def generate_scenario_from_text(user_input: str) -> dict:
    """
    Send user text to Ollama → get back a REBOUND scenario dict.
    This is the magic function that makes any simulation possible.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": f"User wants to simulate: {user_input}\n\nGenerate the JSON:",
                "system": SCENARIO_SYSTEM_PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2000,
                }
            },
            timeout=120
        )
        raw = response.json().get("response", "").strip()

        # Strip markdown if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        # Find JSON object
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        scenario = json.loads(raw[start:end])

        # Validate minimum requirements
        if "bodies" not in scenario or len(scenario["bodies"]) == 0:
            raise ValueError("No bodies in scenario")

        # Set defaults for missing fields
        scenario.setdefault("units",       "solar")
        scenario.setdefault("integrator",  "ias15")
        scenario.setdefault("t_per_frame", 0.005)
        scenario.setdefault("scale",       180.0)

        return {"ok": True, "scenario": scenario}

    except Exception as e:
        return {"ok": False, "error": str(e), "raw": raw if 'raw' in dir() else ""}


def validate_scenario(scenario: dict) -> tuple[bool, str]:
    """
    Sanity check a scenario before sending to REBOUND.
    Returns (is_valid, error_message)
    """
    bodies = scenario.get("bodies", [])
    if len(bodies) < 2:
        return False, "Need at least 2 bodies"

    for i, b in enumerate(bodies):
        if b.get("mass", 0) <= 0:
            return False, f"Body {i} has non-positive mass: {b.get('mass')}"
        for field in ("x", "y", "vx", "vy"):
            if not isinstance(b.get(field, 0), (int, float)):
                return False, f"Body {i} has invalid {field}"
        if abs(b.get("x", 0)) > 1e6 or abs(b.get("y", 0)) > 1e6:
            return False, f"Body {i} has extreme position — check units"

    return True, "OK"


# ── BUILT-IN KNOWN SCENARIOS ──────────────────────────────────
# For common requests, skip the LLM and return exact, well-tuned parameters.
# The LLM handles everything else.

KNOWN_SCENARIOS = {
    "solar system": {
        "name": "Solar System",
        "description": "Real solar system — Sun + 8 planets from NASA Horizons",
        "use_horizons": ["Sun","Mercury","Venus","Earth","Mars","Jupiter","Saturn","Uranus","Neptune"],
        "integrator": "whfast",
        "t_per_frame": 0.005,
        "scale": 45.0,
    },
    "inner planets": {
        "name": "Inner Planets",
        "description": "Sun + Mercury Venus Earth Mars",
        "use_horizons": ["Sun","Mercury","Venus","Earth","Mars"],
        "integrator": "whfast",
        "t_per_frame": 0.003,
        "scale": 180.0,
    },
    "earth moon": {
        "name": "Earth-Moon System",
        "description": "Earth and Moon — real orbital data",
        "units": "solar", "integrator": "ias15", "t_per_frame": 0.0001, "scale": 3000,
        "bodies": [
            {"name": "Earth", "mass": 3.003e-6,  "x": 0,        "y": 0,   "vx": 0, "vy": 0, "color": "#4fffb0", "radius": 14, "type": "planet"},
            {"name": "Moon",  "mass": 3.694e-8,  "x": 0.00257,  "y": 0,   "vx": 0, "vy": 6.396, "color": "#cccccc", "radius": 7,  "type": "moon"},
        ]
    },
    "figure-8": {
        "name": "Figure-8 Choreography",
        "description": "Chenciner & Montgomery (2000) exact solution",
        "units": "solar", "integrator": "ias15", "t_per_frame": 0.004, "scale": 220,
        "bodies": [
            {"name": "Body A", "mass": 1.0, "x":  0.9700436, "y": -0.2430870, "vx":  0.2330018, "vy":  0.2161829, "color": "#ff6b35", "radius": 9, "type": "star"},
            {"name": "Body B", "mass": 1.0, "x": -0.9700436, "y":  0.2430870, "vx":  0.2330018, "vy":  0.2161829, "color": "#4fffb0", "radius": 9, "type": "star"},
            {"name": "Body C", "mass": 1.0, "x":  0.0,       "y":  0.0,       "vx": -0.4660035, "vy": -0.4323658, "color": "#bf7fff", "radius": 9, "type": "star"},
        ]
    },
}

def get_scenario(request: str) -> dict:
    """
    Main entry point. Returns a scenario dict for any request.
    1. Checks known scenarios first (exact, fast)
    2. Falls back to AI generation (flexible, unlimited)
    """
    req_lower = request.lower().strip()

    # Check known scenarios
    for key, val in KNOWN_SCENARIOS.items():
        if key in req_lower:
            return {"ok": True, "scenario": val, "source": "builtin"}

    # AI generation
    result = generate_scenario_from_text(request)
    if result["ok"]:
        result["source"] = "ai"
    return result


# ── TEST ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing AI scenario generator...")
    print("(Requires Ollama running with llama3.1)\n")

    test_prompts = [
        "two neutron stars spiraling together",
        "TRAPPIST-1 system",
        "a rogue star flying through a planetary system",
        "Jupiter with its 4 Galilean moons",
        "two black holes orbiting each other",
        "a comet on a highly eccentric orbit around the sun",
        "protoplanetary disk with 20 planetesimals",
        "alpha centauri triple star system",
    ]

    for prompt in test_prompts:
        print(f"Prompt: '{prompt}'")
        result = get_scenario(prompt)
        if result["ok"]:
            sc = result["scenario"]
            n = len(sc.get("bodies", []))
            src = result.get("source", "?")
            print(f"  ✓ [{src}] '{sc['name']}' — {n} bodies")
            print(f"    integrator={sc.get('integrator')}  scale={sc.get('scale')}  t_per_frame={sc.get('t_per_frame')}")
        else:
            print(f"  ✗ Error: {result['error']}")
        print()

    print("Step 3 complete — run step4_websocket_server.py next")
