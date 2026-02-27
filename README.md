# 🌌 Astro Thesaurus v2.0

**AI-powered orbital dynamics simulator with RAG-enhanced chatbot**

Real-time N-body physics simulations + intelligent Q&A system for orbital mechanics.

---

## ✨ Features

- 🤖 **RAG-powered chatbot** - 1,226 documents, Llama 3.1 LLM
- 🎬 **Live simulations** - REBOUND N-body engine, 30 FPS
- 🎨 **Advanced visualization** - Orbit trails, velocity coloring, auto-scaling
- 🌍 **Real NASA data** - JPL Horizons + exoplanet archive
- ⚡ **WebSocket streaming** - Real-time bidirectional communication

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install Ollama & pull model
ollama pull llama3.1

# Build database
python rebuild_balanced.py

# Start servers
python websocket_server.py  # Terminal 1
node server_v2.js          # Terminal 2

# Open browser
http://localhost:3000
```

---

## 💬 Chatbot Examples

```
"What is a Hohmann transfer?"
"What's Mars's orbital period?"
"Explain Kepler's third law"
"Calculate delta-v for Earth to Mars"
"What are Lagrange points?"
```

## 🎬 Simulation Examples

```
"Simulate the real solar system"
"Hot Jupiter system"
"Earth-Moon system"
"TRAPPIST-1 with all 7 planets"
"Two neutron stars spiraling together"
"Hohmann transfer Earth to Mars"
```

---

## 📦 Tech Stack

- **Backend:** FastAPI, REBOUND, ChromaDB, Ollama
- **Frontend:** WebSocket, Canvas API, Vanilla JS
- **Data:** NASA JPL Horizons, Exoplanet Archive
- **LLM:** Llama 3.1 (local via Ollama)

---

## 🎨 Key Features

### Orbit Trails
Toggle to see motion history with adjustable fade length

### Auto-Scaling
Prevents bodies going off-screen (scales 20-600 based on system size)

### Velocity Validation
Auto-corrects velocities to prevent falling/escaping bodies

### Z-Ordering
Stars render behind planets (no visual overlapping)

---

## 📊 Database

**1,226 documents:**
- 28 curated concepts (Kepler's laws, transfers, etc.)
- 8 solar system planets
- 500 exoplanets
- 100 asteroids
- 100 Trojans
- ~500 comets

---

## 🎮 Controls

**Simulation:**
- ▶/⏸ Play/Pause
- 🔄 Reset
- 👁️ Trails toggle
- 💫 Glow toggle
- 🏷️ Labels toggle
- ⚡ Speed (1-10×)

**Trail Length:**
- Slider (Instant → V.Long)

---

## 🔧 Configuration

### Change Model
```python
# intent_parser.py & ai_scenario_generator.py
MODEL = "llama3.1"  # Change to other Ollama models
```

### Adjust FPS
```python
# websocket_server.py
fps = 30  # Increase/decrease frame rate
```

### More Exoplanets
```python
# rebuild_balanced.py
exo_count = 500  # Increase number
```

---

## 🐛 Common Issues

**Bodies fall off screen?**
```bash
python smart_restrict.py
```

**Chatbot not responding?**
```bash
ollama list  # Check Ollama running
ls chroma_db/  # Check database exists
```

**Planets overlap Sun?**
- Already fixed with z-ordering
- Reload browser (Ctrl+Shift+R)

---

## 📈 Performance

- RAG Query: < 50ms
- LLM Response: 1-3s
- Simulation: 30 FPS sustained
- Physics Accuracy: ΔE/E < 10⁻⁸

---

## 🔒 Domain

**✅ Can simulate:**
Planets, moons, stars, asteroids, comets, black holes, neutron stars, spacecraft, exoplanets, binary systems

**❌ Cannot simulate:**
Weather, chemistry, biology, quantum mechanics, mechanical systems

---

## 📝 Commit Message (Your Last Push)

```
fix: correct Moon orbital velocity and visual rendering

- Fixed Moon velocity from 6.396 to 0.2148 AU/yr (30× error)
- Added auto-validator to prevent future velocity issues
- Implemented z-ordering to fix planet-Sun visual overlapping
- Added auto-scaling to prevent bodies going off-screen
- Restricted simulations to orbital dynamics domain only
```

---

## 🗺️ Project Structure

```
astro-thesaurus/
├── websocket_server.py       # FastAPI server
├── ai_scenario_generator.py  # AI scenario creation
├── rebound_engine.py          # Physics wrapper
├── query_rag.py               # RAG queries
├── intent_parser.py           # LLM integration
├── scenario_validator.py      # Velocity validation
├── index_rebound.html         # Frontend
├── server_v2.js               # File server
├── chroma_db/                 # Vector database
└── datasets/                  # NASA data
```

---

## 🙏 Acknowledgments

- REBOUND - Hanno Rein & Daniel Tamayo
- ChromaDB - Chroma team
- Ollama - Ollama team
- Llama 3.1 - Meta AI
- NASA JPL - Data sources

---

## 📄 License

MIT License

---

**Built for space enthusiasts and orbital mechanics students** 🚀
