# Deploy Mojify to Google Cloud Platform (Cloud Run)

**Unified deployment**: One URL for both frontend and backend. Endpoints like `/skill.md`, `/api/`, `/claim/...` all live at the same base URL.

## Prerequisites

1. **Google Cloud account** — [console.cloud.google.com](https://console.cloud.google.com)
2. **gcloud CLI** — [Install guide](https://cloud.google.com/sdk/docs/install)
3. **Billing** — Cloud Run requires a billing account (free tier: 2M requests/month)

## One-time setup

```bash
# Login
gcloud auth login

# Create or select project
gcloud projects create mojify-prod --name="Mojify"  # or use existing
gcloud config set project mojify-prod

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## Deploy (option 1: Script)

```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1

chmod +x scripts/deploy-gcp.sh
./scripts/deploy-gcp.sh
```

## Deploy (option 2: Cloud Build)

```bash
gcloud builds submit --config=cloudbuild.yaml
```

Uses Docker layer caching and E2_HIGHCPU_8 for faster builds (especially on repeat deploys).

## Deploy (option 3: Manual)

From project root:

```bash
gcloud run deploy mojify \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=mojify.db

# Set base URL (same for frontend + backend)
URL=$(gcloud run services describe mojify --region us-central1 --format='value(status.url)')
gcloud run services update mojify --region us-central1 \
  --update-env-vars APP_URL=$URL,FRONTEND_URL=$URL
```

## Environment variables

Set via Cloud Run:

```bash
gcloud run services update mojify --region us-central1 \
  --update-env-vars OPENAI_API_KEY=sk-...,TELEGRAM_BOT_TOKEN=...
```

Or in Cloud Console: Cloud Run → mojify → Edit & Deploy → Variables.

## Endpoints (single URL)

| Path | Description |
|------|-------------|
| `/` | Frontend app |
| `/claim/{token}` | Claim agent page |
| `/skill.md` | Agent skill docs |
| `/heartbeat.md` | Agent heartbeat |
| `/skill.json` | Agent metadata |
| `/api/` | REST API |

## Notes

- **SQLite**: Data is ephemeral — resets on new instances. For persistent data, use Cloud SQL (PostgreSQL) or Cloud Storage.
- **Custom domain**: Cloud Run → Manage custom domains
- **Costs**: Free tier covers ~2M requests/month. Monitor in [Billing](https://console.cloud.google.com/billing)
