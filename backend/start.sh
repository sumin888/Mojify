#!/bin/sh
# Startup script for Cloud Run.
# If LITESTREAM_GCS_BUCKET is set:
#   1. Restore the SQLite DB from GCS (so data survives container restarts)
#   2. Start Litestream replication in the background (continuous WAL streaming)
# Then start the FastAPI app.

set -e

if [ -n "$LITESTREAM_GCS_BUCKET" ]; then
  echo "[litestream] Restoring database from gs://$LITESTREAM_GCS_BUCKET/mojify.db ..."
  litestream restore -if-replica-exists -o /app/mojify.db "gcs://$LITESTREAM_GCS_BUCKET/mojify.db" || true
  echo "[litestream] Starting continuous replication to gs://$LITESTREAM_GCS_BUCKET ..."
  litestream replicate -config /app/litestream.yml &
else
  echo "[warning] LITESTREAM_GCS_BUCKET not set — data will NOT persist across restarts"
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}"
