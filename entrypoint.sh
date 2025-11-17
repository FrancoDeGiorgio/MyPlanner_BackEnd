#!/bin/bash
set -euo pipefail

echo "🔍 Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ PostgreSQL started"

echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations completed successfully"
else
    status=$?
    echo "⚠️  Alembic upgrade failed (exit code $status)."
    if [ "${ALEMBIC_STAMP_LEGACY_SCHEMA:-0}" = "1" ]; then
        echo "♻️  Attempting to stamp existing schema to revision 001 and retry..."
        alembic stamp 001
        alembic upgrade head
        echo "✅ Legacy schema stamped and migrations applied"
    else
        cat <<'EOF'
❌ Migrations failed.

Possibile causa: il database contiene già lo schema base creato manualmente.

Soluzioni possibili:
  1. Eliminare il volume e ripartire da zero:
       docker compose down -v
       docker compose up --build
  2. (Avanzato) Impostare ALEMBIC_STAMP_LEGACY_SCHEMA=1 per eseguire automaticamente:
       alembic stamp 001
       alembic upgrade head

Nota: ALEMBIC_STAMP_LEGACY_SCHEMA=1 va usato solo se si è certi che lo schema attuale
      corrisponda alla revisione iniziale.
EOF
        exit $status
    fi
fi

echo "🚀 Starting FastAPI application..."
if [ "${ENVIRONMENT:-development}" = "production" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4}
else
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
fi

