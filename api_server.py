from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Astro Thesaurus RAG API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    msg = req.message.strip()
    try:
        # Try full stack (requires query_rag, intent_parser, physics_engine, visualizer)
        from query_rag import query_rag_multi, is_orbital_query
        from intent_parser import parse_intent, answer_with_rag
        from physics_engine import compute_orbit, compute_hohmann, compute_multi_orbit, SOLAR_SYSTEM
        from visualizer import plot_orbit, plot_hohmann, plot_multi_orbit

        if not is_orbital_query(msg):
            return {
                "text": "I specialise in orbital mechanics. Ask me about planet orbits, "
                        "Hohmann transfers, Lagrange points, Kepler's laws, exoplanets, comets or asteroids.",
                "plot": None, "data": None, "intent": None
            }

        intent   = parse_intent(msg)
        rag_ctx  = query_rag_multi(msg)
        text_ans = answer_with_rag(msg, rag_ctx) if rag_ctx else "No relevant data found in database."

        plot_b64 = None
        num_data = None
        body     = (intent.get("body") or "").lower()
        action   = (intent.get("action") or "").lower()

        if intent.get("intent") in ["simulate", "plot"] and body in SOLAR_SYSTEM:
            duration = intent.get("duration_days") or 365
            orbit = compute_orbit(body, duration_days=int(duration))
            if orbit:
                plot_b64 = plot_orbit(orbit, f"{body.title()} — {int(duration)} Day Trajectory")
                num_data = orbit["elements"]
        elif "transfer" in action or "hohmann" in msg.lower():
            bodies = [b for b in SOLAR_SYSTEM if b in msg.lower()]
            b1 = bodies[0] if bodies else "earth"
            b2 = bodies[1] if len(bodies) > 1 else "mars"
            transfer = compute_hohmann(b1, b2)
            if transfer:
                plot_b64 = plot_hohmann(transfer)
                num_data = {k: transfer[k] for k in
                            ["from","to","transfer_days","delta_v1","delta_v2","total_delta_v"]
                            if k in transfer}
        elif "solar system" in msg.lower() or "all planets" in msg.lower():
            orbits = compute_multi_orbit(
                ["mercury","venus","earth","mars","jupiter","saturn"], duration_days=365)
            if orbits:
                plot_b64 = plot_multi_orbit(orbits, "Inner & Outer Solar System")
                num_data = {p["body"]: p["elements"] for p in orbits}
        elif body in SOLAR_SYSTEM:
            orbit = compute_orbit(body, duration_days=365)
            if orbit:
                plot_b64 = plot_orbit(orbit, f"{body.title()} — Orbital Parameters")
                num_data = orbit["elements"]

        return {"text": text_ans, "plot": plot_b64, "data": num_data, "intent": intent}

    except ImportError:
        # Graceful fallback — RAG/physics modules not installed, try ChromaDB directly
        try:
            import chromadb
            client = chromadb.PersistentClient(path="./chroma_db")
            col    = client.get_collection("orbital_dynamics")
            results = col.query(query_texts=[msg], n_results=3)
            docs = results["documents"][0] if results["documents"] else []
            if docs:
                answer = "From the orbital mechanics database:\n\n"
                for doc in docs[:2]:
                    answer += doc[:400].strip() + "\n\n"
                return {"text": answer.strip(), "plot": None, "data": None, "intent": None}
        except Exception:
            pass
        return {
            "text": (
                "⚠️ The RAG/physics modules (query_rag, intent_parser, physics_engine, visualizer) "
                "are not found in the project directory.\n\n"
                "The REBOUND simulator on the right still works fully — type a scenario and click ▶.\n\n"
                "To enable full AI chat answers: make sure query_rag.py, intent_parser.py, "
                "physics_engine.py, and visualizer.py are in the same folder as api_server.py, "
                "then restart the server."
            ),
            "plot": None, "data": None, "intent": None
        }
    except Exception as e:
        return {"text": f"Error: {str(e)}", "plot": None, "data": None, "intent": None}


@app.get("/api/health")
async def health():
    """Health check — returns rebound version and live RAG doc count."""
    rag_count   = 0
    rebound_ver = "not installed"
    try:
        import chromadb
        _client   = chromadb.PersistentClient(path="./chroma_db")
        _col      = _client.get_collection("orbital_dynamics")
        rag_count = _col.count()
    except Exception:
        pass
    try:
        import rebound
        rebound_ver = rebound.__version__
    except Exception:
        pass
    return {"status": "online", "rebound": rebound_ver, "model": "llama3.1", "rag_docs": rag_count}


@app.get("/api/bodies")
async def get_bodies():
    try:
        from physics_engine import SOLAR_SYSTEM
        return {"bodies": list(SOLAR_SYSTEM.keys())}
    except Exception:
        return {"bodies": ["sun","mercury","venus","earth","mars",
                           "jupiter","saturn","uranus","neptune"]}


@app.get("/")
async def root():
    return {"status": "Astro Thesaurus API running"}


if __name__ == "__main__":
    import uvicorn
    print("  ╔══════════════════════════════════════════╗")
    print("  ║   ASTRO THESAURUS — api_server.py        ║")
    print("  ║   API: http://localhost:8000              ║")
    print("  ╚══════════════════════════════════════════╝")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
