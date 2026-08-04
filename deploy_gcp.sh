#!/usr/bin/env bash
# ==============================================================================
# PyMorph AI - GCP Cloud Run Automated Deployment Script
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GCLOUD_BIN="${SCRIPT_DIR}/google-cloud-sdk/bin/gcloud"

if [ ! -f "$GCLOUD_BIN" ]; then
    GCLOUD_BIN="gcloud"
fi

echo "🚀 Starting PyMorph AI Google Cloud Run deployment..."

# Check if logged in
ACTIVE_ACCOUNT=$("$GCLOUD_BIN" config get-value account 2>/dev/null || true)
if [ -z "$ACTIVE_ACCOUNT" ] || [ "$ACTIVE_ACCOUNT" = "(unset)" ]; then
    echo "🔐 Logging into Google Cloud..."
    "$GCLOUD_BIN" auth login
fi

# Check project ID
PROJECT_ID=$("$GCLOUD_BIN" config get-value project 2>/dev/null || true)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "📋 Please enter your GCP Project ID:"
    read -r PROJECT_ID
    "$GCLOUD_BIN" config set project "$PROJECT_ID"
fi

echo "📦 Enabling required GCP APIs (Cloud Run, Cloud Build, Artifact Registry)..."
"$GCLOUD_BIN" services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# Extract Gemini API Key from backend/.env if available
GEMINI_KEY=""
if [ -f "${SCRIPT_DIR}/backend/.env" ]; then
    GEMINI_KEY=$(grep -E '^GEMINI_API_KEY=' "${SCRIPT_DIR}/backend/.env" | cut -d '=' -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "$GEMINI_KEY" ]; then
    GEMINI_KEY="your_gemini_api_key_here"
fi

echo "⚡ Deploying PyMorph AI to Google Cloud Run..."
"$GCLOUD_BIN" run deploy pymorph-ai \
    --source "${SCRIPT_DIR}" \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 7860 \
    --memory 1Gi \
    --cpu 1 \
    --set-env-vars GEMINI_API_KEY="${GEMINI_KEY}"

echo "🎉 Deployment complete!"
