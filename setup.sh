#!/usr/bin/env bash
# One-command environment setup for Astro Thesaurus v2.0 (Linux / macOS).
# Creates a Python venv, installs pinned dependencies, and checks for the
# non-pip prerequisites (Node.js, Ollama, a C compiler for the `rebound` build).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== Checking prerequisites =="

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: $PYTHON_BIN not found. Install Python 3.11+ first." >&2
    exit 1
fi
echo "Python:  $($PYTHON_BIN --version)"

if ! command -v cc >/dev/null 2>&1 && ! command -v gcc >/dev/null 2>&1; then
    echo "ERROR: no C compiler found. The 'rebound' package builds a C extension on install." >&2
    echo "       Install build tools first, e.g. 'sudo apt install build-essential' on Debian/Ubuntu." >&2
    exit 1
fi
echo "C compiler: $(command -v cc || command -v gcc)"

if command -v node >/dev/null 2>&1; then
    echo "Node.js: $(node --version)"
else
    echo "WARNING: Node.js not found. server_v2.js (the static frontend server) needs Node.js >= 18." >&2
fi

if command -v ollama >/dev/null 2>&1; then
    echo "Ollama:  $(ollama --version 2>&1 | head -1)"
else
    echo "WARNING: Ollama not found. The RAG chatbot and AI scenario generator require it." >&2
    echo "         Install from https://ollama.com/download, then run: ollama pull llama3.1" >&2
fi

echo
echo "== Setting up Python virtual environment (.venv) =="
"$PYTHON_BIN" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt

echo
echo "== Verifying project modules import correctly =="
python -c "
import importlib
mods = ['physics_engine','orbital_physics','query_rag','intent_parser',
        'rebound_engine','scenario_validator','visualizer','websocket_server']
for m in mods:
    importlib.import_module(m)
print('All modules imported successfully.')
"

echo
echo "== Done =="
echo "Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. ollama pull llama3.1        (if not already pulled)"
echo "  3. python rebuild_balanced.py  (builds chroma_db/, one-time)"
echo "  4. uvicorn websocket_server:app --host 0.0.0.0 --port 8000   # Terminal 1"
echo "  5. node server_v2.js                                          # Terminal 2"
echo "  6. open http://localhost:3000"
echo
echo "To run the validation test suite (see VALIDATION.md):"
echo "  pip install -r requirements-dev.txt"
echo "  pytest -m \"not network\""
