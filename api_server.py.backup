from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sys
import os

sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="Astro Thesaurus RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str

class SimRequest(BaseModel):
    scenario: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        from query_rag import query_rag_multi, is_orbital_query
        from intent_parser import parse_intent, answer_with_rag
        from physics_engine import compute_orbit, compute_hohmann, compute_multi_orbit, SOLAR_SYSTEM
        from visualizer import plot_orbit, plot_hohmann, plot_multi_orbit

        msg = req.message.strip()

        # Domain check
        if not is_orbital_query(msg):
            return {
                "text": "I specialize in orbital mechanics and dynamics only. Try asking about planet orbits, Hohmann transfers, Lagrange points, Kepler's laws, exoplanets, comets, or asteroids.",
                "plot": None,
                "data": None,
                "intent": None
            }

        # Parse intent
        intent = parse_intent(msg)

        # Query RAG
        rag_context = query_rag_multi(msg)

        # Generate text answer
        text_answer = answer_with_rag(msg, rag_context) if rag_context else "I couldn't find relevant data for that query."

        plot_b64 = None
        numerical_data = None
        body = (intent.get("body") or "").lower()
        action = (intent.get("action") or "").lower()

        # Route to correct physics + visualization
        if intent.get("intent") in ["simulate", "plot"] and body in SOLAR_SYSTEM:
            duration = intent.get("duration_days") or 365
            orbit = compute_orbit(body, duration_days=int(duration))
            if orbit:
                plot_b64 = plot_orbit(orbit, f"{body.title()} — {int(duration)} Day Trajectory")
                numerical_data = orbit["elements"]

        elif "transfer" in action or "hohmann" in msg.lower():
            # Detect from/to bodies
            bodies = [b for b in SOLAR_SYSTEM if b in msg.lower()]
            b1 = bodies[0] if len(bodies) > 0 else "earth"
            b2 = bodies[1] if len(bodies) > 1 else "mars"
            transfer = compute_hohmann(b1, b2)
            if transfer:
                plot_b64 = plot_hohmann(transfer)
                numerical_data = {
                    "from": b1, "to": b2,
                    "transfer_days": transfer["transfer_days"],
                    "delta_v1": transfer["delta_v1"],
                    "delta_v2": transfer["delta_v2"],
                    "total_delta_v": transfer["total_delta_v"]
                }

        elif "solar system" in msg.lower() or "all planets" in msg.lower():
            planet_list = ["mercury","venus","earth","mars","jupiter","saturn"]
            orbits = compute_multi_orbit(planet_list, duration_days=365)
            if orbits:
                plot_b64 = plot_multi_orbit(orbits, "Inner & Outer Solar System")
                numerical_data = {p["body"]: p["elements"] for p in orbits}

        elif body in SOLAR_SYSTEM and intent.get("intent") == "explain":
            orbit = compute_orbit(body, duration_days=365)
            if orbit:
                plot_b64 = plot_orbit(orbit, f"{body.title()} — Orbital Parameters")
                numerical_data = orbit["elements"]

        return {
            "text": text_answer,
            "plot": plot_b64,
            "data": numerical_data,
            "intent": intent
        }

    except Exception as e:
        return {
            "text": f"Error processing request: {str(e)}",
            "plot": None,
            "data": None,
            "intent": None
        }

@app.get("/api/bodies")
async def get_bodies():
    from physics_engine import SOLAR_SYSTEM
    return {"bodies": list(SOLAR_SYSTEM.keys())}

@app.get("/api/health")
async def health():
    return {"status": "online", "model": "llama3.1", "rag_docs": 1226}

@app.get("/")
async def root():
    return {"status": "Astro Thesaurus API running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
