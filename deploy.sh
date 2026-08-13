#!/usr/bin/env bash
# Google Cloud Run へのデプロイスクリプト。
#
# 前提(README.md の「Google Cloud Runへのデプロイ」を参照して先に済ませておくこと):
#   - gcloud CLI でログイン済み (gcloud auth login)
#   - デプロイ先の GCP プロジェクトが作成済み・課金有効化済み
#   - Cloud Run / Cloud Build / Artifact Registry の API が有効化済み
#
# 使い方:
#   GCP_PROJECT_ID=your-project-id ./deploy.sh
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?環境変数 GCP_PROJECT_ID を設定してください (例: GCP_PROJECT_ID=xxx ./deploy.sh)}"
REGION="${GCP_REGION:-asia-northeast1}"
SERVICE_NAME="${GCP_SERVICE_NAME:-dazai-classifier}"

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --port 7860 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
