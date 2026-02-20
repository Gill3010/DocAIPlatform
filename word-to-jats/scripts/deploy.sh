#!/bin/bash
# Deploy de la infraestructura Word-to-JATS
set -e
cd "$(dirname "$0")/.."
echo "=== Word-to-JATS Platform - Deploy ==="

# Crear venv si no existe
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

pip install -q -r requirements.txt
pip install -q aws-cdk-lib constructs

export CDK_DEFAULT_ACCOUNT="${CDK_DEFAULT_ACCOUNT:-$(aws sts get-caller-identity --query Account --output text)}"
export CDK_DEFAULT_REGION="${CDK_DEFAULT_REGION:-us-east-1}"

cdk synth
cdk deploy --require-approval never

echo "=== Deploy completado ==="
