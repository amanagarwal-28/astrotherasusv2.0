# 🌌 Astro Thesaurus v2.0
### *Where Gravity Tells Its Story*

A natural-language interface for real-time N-body gravitational simulations. Type a plain-English description of any gravitational system and watch a physically accurate simulation render live in your browser — no coding required.

---

## ✨ Features

- **Natural language input** — describe any system: *"two neutron stars spiraling together"*, *"the real solar system"*, *"a rogue star passing near a binary"*
- **Physically accurate simulation** — powered by the REBOUND N-body integrator (used in real astrophysics research)
- **Local AI pipeline** — Llama 3.1 via Ollama with RAG-augmented context from 1,226 astronomy documents
- **Real astronomical data** — NASA JPL Horizons ephemeris, NASA Exoplanet Archive, Unified Astronomy Thesaurus
- **30 fps real-time rendering** — HTML5 Canvas with glow effects, orbital trails, and live physics stats
- **Fully offline** — no cloud APIs, no API keys, no data leaves your machine

---

## 🏗️ Architecture

```
Browser (index_rebound.html)
        │  WebSocket / HTTP
        ▼
Node.js Server :3000          ← Static file serving only
        │
        ▼
Python FastAPI Backend :8000  ← All intelligence lives here
    ├── RAG Pipeline (ChromaDB + sentence-transformers)
    ├── Llama 3.1 via Ollama
    └── REBOUND N-body Engine
```

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5 Canvas + WebSocket | UI, rendering, user input |
| Frontend Server | Node.js (port 3000) | Static file serving (CORS fix) |
| Backend | Python FastAPI (port 8000) | AI, RAG, physics, WebSocket handler |
| LLM | Ollama + Llama 3.1 8B | Scenario generation from natural language |
| Vector DB | ChromaDB | Semantic search over astronomy documents |
| Physics Engine | REBOUND 4.6.0 | N-body orbital integration |

---

