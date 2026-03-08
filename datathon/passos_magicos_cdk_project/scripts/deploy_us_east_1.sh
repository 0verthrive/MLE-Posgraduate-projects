#!/usr/bin/env bash
set -euo pipefail

ACCOUNT_ID="${1:-123456789012}"
PROJECT_NAME="${2:-passos-magicos}"
STAGE="${3:-dev}"
REGION="us-east-1"

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if ! command -v cdk >/dev/null 2>&1; then
  npm install -g aws-cdk
fi

aws sts get-caller-identity
cdk bootstrap "aws://${ACCOUNT_ID}/${REGION}"
cdk synth \
  -c project_name="${PROJECT_NAME}" \
  -c stage="${STAGE}" \
  -c account="${ACCOUNT_ID}" \
  -c region="${REGION}"

cdk deploy --all \
  -c project_name="${PROJECT_NAME}" \
  -c stage="${STAGE}" \
  -c account="${ACCOUNT_ID}" \
  -c region="${REGION}" \
  --require-approval never
