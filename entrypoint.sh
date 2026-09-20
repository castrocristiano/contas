#!/bin/sh
set -e

echo "==> Running database migrations with Alembic..."
uv run --no-dev alembic upgrade head

echo "==> Starting Streamlit web server on port 8501..."
exec uv run --no-dev streamlit run src/contas/ui/app.py --server.port=8501 --server.address=0.0.0.0

