---
name: Flask on Replit Nix
description: How to run a Python Flask backend as an api-server artifact on Replit Nix, including package restrictions and path gotchas.
---

# Flask on Replit Nix

## The rule
Workflow run commands must use **absolute paths** for shell scripts. Relative paths like `bash artifacts/flask-ranker/start.sh` fail because the workflow runner's cwd is not guaranteed to be the workspace root.

**Why:** Got `No such file or directory` on first deploy even though the file existed at the relative path.

**How to apply:** Always write `bash /home/runner/workspace/artifacts/flask-ranker/start.sh` in artifact.toml `run` commands.

## sentence-transformers cannot be installed

`sentence-transformers` cannot be installed in this Nix environment via:
- `pip install` — blocked by PEP 668
- `installLanguagePackages(python-3.11)` — uv resolver returns "no versions on linux"

**Why:** Replit Nix uses a locked system-level Python; heavy ML packages with complex native deps are blocked.

**How to apply:** Implement a TF-IDF cosine similarity fallback (scikit-learn, which IS installed via `.pythonlibs`) in the semantic scorer. Use lazy import of `sentence_transformers` wrapped in try/except so Flask starts cleanly regardless.

## Packages that DO install
These are already in `.pythonlibs` and importable by system `python3`:
- flask, flask-cors, werkzeug
- scikit-learn, numpy, scipy
- rank-bm25, pandas, python-dateutil

## start.sh pattern
```bash
#!/usr/bin/env bash
set -e
cd /home/runner/workspace/artifacts/flask-ranker
export FLASK_PORT="${PORT:-8080}"
exec python3 app.py
```
