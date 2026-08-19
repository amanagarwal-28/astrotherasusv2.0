# Archived development scripts

These files are **not part of the running system**. They're kept for
historical/development-process context, not for reuse — none of them are
imported by any other module in the project (verified by grep before
archiving).

| File | What it was |
|---|---|
| `emergency_fix.py`, `fix_overlap.py`, `fix_mars.py`, `fix_suggestions.py`, `smart_restrict.py` | One-shot scripts that patched `index_rebound.html` / `websocket_server.py` / the ChromaDB collection in place during development (e.g. "planets overlapping the Sun", "wrong Mars velocity"). Each fix has already been applied — the result is in the current committed code, not in these scripts. **Do not re-run them**: they search-and-replace against an assumed prior state and will not behave predictably against the current codebase. |
| `build_rag.py` | An earlier, superseded version of the ChromaDB collection builder. [`rebuild_balanced.py`](../../rebuild_balanced.py) at the repo root is the current, documented builder (see `TECHNICAL_DOCUMENT.md` §11). |
| `api_server.py.backup` | A literal backup snapshot of `api_server.py` from during development. |
| `test.py`, `test_rebound.py` | Manual smoke-test scripts (print-based, no assertions) written before the project had an automated test suite. Superseded by [`tests/`](../../tests/) (pytest, see `VALIDATION.md`). |

If you're trying to understand *why* the current code looks the way it does
(e.g. why Moon velocity is computed a specific way, or why the frontend
z-orders stars behind planets), these scripts' docstrings and diffs are the
paper trail — that's the only reason they're kept instead of deleted.
