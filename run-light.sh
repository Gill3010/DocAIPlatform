#!/bin/bash
# Solo backend - menos RAM, SSH mas estable
cd "$(dirname "$0")"
pkill -9 -f "uvicorn backend.main" 2>/dev/null || true
sleep 2
source backend/venv/bin/activate
export PYTHONPATH="${PWD}:${PYTHONPATH}"
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/docai-backend.log 2>&1 &
echo "Backend solo en puerto 8000. Para parar: ./stop-app-services.sh"
