#!/bin/bash
# Ejecutar DocAI Platform
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || { echo "Ejecuta primero: ./deploy.sh"; exit 1; }
exec python3 src/docai_platform.py "$@"