## ⚡ Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) (any recent LTS)
- [Python 3.9+](https://www.python.org/)
- [Ollama](https://ollama.com/) with `llama3.1` pulled

```bash
ollama pull llama3.1
```

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/astro-thesaurus.git
cd astro-thesaurus

# Install Python dependencies
pip install fastapi uvicorn rebound chromadb sentence-transformers

# Build the ChromaDB vector index (first run only)
python build_index.py

# Start the Python backend
python websocket_server.py

# In a separate terminal, start the Node.js frontend server
node server_v2.js

# Open your browser
open http://localhost:3000
```

---

## 🔭 Usage

1. Open `http://localhost:3000` in your browser
2. Type a description into the search bar, for example:
   - `"two neutron stars spiraling together"`
   - `"the real solar system"`
   - `"a rogue star passing near a binary"`
   - `"TRAPPIST-1 planetary system"`
   - `"Halley's comet orbit around the sun"`
3. Press Enter and watch the simulation render in real time
4. Use the controls to **Pause**, **Resume**, **Reset**, or change simulation speed
5. Click the chat panel to ask astronomy questions grounded in real data

---

## 📁 File Structure

```
astro-thesaurus/
├── index_rebound.html          # Complete frontend (UI + canvas renderer + WebSocket client)
├── server_v2.js                # Node.js static file server (port 3000)
├── websocket_server.py         # Python FastAPI backend (port 8000)
├── rebound_engine.py           # REBOUND wrapper — simulation loop & physics extraction
├── ai_scenario_generator.py    # AI pipeline — RAG → Llama 3.1 → JSON → REBOUND params
├── test_rebound.py             # Unit tests for REBOUND API compatibility
├── chroma_db/                  # Persisted ChromaDB vector index (1,226 documents)
└── datasets/
    ├── UAT.json                # Unified Astronomy Thesaurus (~2,000 terms)
    ├── exoplanets.csv          # NASA confirmed exoplanet catalog
    ├── planets_horizons.json   # NASA JPL Horizons solar system state vectors
    ├── asteroids.json          # Asteroid orbital elements & classifications
    ├── comet.json              # Comet orbital elements (high-eccentricity objects)
    ├── trojan.json             # Jupiter Trojan asteroids (L4/L5 Lagrange points)
    └── small_body.json         # Broader minor body catalog
```

---

## 🤖 How It Works

### The AI Pipeline

When you submit a prompt, the following happens in under 5 seconds:

1. **RAG Lookup** — Your prompt is embedded using `sentence-transformers/all-MiniLM-L6-v2` and ChromaDB retrieves the 5 most semantically relevant astronomy document chunks
2. **Prompt Assembly** — A structured prompt is built: system role + retrieved facts + your request + required JSON schema
3. **Llama 3.1 Inference** — Ollama runs the model locally and returns a JSON scenario (masses, positions, velocities, integrator choice)
4. **REBOUND Init** — The JSON is parsed and fed into REBOUND as particle initial conditions
5. **Frame Streaming** — REBOUND advances the simulation and sends each frame to your browser via WebSocket at ~30 fps

If the LLM returns invalid JSON, a keyword-matching fallback system guarantees a simulation always loads.

### Physics Accuracy

REBOUND uses **astronomical units** throughout:
- Length: AU (Earth-Sun distance)
- Mass: Solar masses
- Time: Years
- Gravitational constant: G = 4π²

The **IAS15 integrator** (default) maintains energy conservation to near machine-precision (ΔE/E ≈ 1×10⁻¹⁵), making it suitable for close encounters like neutron star mergers. **WHFast** is used for stable planetary systems and runs 50–100× faster.

---

## 📊 Datasets

| Dataset | Source | Contents |
|---|---|---|
| `UAT.json` | American Astronomical Society | ~2,000 controlled astronomy vocabulary terms |
| `exoplanets.csv` | NASA Exoplanet Archive | Thousands of confirmed exoplanets with orbital parameters |
| `planets_horizons.json` | NASA JPL Horizons | Real solar system state vectors (positions & velocities) |
| `asteroids.json` | Small Body Database | Asteroid orbital elements & classifications |
| `comet.json` | — | Comet orbital elements (e > 0.9 eccentricities) |
| `trojan.json` | — | Jupiter Trojan asteroids at L4/L5 Lagrange points |

---

## 🛠️ Configuration

| Setting | Default | Description |
|---|---|---|
| Backend port | `8000` | Python FastAPI server |
| Frontend port | `3000` | Node.js static server |
| RAG top-k | `5` | Number of document chunks retrieved per query |
| Target FPS | `30` | WebSocket frame rate |
| Embedding model | `all-MiniLM-L6-v2` | 384-dim local semantic embeddings |
| LLM | `llama3.1` (8B) | Local inference via Ollama |

---

## 🔌 API Reference

### WebSocket — `ws://localhost:8000/ws/sim`

| Message (Client → Server) | Description |
|---|---|
| `{action: 'start', prompt: '...', fps: 30}` | Start a new simulation |
| `{action: 'pause'}` | Pause simulation |
| `{action: 'resume'}` | Resume simulation |
| `{action: 'reset'}` | Reset to initial conditions |
| `{action: 'set_speed', multiplier: N}` | Change simulation speed |
| `{action: 'get_elements'}` | Request orbital element calculations |

| Message (Server → Client) | Description |
|---|---|
| `{type: 'status', ...}` | Loading status updates |
| `{type: 'scenario', data: {...}}` | Simulation metadata (name, bodies, integrator) |
| `{type: 'frame', data: {bodies, t, energy_drift}}` | One animation frame |
| `{type: 'elements', data: {...}}` | Computed orbital elements |
| `{type: 'error', message: '...'}` | Error details |

### REST Endpoints

| Endpoint | Description |
|---|---|
| `POST /api/chat` | Chat with the astronomy AI (RAG-augmented) |
| `GET /api/health` | Returns REBOUND version, RAG doc count, status |

---

## 🧪 Testing

```bash
python test_rebound.py
```

Tests verify REBOUND 4.x API compatibility (`particle.orbit()`, `sim.energy()` methods).

---

## 🎨 Rendering Details

The canvas renderer uses layered drawing for visual quality:
- **Trail effect** — Semi-transparent overlay fades old positions rather than clearing the canvas
- **Glow layers** — Each body is drawn three times: outer halo, inner glow, and solid core
- **Body scaling** — Stars, planets, black holes, and neutron stars each have distinct size multipliers and color palettes
- **Background starfield** — Three layers of twinkling stars (600 + 200 + 40) plus shooting stars, rendered on a separate canvas

---

## 📝 Design Decisions

| Decision | Rationale |
|---|---|
| Local LLM (Ollama) | Privacy, zero cost, offline capability, no rate limits |
| ChromaDB | File-based, zero infrastructure, fully offline |
| WebSocket over HTTP | 30 fps streaming requires a persistent connection |
| Two servers | CORS requires a real HTTP origin for WebSocket connections |
| REBOUND over custom integrator | Research-grade accuracy; IAS15 at machine-precision |
| Single HTML file frontend | No build system, fully portable, no framework overhead in the render loop |
| Llama 3.1 8B over 70B | Runs on consumer hardware; 2–5s generation is acceptable for UX |

---

## 📄 License

REBOUND is developed at the University of Toronto (Hanno Rein et al.). Llama 3.1 is released under the Llama 3.1 Community License. Dataset sources are credited to NASA, the American Astronomical Society, and respective data providers.

---

*Built with REBOUND 4.6.0 · Llama 3.1 · ChromaDB · FastAPI · HTML5 Canvas*
