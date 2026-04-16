#!/bin/sh
set -e
cd /app

# Render injecte PORT ; fallback local / Dockerfile
export PORT="${PORT:-8000}"

alembic upgrade head

# # Données de démo une seule fois (seed.py ignore si la BDD est déjà peuplée)
# if [ "${HORIZON_AUTO_SEED:-true}" != "false" ]; then
#   python scripts/seed.py
# fi

exec uvicorn horizon.main:app --host 0.0.0.0 --port "$PORT" --workers 1
