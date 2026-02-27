"""
STEP 4 — WebSocket Simulation Server
FastAPI server that:
  - Accepts any simulation request via POST /api/simulate
  - Streams live REBOUND frames via WebSocket /ws/sim
  - Handles multiple concurrent simulations per client
  - Integrates with existing RAG + chat API
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import json
import sys, os

sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="Astro Thesaurus — REBOUND Server")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── HELPER: live RAG doc count ────────────────────────────────
def get_rag_doc_count() -> int:
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        col = client.get_collection("orbital_dynamics")
        return col.count()
    except Exception:
        return 0

# ── REQUEST MODELS ────────────────────────────────────────────

class SimRequest(BaseModel):
    prompt: str              # "simulate a hot Jupiter system"
    frames_per_second: int = 30
    steps_per_frame: int   = 2   # physics steps between each sent frame

class ChatRequest(BaseModel):
    message: str

# ── WEBSOCKET SIMULATION STREAM ───────────────────────────────

@app.websocket("/ws/sim")
async def websocket_sim(websocket: WebSocket):
    """
    WebSocket endpoint for live simulation streaming.
    
    Protocol:
      CLIENT → SERVER: JSON with action
        {"action": "start", "prompt": "hot jupiter system", "fps": 30}
        {"action": "pause"}
        {"action": "resume"}
        {"action": "reset"}
        {"action": "stop"}
        {"action": "set_speed", "multiplier": 2.0}
    
      SERVER → CLIENT: JSON frames
        {"type": "scenario", "data": {name, description, N, integrator, scale, bodies[]}}
        {"type": "frame",    "data": {t, N, bodies[], energy_drift}}
        {"type": "error",    "message": "..."}
        {"type": "status",   "message": "Generating scenario..."}
    """
    await websocket.accept()
    
    engine = None
    playing = False
    speed_multiplier = 1.0
    fps = 30
    steps_per_frame = 2

    async def send(obj):
        await websocket.send_text(json.dumps(obj))

    try:
        while True:
            # Non-blocking receive with timeout for simulation loop
            try:
                if playing and engine:
                    # Try to receive message without blocking
                    try:
                        raw = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                        msg = json.loads(raw)
                    except asyncio.TimeoutError:
                        msg = None
                else:
                    # Blocking receive when paused
                    raw = await websocket.receive_text()
                    msg = json.loads(raw)
            except WebSocketDisconnect:
                break

            # Handle incoming message
            if msg:
                action = msg.get("action", "")

                if action == "start":
                    prompt = msg.get("prompt", "solar system")
                    fps    = msg.get("fps", 30)
                    steps_per_frame = msg.get("steps_per_frame", 2)
                    
                    await send({"type": "status", "message": f"Generating scenario: {prompt}"})

                    # Generate scenario
                    try:
                        from ai_scenario_generator import get_scenario
                        result = get_scenario(prompt)
                    except ImportError:
                        from ai_scenario_generator import get_scenario
                        result = get_scenario(prompt)

                    if not result["ok"]:
                        await send({"type": "error", "message": result.get("error", "Failed to generate scenario")})
                        continue

                    scenario = result["scenario"]
                    await send({"type": "status", "message": f"Loading simulation: {scenario.get('name', '?')}"})

                    # Initialize REBOUND engine
                    try:
                        import rebound
                        from rebound_engine import ReboundEngine
                    except ImportError:
                        from rebound_engine import ReboundEngine

                    engine = ReboundEngine()

                    # Handle Horizons-based scenarios
                    if "use_horizons" in scenario:
                        initial_frame = engine.load_from_horizons(
                            scenario["use_horizons"],
                            integrator=scenario.get("integrator", "whfast")
                        )
                        engine.t_per_frame = scenario.get("t_per_frame", 0.005)
                        engine.scale       = scenario.get("scale", 180.0)
                    else:
                        initial_frame = engine.load_scenario(scenario)

                    # Apply speed multiplier to t_per_frame
                    engine.t_per_frame *= speed_multiplier

                    # Send scenario metadata
                    await send({
                        "type":  "scenario",
                        "source": result.get("source", "ai"),
                        "data":  {
                            "name":        scenario.get("name", "Simulation"),
                            "description": scenario.get("description", ""),
                            "integrator":  scenario.get("integrator", "ias15"),
                            "N":           engine.sim.N,
                            "scale":       engine.scale,
                            "bodies_meta": engine.body_info,
                        }
                    })

                    # Send first frame
                    await send({"type": "frame", "data": initial_frame})
                    playing = True

                elif action == "pause":
                    playing = False
                    await send({"type": "status", "message": "Paused"})

                elif action == "resume":
                    if engine:
                        playing = True
                        await send({"type": "status", "message": "Resumed"})

                elif action == "reset":
                    if engine:
                        engine.reset()
                        playing = False
                        await send({"type": "frame", "data": engine.get_frame()})
                        await send({"type": "status", "message": "Reset"})

                elif action == "set_speed":
                    mult = float(msg.get("multiplier", 1.0))
                    if engine:
                        # Adjust t_per_frame proportionally
                        engine.t_per_frame = engine.t_per_frame / speed_multiplier * mult
                    speed_multiplier = mult

                elif action == "stop":
                    playing = False
                    engine  = None
                    await send({"type": "status", "message": "Stopped"})

                elif action == "get_elements":
                    if engine:
                        elements = engine.get_orbital_elements()
                        await send({"type": "elements", "data": elements})

            # Simulation loop: send frame if playing
            if playing and engine:
                try:
                    for _ in range(steps_per_frame):
                        frame = engine.step()
                    await send({"type": "frame", "data": frame})
                    # Target fps
                    await asyncio.sleep(1.0 / fps)
                except Exception as e:
                    await send({"type": "error", "message": f"Simulation error: {str(e)}"})
                    playing = False

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await send({"type": "error", "message": str(e)})
        except:
            pass


# ── REST ENDPOINTS ────────────────────────────────────────────

@app.post("/api/simulate")
async def simulate_once(req: SimRequest):
    """
    Non-streaming: generate scenario + compute N frames, return all at once.
    Useful for generating trajectory plots without WebSocket.
    """
    try:
        from ai_scenario_generator import get_scenario
    except ImportError:
        from ai_scenario_generator import get_scenario

    result = get_scenario(req.prompt)
    if not result["ok"]:
        return JSONResponse({"error": result.get("error")}, status_code=400)

    scenario = result["scenario"]

    try:
        import rebound
        from rebound_engine import ReboundEngine
    except ImportError:
        from rebound_engine import ReboundEngine

    engine = ReboundEngine()

    if "use_horizons" in scenario:
        engine.load_from_horizons(scenario["use_horizons"], scenario.get("integrator", "whfast"))
        engine.t_per_frame = scenario.get("t_per_frame", 0.005)
        engine.scale       = scenario.get("scale", 180.0)
    else:
        engine.load_scenario(scenario)

    # Compute frames
    n_frames = req.frames_per_second * 5  # 5 seconds of simulation
    frames = []
    for _ in range(min(n_frames, 300)):  # cap at 300 frames
        frames.append(engine.step(req.steps_per_frame))

    return {
        "scenario": scenario,
        "source":   result.get("source", "ai"),
        "frames":   frames,
        "elements": engine.get_orbital_elements(),
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Existing chat endpoint — unchanged from your original api_server.py"""
    try:
        from query_rag import query_rag_multi, is_orbital_query
        from intent_parser import parse_intent, answer_with_rag
        from physics_engine import compute_orbit, compute_hohmann, compute_multi_orbit, SOLAR_SYSTEM
        from visualizer import plot_orbit, plot_hohmann, plot_multi_orbit

        msg = req.message.strip()

        if not is_orbital_query(msg):
            return {
                "text": "I specialize in orbital mechanics. Ask about planet orbits, transfers, Lagrange points, Kepler's laws, or tell me to simulate anything!",
                "plot": None, "data": None, "intent": None, "sim_prompt": None
            }

        intent     = parse_intent(msg)
        rag_ctx    = query_rag_multi(msg)
        text_ans   = answer_with_rag(msg, rag_ctx) if rag_ctx else "No relevant data found."

        # Detect if user wants a simulation → return sim_prompt for frontend
        sim_keywords = ["simulate", "show", "animate", "visualize", "watch", "run", "model"]
        wants_sim = any(k in msg.lower() for k in sim_keywords)
        sim_prompt = msg if wants_sim else None

        plot_b64 = None
        num_data = None
        body   = (intent.get("body") or "").lower()
        action = (intent.get("action") or "").lower()

        if intent.get("intent") in ["simulate","plot"] and body in SOLAR_SYSTEM:
            dur   = intent.get("duration_days") or 365
            orbit = compute_orbit(body, duration_days=int(dur))
            if orbit:
                plot_b64 = plot_orbit(orbit, f"{body.title()} — {int(dur)}d Trajectory")
                num_data = orbit["elements"]

        elif "transfer" in action or "hohmann" in msg.lower():
            bodies = [b for b in SOLAR_SYSTEM if b in msg.lower()]
            b1 = bodies[0] if len(bodies) > 0 else "earth"
            b2 = bodies[1] if len(bodies) > 1 else "mars"
            tf = compute_hohmann(b1, b2)
            if tf:
                plot_b64 = plot_hohmann(tf)
                num_data = {"from":b1,"to":b2,"transfer_days":tf["transfer_days"],
                            "delta_v1":tf["delta_v1"],"delta_v2":tf["delta_v2"]}

        elif "solar system" in msg.lower() or "all planets" in msg.lower():
            orbits = compute_multi_orbit(["mercury","venus","earth","mars","jupiter","saturn"],365)
            if orbits:
                plot_b64 = plot_multi_orbit(orbits,"Inner & Outer Solar System")
                num_data = {p["body"]:p["elements"] for p in orbits}

        return {"text": text_ans, "plot": plot_b64, "data": num_data,
                "intent": intent, "sim_prompt": sim_prompt}

    except Exception as e:
        return {"text": f"Error: {str(e)}", "plot": None, "data": None,
                "intent": None, "sim_prompt": None}


