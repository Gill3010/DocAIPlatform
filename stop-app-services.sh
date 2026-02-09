#!/bin/bash
# Stop backend, frontend, and collab to free RAM and reduce load (helps SSH stability)
pkill -9 -f "uvicorn backend.main" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
pkill -9 -f "node.*backend-collab/dist/server" 2>/dev/null || true
for port in 8000 5173 3001; do
  pid=$(lsof -ti :$port 2>/dev/null)
  [ -n "$pid" ] && kill -9 $pid 2>/dev/null || true
done
echo "App services stopped. Run ./run.sh when you need them again."
