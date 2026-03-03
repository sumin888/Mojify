#!/bin/bash
# Deploy Mojify to Google Cloud Run (unified: single URL for frontend + backend)
# Prerequisites: gcloud CLI, GCP project with Cloud Run API enabled
#
# ONE-TIME SETUP (run before first deploy):
#   1. Create the GCS bucket for SQLite persistence:
#        gsutil mb -p YOUR_PROJECT -l us-central1 gs://mojify-db
#        gsutil uniformbucketlevelaccess set on gs://mojify-db
#   2. Grant the Cloud Run service account access:
#        PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT --format='value(projectNumber)')
#        gsutil iam ch serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com:roles/storage.objectAdmin gs://mojify-db
#   3. Set secrets once (they survive all future deploys):
#        gcloud run services update mojify --region us-central1 \
#          --update-env-vars TELEGRAM_BOT_TOKEN=<token>,OPENAI_API_KEY=<key>

set -e

# Config - change these
PROJECT_ID="${GCP_PROJECT_ID:-mojify-prod-12345}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${GCP_SERVICE:-mojify}"
GCS_BUCKET="${GCS_BUCKET:-mojify-db}"

echo "=== Deploying Mojify to GCP Cloud Run (unified) ==="
echo "Project:    $PROJECT_ID"
echo "Region:     $REGION"
echo "Service:    $SERVICE_NAME"
echo "DB bucket:  gs://$GCS_BUCKET"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Project root (absolute path)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Build and deploy via cloudbuild.yaml (uses Docker cache + E2_HIGHCPU_8)
echo ">>> Building and deploying Mojify (backend + frontend)..."
cd "$PROJECT_ROOT"
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions="_GCS_BUCKET=$GCS_BUCKET" .

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format 'value(status.url)')

echo ""
echo "=== Deployment complete ==="
echo "URL: $SERVICE_URL"
echo ""
echo "Endpoints:"
echo "  App:      $SERVICE_URL"
echo "  skill.md: $SERVICE_URL/skill.md"
echo "  API:      $SERVICE_URL/api/"
echo ""

# Register the Telegram webhook automatically if the service is reachable
echo ">>> Registering Telegram webhook..."
SETUP_RESP=$(curl -sf "$SERVICE_URL/telegram/setup" 2>&1) && {
  echo "Telegram webhook registered: $SETUP_RESP"
} || {
  echo "(Skipped — service not reachable yet or TELEGRAM_BOT_TOKEN not set)"
  echo "Register manually after setting the token:"
  echo "  gcloud run services update $SERVICE_NAME --region $REGION --update-env-vars TELEGRAM_BOT_TOKEN=<token>"
  echo "  curl $SERVICE_URL/telegram/setup"
}
echo ""
echo "To set secrets (only needed once — persists across deploys):"
echo "  gcloud run services update $SERVICE_NAME --region $REGION \\"
echo "    --update-env-vars TELEGRAM_BOT_TOKEN=<token>,OPENAI_API_KEY=<key>"
echo ""