@app.get("/api/health")
async def health():
    try:
        import rebound
        rb_ver = rebound.__version__
    except:
        rb_ver = "not installed"
    return {
        "status": "online",
        "rebound": rb_ver,
        "model": "llama3.1",
        "rag_docs": get_rag_doc_count(),   # live count, not hardcoded
    }

@app.get("/api/horizons")
async def horizons_scenario():
    """
    Return a scenario dict built from live NASA JPL Horizons data.
    REBOUND fetches actual positions/velocities for today's date.
    The frontend can POST this straight to the WebSocket 'start' action.
    """
    BODIES = ["Sun","Mercury","Venus","Earth","Mars","Jupiter","Saturn","Uranus","Neptune"]
    STYLES = {
        "Sun":     {"color":"#fff200","radius":22,"type":"star"},
        "Mercury": {"color":"#b5b5b5","radius":4, "type":"planet"},
        "Venus":   {"color":"#e8cda0","radius":6, "type":"planet"},
        "Earth":   {"color":"#4fffb0","radius":7, "type":"planet"},
        "Mars":    {"color":"#ff6b35","radius":5, "type":"planet"},
        "Jupiter": {"color":"#c88b3a","radius":14,"type":"planet"},
        "Saturn":  {"color":"#e4d191","radius":12,"type":"planet"},
        "Uranus":  {"color":"#7de8e8","radius":9, "type":"planet"},
        "Neptune": {"color":"#3f54ba","radius":9, "type":"planet"},
    }
    try:
        import rebound, math
        sim = rebound.Simulation()
        sim.units = ('AU','yr','Msun')
        for name in BODIES:
            sim.add(name)
        sim.move_to_com()

        bodies = []
        for i, p in enumerate(sim.particles):
            name  = BODIES[i]
            style = STYLES.get(name, {"color":"#aaaaaa","radius":5,"type":"planet"})
            bodies.append({
                "name":   name,
                "mass":   p.m,
                "x":      round(p.x,  8),
                "y":      round(p.y,  8),
                "vx":     round(p.vx, 8),
                "vy":     round(p.vy, 8),
                **style,
            })

        return {
            "ok": True,
            "scenario": {
                "name":        "Solar System — Live NASA Data",
                "description": "Real positions from NASA JPL Horizons (today)",
                "units":       "solar",
                "integrator":  "whfast",
                "t_per_frame": 0.005,
                "scale":       45.0,
                "collisions":  False,
                "bodies":      bodies,
            }
        }
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.get("/api/examples")
async def examples():
    """Return example simulation prompts for the UI."""
    return {"examples": [
        "Simulate the real solar system",
        "Two neutron stars spiraling together",
        "TRAPPIST-1 system with 7 planets",
        "Hot Jupiter with a super-Earth",
        "Alpha Centauri triple star system",
        "Black hole with 5 orbiting stars",
        "Earth-Moon system",
        "Rogue star flying through a planetary system",
        "Four equal mass stars in a chaotic dance",
        "Protoplanetary disk with 15 planetesimals",
        "Pluto-Charon binary system",
        "Saturn with its rings and moons",
        "A comet on Halley-like orbit",
        "Jupiter's Galilean moons",
        "Pulsar with companion star",
    ]}


if __name__ == "__main__":
    import uvicorn
    print("\n  ╔══════════════════════════════════════════╗")
    print("  ║   ASTRO THESAURUS — REBOUND Server       ║")
    print("  ║   API:  http://localhost:8000             ║")
    print("  ║   WS:   ws://localhost:8000/ws/sim        ║")
    print("  ╚══════════════════════════════════════════╝\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
