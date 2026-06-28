#!/usr/bin/env bash
set -e
cd /home/runner/workspace/artifacts/flask-ranker
export FLASK_PORT="${PORT:-8080}"
exec python3 app.py
