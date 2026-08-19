# Astro Thesaurus v2.0 — Technical Document

**Document Version:** 1.0  
**Date:** April 1, 2026  
**Project:** AI-Powered Orbital Dynamics Simulator with RAG-Enhanced Chatbot

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Component Reference](#3-component-reference)
4. [Data Layer](#4-data-layer)
5. [Physics Engine](#5-physics-engine)
6. [AI & RAG Pipeline](#6-ai--rag-pipeline)
7. [Simulation Engine (REBOUND)](#7-simulation-engine-rebound)
8. [WebSocket Protocol](#8-websocket-protocol)
9. [Frontend](#9-frontend)
10. [API Reference](#10-api-reference)
11. [Deployment](#11-deployment)
12. [Dataset Inventory](#12-dataset-inventory)
13. [Validation & Benchmarks](#13-validation--benchmarks)

---

## 1. System Overview

Astro Thesaurus v2.0 is a real-time orbital mechanics platform combining:

- **N-body physics simulation** using the REBOUND integrator, streamed at 30 FPS over WebSocket
- **RAG (Retrieval-Augmented Generation) chatbot** backed by ChromaDB and Llama 3.1 (via Ollama)
- **Keplerian trajectory engine** for analytical orbit computation and Hohmann transfer calculations
- **AI scenario generator** that converts natural-language prompts into fully parameterised simulation setups

The system is entirely local — no external API keys are required. All AI inference runs through the user's local Ollama instance.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER CLIENT                           │
│  index_rebound.html — Canvas renderer + WebSocket client        │
│  index_v2.html      — Legacy chat-only interface                │
└──────────────────────┬──────────────────────┬───────────────────┘
                       │ HTTP :3000            │ WebSocket :8000
                       ▼                       ▼
              ┌────────────────┐   ┌──────────────────────────────┐
              │  server_v2.js  │   │     websocket_server.py       │
              │  Node.js HTTP  │   │  FastAPI + uvicorn            │
              │  Static files  │   │  /ws/sim  — simulation stream │
              └────────────────┘   │  /api/chat — RAG Q&A          │
                                   │  /api/simulate — POST         │
                                   │  /api/status  — health check  │
                                   └──────────┬───────────────────┘
                                              │
                    ┌─────────────────────────┼──────────────────────┐
                    ▼                         ▼                      ▼
         ┌──────────────────┐   ┌─────────────────────┐  ┌──────────────────┐
         │  rebound_engine  │   │    query_rag.py      │  │  physics_engine  │
         │  N-body sim      │   │    ChromaDB client   │  │  Keplerian orbits│
         │  IAS15/WHFast    │   │    1,226 documents   │  │  Hohmann calc    │
         └──────────────────┘   └──────────┬──────────┘  └──────────────────┘
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                    ┌──────────────────┐    ┌───────────────────────┐
                    │   chroma_db/     │    │  intent_parser.py     │
                    │  SQLite + HNSW   │    │  Ollama Llama 3.1     │
                    │  vector store    │    │  JSON intent parser   │
                    └──────────────────┘    └───────────────────────┘
                                                        │
                                           ┌────────────┴────────────┐
                                           ▼                         ▼
                                 ┌──────────────────┐   ┌────────────────────┐
                                 │ ai_scenario_     │   │  scenario_         │
                                 │ generator.py     │   │  validator.py      │
                                 │ Prompt → JSON    │   │  Velocity fixer    │
                                 └──────────────────┘   └────────────────────┘
```

### Port Layout

| Port | Service | Protocol |
|------|---------|----------|
| 3000 | `server_v2.js` – static file server | HTTP |
| 8000 | `websocket_server.py` – simulation & chat API (primary; serves `index_rebound.html`) | HTTP + WebSocket |
| 8001 | `api_server.py` – chat-only API (legacy; serves `index_v2.html` only) | HTTP |
| 11434 | Ollama – local LLM inference | HTTP |

---

## 3. Component Reference

### `websocket_server.py`
Primary backend server (FastAPI). Combines all subsystems into a single process:
- WebSocket endpoint `/ws/sim` streams N-body simulation frames
- REST endpoint `/api/chat` handles RAG chatbot queries
- REST endpoint `/api/simulate` accepts POST for on-demand simulation start
- REST endpoint `/api/status` exposes health check with live RAG document count

### `rebound_engine.py`
Wraps the REBOUND C library through its Python bindings. Provides:
- `ReboundEngine.load_scenario(dict)` — initialises a simulation from a scenario dict
- `ReboundEngine.step()` — advances by `t_per_frame` and returns a frame dict
- `ReboundEngine.reset()` — restores to the initial scenario state
- Energy drift tracking (`(E - E₀) / E₀`) for integration quality monitoring

### `ai_scenario_generator.py`
Sends natural-language prompts to the local Ollama `/api/generate` endpoint, requesting structured JSON. The generated scenario is then passed to `scenario_validator.py` before being loaded into REBOUND.

### `scenario_validator.py`
Post-processes scenarios produced by the AI generator:
- Detects bodies with velocities below 30 % of circular velocity (will crash)
- Detects bodies with velocities above 150 % of escape velocity (hyperbolic escape)
- Auto-corrects to circular orbit velocity when a problem is found
- Preserves direction of the original velocity vector after rescaling

### `query_rag.py`
ChromaDB client layer. Exposes:
- `is_orbital_query(text)` — keyword guard to reject out-of-domain questions
- `query_rag(question, n)` — plain top-N vector search
- `query_rag_by_type(question, type, n)` — filtered search by metadata type
- `query_rag_multi(question)` — composite search: concept definitions + planet data + exoplanet/comet/asteroid data merged into a single context string

### `intent_parser.py`
Sends user input to Ollama with a strict system prompt; returns a JSON object:

```json
{
  "intent": "simulate|query|explain|plot|compare",
  "body": "mars",
  "action": "orbit|transfer|lagrange|resonance|flyby|explain|list",
  "duration_days": 730,
  "reference": "sun",
  "plot_type": "orbit|histogram|phase|hr|trajectory",
  "is_orbital": true
}
```

### `physics_engine.py`
Analytical Keplerian engine (no N-body):
- Solves Kepler's equation using Newton–Raphson iteration
- Computes elliptic trajectories at 500 sample points
- Implements the Hohmann transfer $\Delta v$ equations
- Returns base64-encoded matplotlib plots via `visualizer.py`

### `orbital_physics.py`
Pure-math helper library (no external dependencies). Exported functions:

| Function | Description |
|----------|-------------|
| `circular_orbit_velocity(M, r)` | $v = \sqrt{GM/r}$ in AU/yr |
| `orbital_period(M, r)` | $T = 2\pi\sqrt{r^3/GM}$ in years |
| `velocity_from_period(r, T)` | $v = 2\pi r / T$ |
| `binary_velocities(m1, m2, sep, e)` | Velocities for a binary pair |
| `escape_velocity(M, r)` | $v_{esc} = \sqrt{2GM/r}$ |

### `visualizer.py`
Matplotlib-based static plot generator. All figures are rendered to PNG and returned as base64 strings. Supports:
- Orbital path with velocity colour-mapping
- Distance and speed vs time line charts
- Hohmann transfer diagrams

### `rebuild_balanced.py`
One-time database builder. Drops and recreates the ChromaDB `orbital_dynamics` collection, then ingests all document types in priority order.

### `server_v2.js`
Minimal Node.js HTTP server. Serves static frontend files from the workspace root directory on port 3000.

### `api_server.py`
Legacy chat-only FastAPI server (port 8001), predating `websocket_server.py`.
Serves `/api/chat` for `index_v2.html` only — no simulation streaming. New
work should go through `websocket_server.py`; this file is kept solely for
`index_v2.html` backward compatibility.

---

## 4. Data Layer

### ChromaDB Vector Store

**Location:** `./chroma_db/`  
**Collection:** `orbital_dynamics`  
**Total documents:** 1,226  
**Embedding model:** ChromaDB default (all-MiniLM-L6-v2)

| Type | Count | Source |
|------|-------|--------|
| Curated concepts | 28 | Hand-written (`rebuild_balanced.py`) |
| Solar system planets | 8 | Hand-written |
| Exoplanets | 500 | NASA Exoplanet Archive (`datasets/exoplanets.csv`) |
| Asteroids | 100 | MPC / JPL (`datasets/asteroids.json`) |
| Jupiter Trojans | 100 | MPC (`datasets/trojan.json`) |
| Comets | ~490 | MPC (`datasets/comet.json`) |

Metadata schema per document:

```jsonc
{
  "source": "NASA | curated | MPC",
  "type": "planet | concept | exoplanet | asteroid | trojan | comet"
}
```

### Curated Concept Topics

Kepler's three laws, Vis-Viva equation, Hohmann transfer, Lagrange points (L1–L5), Roche limit, orbital resonance, three-body problem, eccentricity, escape velocity, gravity assist, tidal locking, orbital perturbation, binary star systems, orbital inclination, semi-major axis, Halley's Comet.

---

## 5. Physics Engine

### Keplerian Orbit Computation (`physics_engine.py`)

Propagation follows standard two-body orbital mechanics using the eccentric anomaly. For a body with semi-major axis $a$ and eccentricity $e$:

$$M(t) = \frac{2\pi t}{T}$$

Kepler's equation is solved with Newton–Raphson:

$$E_{n+1} = E_n + \frac{M - E_n + e\sin(E_n)}{1 - e\cos(E_n)}$$

True anomaly:

$$\nu = 2\arctan\!\left(\sqrt{\frac{1+e}{1-e}}\tan\frac{E}{2}\right)$$

Radius:

$$r = \frac{a(1-e^2)}{1+e\cos\nu}$$

Speed (Vis-Viva, converted to AU/day):

$$v = \sqrt{GM\!\left(\frac{2}{r}-\frac{1}{a}\right)} \cdot \frac{365.25}{2\pi}$$

### Hohmann Transfer

For transfer from orbit $r_1$ to orbit $r_2$:

$$\Delta v_1 = \sqrt{\frac{GM}{r_1}}\!\left(\sqrt{\frac{2r_2}{r_1+r_2}}-1\right)$$

$$\Delta v_2 = \sqrt{\frac{GM}{r_2}}\!\left(1-\sqrt{\frac{2r_1}{r_1+r_2}}\right)$$

$$t_{transfer} = \pi\sqrt{\frac{(r_1+r_2)^3}{8GM}}$$

### Unit System

All physics uses solar units: AU (length), years (time), solar masses (mass).  
Gravitational constant: $G = 4\pi^2 \approx 39.48 \ \text{AU}^3\,\text{yr}^{-2}\,M_\odot^{-1}$

---

## 6. AI & RAG Pipeline

### Query Flow

```
User message
    │
    ▼
is_orbital_query()  ──(false)──► "I specialise in orbital mechanics…"
    │ (true)
    ▼
query_rag_multi()   ──► ChromaDB vector search (concepts + filtered types)
    │
    ▼
intent_parser()     ──► Ollama Llama 3.1 → structured JSON intent
    │
    ▼
physics_engine / rebound_engine   (if intent == simulate / plot)
    │
    ▼
answer_with_rag()   ──► Ollama Llama 3.1 + RAG context → text answer
    │
    ▼
JSON response: { text, plot (base64), data, intent }
```

### LLM Configuration

| Parameter | Value |
|-----------|-------|
| Model | `llama3.1` |
| Endpoint | `http://localhost:11434/api/generate` |
| Temperature (intent parser) | 0.1 |
| Temperature (scenario generator) | default |
| Max tokens (intent parser) | 500 |
| Stream | false |
| Timeout | 120 s |

### Scenario Generation Prompt

The scenario generator uses a strict system prompt that instructs Llama 3.1 to return **only** a JSON object matching the REBOUND scenario schema. Critical invariant enforced in the prompt:

$$v_{circular} = 2\pi\sqrt{\frac{M}{r}}$$

where $M$ is central body mass in solar masses and $r$ is orbital radius in AU (numerically equal to $\sqrt{GM/r}$ in solar units since $G = 4\pi^2$).

After generation, `scenario_validator.py` applies a secondary correction pass before the scenario reaches REBOUND.

---

## 7. Simulation Engine (REBOUND)

### Integrators

| Key | REBOUND integrator | Best for |
|-----|--------------------|----------|
| `ias15` | IAS15 (adaptive RK) | Default; chaotic systems, close encounters |
| `whfast` | WHFast (symplectic) | Long-term planetary systems |
| `mercurius` | MERCURIUS (hybrid) | Mixed: distant WHFast + nearby IAS15 |
| `leapfrog` | Leapfrog | Fast, lower accuracy |
| `bs` | Bulirsch–Stoer | High-accuracy short integrations |

### Scenario Schema

```jsonc
{
  "name": "string",
  "description": "string",
  "units": "solar",            // AU / yr / Msun  (only supported value)
  "integrator": "ias15",
  "t_per_frame": 0.005,        // simulation years advanced per frame
  "scale": 180,                // AU → canvas pixels hint
  "bodies": [
    {
      "name": "string",
      "mass": 1.0,             // solar masses
      "x": 0.0,                // AU
      "y": 0.0,                // AU
      "vx": 0.0,               // AU/yr
      "vy": 6.28,              // AU/yr
      "color": "#fff200",
      "radius": 15,            // canvas pixels
      "type": "star|planet|moon|comet|asteroid|blackhole|neutron|debris|spacecraft"
    }
  ]
}
```

### Frame Format (Server → Client)

```jsonc
{
  "type": "frame",
  "data": {
    "t": 1.23,                        // simulation time (years)
    "N": 4,                           // number of bodies
    "energy_drift": -3.2e-10,         // (E - E₀) / E₀
    "bodies": [
      { "name": "Sun",  "x": 0.0,  "y": 0.0,  "vx": 0.0, "vy": 0.0,
        "mass": 1.0, "color": "#fff200", "radius": 15, "type": "star" }
    ]
  }
}
```

Energy drift is computed every frame as $(E - E_0) / E_0$ and included for integration quality monitoring in the client UI.

---

## 8. WebSocket Protocol

**Endpoint:** `ws://localhost:8000/ws/sim`  
**Encoding:** UTF-8 JSON text frames

### Client → Server Messages

| Action | Required fields | Description |
|--------|-----------------|-------------|
| `start` | `prompt`, `fps`, `steps_per_frame` | Begin or restart simulation |
| `pause` | — | Halt frame streaming |
| `resume` | — | Continue streaming |
| `reset` | — | Re-load initial scenario |
| `stop` | — | Stop and clean up |
| `set_speed` | `multiplier` | Scale physics steps per frame |

Example:
```json
{ "action": "start", "prompt": "hot Jupiter system", "fps": 30 }
```

### Server → Client Message Types

| `type` | Description | Key fields |
|--------|-------------|------------|
| `scenario` | Sent once after scenario loads | `name`, `description`, `N`, `integrator`, `scale`, `bodies[]` |
| `frame` | Sent every physics step | `t`, `N`, `bodies[]`, `energy_drift` |
| `status` | Human-readable progress message | `message` |
| `error` | Error notification | `message` |

---

## 9. Frontend

### Files

| File | Purpose |
|------|---------|
| `index_rebound.html` | Primary UI — simulation canvas + chat (default served at `/`) |
| `index_v2.html` | Alternative chat-focused layout |

### Design System

| Token | Value | Usage |
|-------|-------|-------|
| `--void` | `#000008` | Page background |
| `--deep` | `#03071a` | Panel background |
| `--accent` | `#3280ff` | Primary interactive elements |
| `--pulse` | `#00e5ff` | Glow highlights |
| `--text` | `#c8d8ff` | Body text |
| `--green` | `#00ff88` | Positive indicators |
| `--nova` | `#ff1a6e` | Alerts / destructive |

**Typography:**
- `Orbitron` — headings, logo
- `JetBrains Mono` — data, code values  
- `Space Grotesk` — body text

### Layout

3-column CSS Grid (`280px | 1fr | 360px`) with a 52 px header row:

```
┌──────────────────────────────────────────────────────┐
│                     HEADER (52px)                    │
├────────────┬────────────────────────┬────────────────┤
│  LEFT      │   CANVAS (simulation)  │  RIGHT         │
│  Controls  │   Canvas API / WebGL   │  Chat panel    │
│  Scenarios │                        │  RAG messages  │
└────────────┴────────────────────────┴────────────────┘
```

### Canvas Renderer

- HTML5 `<canvas>` with 2D context
- Bodies rendered as filled circles with glow shadows
- **Orbit trails**: ring buffer of past positions, faded by age
- **Auto-scaling**: scale hint from scenario guides initial view; auto-zoom keeps all bodies within canvas
- **Z-ordering**: stars rendered first (behind planets)
- **Velocity coloring**: body colour is mapped to speed relative to system mean — cool blue (slow) to hot white (fast)

---

## 10. API Reference

### `POST /api/chat`

Request:
```json
{ "message": "What is a Hohmann transfer?" }
```

Response:
```jsonc
{
  "text": "A Hohmann transfer is...",
  "plot": "<base64 PNG | null>",
  "data": { "semi_major_axis_au": 1.524, ... },
  "intent": { "intent": "explain", "body": null, "action": "transfer", ... }
}
```

### `POST /api/simulate`

Request:
```json
{ "prompt": "simulate a hot Jupiter system", "frames_per_second": 30, "steps_per_frame": 2 }
```

Response:
```json
{ "status": "started", "message": "Use WebSocket /ws/sim to receive frames" }
```

### `GET /api/status`

Response:
```json
{ "status": "ok", "rag_docs": 1226, "ollama": "available" }
```

---

## 11. Deployment

### Prerequisites

Pinned exact versions live in [`requirements.txt`](../requirements.txt) and
[`.python-version`](../.python-version); `setup.sh` verifies all non-pip
prerequisites before installing.

| Dependency | Version (pinned) | Install |
|------------|-------------------|---------|
| Python | 3.13 (3.11+ should work) | system |
| C compiler | any (gcc/clang) | `build-essential` (Debian/Ubuntu) / Xcode CLT (macOS) — required to build the `rebound` C extension |
| Node.js | ≥ 18 (tested on 20) | system |
| Ollama | latest | `ollama.com/download` |
| REBOUND | 5.1.1 | `requirements.txt` |
| FastAPI | 0.141.1 | `requirements.txt` |
| Uvicorn | 0.52.3 (`[standard]` extra, for WebSocket support) | `requirements.txt` |
| ChromaDB | 1.5.9 | `requirements.txt` |
| Pydantic | 2.13.4 | `requirements.txt` |
| NumPy | 2.5.2 | `requirements.txt` |
| Matplotlib | 3.11.1 | `requirements.txt` |
| Requests | 2.34.2 | `requirements.txt` |
| Astroquery | 0.4.11 | `requirements.txt` |

### Setup Sequence

```bash
# 1. One-command setup: venv + pinned Python deps + prerequisite checks
./setup.sh
source .venv/bin/activate

# 2. Pull LLM model (requires Ollama running)
ollama pull llama3.1

# 3. Build vector database (one-time; drops & rebuilds collection)
python rebuild_balanced.py

# 4. Start simulation + API server (Terminal 1)
uvicorn websocket_server:app --host 0.0.0.0 --port 8000

# 5. Start frontend HTTP server (Terminal 2)
node server_v2.js

# 6. Open browser
http://localhost:3000
```

CI (`.github/workflows/ci.yml`) installs `requirements.txt` and import-smoke-tests
every module on each push, so environment drift is caught automatically rather
than discovered at demo time.

### Database Rebuild

Run `rebuild_balanced.py` to regenerate the ChromaDB collection:

```bash
python rebuild_balanced.py
```

The script processes sources in this order:
1. 28 hand-written concept/planet documents
2. 500 exoplanets from `datasets/exoplanets.csv`
3. 100 asteroids from `datasets/asteroids.json`
4. 100 Jupiter Trojans from `datasets/trojan.json`
5. Comets from `datasets/comet.json`

Total ingest time: ~30–90 seconds depending on hardware.

### Adding New Concepts

Use `add_concept.py` to append a single document to the live collection without a full rebuild.

---

## 12. Dataset Inventory

| File | Format | Contents |
|------|--------|----------|
| `datasets/exoplanets.csv` | NASA CSV | 5,000 + confirmed exoplanets (pl_name, pl_orbsmax, pl_orbeccen, pl_bmassj, hostname) |
| `datasets/asteroids.json` | JSON array | MPC asteroid elements |
| `datasets/trojan.json` | JSON array | Jupiter Trojan elements |
| `datasets/comet.json` | JSON array | MPC comet orbital elements |
| `datasets/planets_horizons.json` | JSON | 8 planet state vectors from JPL Horizons |
| `datasets/mars_elements.json` | JSON | High-precision Mars orbital elements |
| `datasets/small_body.json` | JSON array | Small body catalog |
| `datasets/nearby_stars.csv` | CSV | Nearby star catalog (SIMBAD) |
| `astro-data.json` | JSON | Aggregated reference data |

---

## 13. Validation & Benchmarks

Full methodology, reproduction commands, and results live in
[`VALIDATION.md`](../VALIDATION.md). Summary:

- **`tests/`** — pytest suite covering closed-form physics (Kepler, vis-viva,
  Hohmann Δv vs textbook values), REBOUND energy/momentum conservation, and
  the `orbital_accuracy.py` scoring modes, including a regression check that
  a poorly-suited integrator scores measurably worse than `ias15` on the same
  orbit. Offline tests run in CI on every push (`pytest -m "not network"`,
  ~0.5s); Horizons-dependent ground-truth tests run best-effort
  (`pytest -m network`).
- **`benchmarks/integrator_comparison.py`** — deterministic, offline
  benchmark integrating a 9-body Sun+planets system under `ias15`, `whfast`,
  and `leapfrog` for 50 years, producing the energy-drift comparison figure
  referenced in the README's accuracy claim.

---

## Appendix A — Orbital Mechanics Reference

| Symbol | Meaning | Unit |
|--------|---------|------|
| $a$ | Semi-major axis | AU |
| $e$ | Eccentricity | — |
| $T$ | Orbital period | yr / days |
| $M$ | Mean anomaly | rad |
| $E$ | Eccentric anomaly | rad |
| $\nu$ | True anomaly | rad |
| $r$ | Orbital radius | AU |
| $v$ | Orbital speed | AU/yr or km/s |
| $\Delta v$ | Delta-v | km/s or AU/yr |
| $G$ | Gravitational constant | $4\pi^2$ (solar units) |

**Common velocity conversions:**  
1 AU/yr ≈ 4.740 km/s

---

## Appendix B — Body Type Color Guide

| Type | Color | Hex |
|------|-------|-----|
| Yellow star | Yellow | `#fff200` |
| Blue star | Light blue | `#aaddff` |
| Red dwarf | Red | `#ff4444` |
| Earth-like planet | Cyan-green | `#4fffb0` |
| Mars-like planet | Orange | `#ff6b35` |
| Gas giant | Tan | `#c88b3a` |
| Black hole | Dark purple | `#220022` |
| Moon / rocky | Grey | `#cccccc` |
| Comet | Ice blue | `#aaddff` |

---

*End of Technical Document*
