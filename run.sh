#!/bin/bash
# DocAI Platform - Ejecutar proyecto completo (backend + frontend)
# Uso: ./run.sh   o   bash run.sh

cd "$(dirname "$0")"
# No usar set -e: pkill y curl pueden fallar sin que debamos salir

echo "🚀 DocAI Platform - Iniciando proyecto completo"
echo "==============================================="

# Detener servicios previos si existen (evita conflicto de puertos)
pkill -f "uvicorn backend.main" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# --- Backend (en segundo plano) ---
echo ""
echo "🔧 Iniciando Backend (FastAPI) en segundo plano..."
if [ ! -d backend/venv ]; then
  echo "📦 Creando entorno virtual y instalando dependencias del backend..."
  (cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt) || { echo "❌ Error al crear venv. Instala manualmente: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"; exit 1; }
fi
source backend/venv/bin/activate
export PYTHONPATH="${PWD}:${PYTHONPATH}"

[ -f backend/sql_app.db ] || { echo "🗄️  Inicializando BD..."; (cd backend && source venv/bin/activate && python init_db.py) 2>/dev/null || true; }

nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/docai-backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✓ Backend PID: $BACKEND_PID (logs: /tmp/docai-backend.log)"

# Esperar a que el backend responda
echo "   Esperando backend..."
BACKEND_OK=0
for i in $(seq 1 20); do
  if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health 2>/dev/null | grep -q 200; then
    BACKEND_OK=1
    break
  fi
  sleep 1
done
if [ "$BACKEND_OK" -eq 1 ]; then
  echo "   ✓ Backend listo en http://localhost:8000"
else
  echo "   ⚠ Backend no respondió en 20 s. Revisa: tail -30 /tmp/docai-backend.log"
  echo "   Continuando con el frontend..."
fi

# --- Frontend (en primer plano) ---
echo ""
echo "🎨 Iniciando Frontend (Vite)..."
[ -d frontend/node_modules ] || { echo "📦 Instalando deps..."; (cd frontend && npm install); }
echo "   ✓ Frontend en http://localhost:5173"
echo ""
echo "==============================================="
echo "   El proyecto ESTÁ CORRIENDO."
echo "   Abre en el navegador: http://localhost:5173"
echo "   IP pública: http://$(curl -s ifconfig.me 2>/dev/null || echo 'TU_IP'):5173"
echo ""
echo "   Este proceso debe quedar abierto. Ctrl+C detiene todo."
echo "==============================================="
echo ""

# Al terminar con Ctrl+C, matar también el backend
trap "kill $BACKEND_PID 2>/dev/null || true; echo ''; echo '👋 Frontend y backend detenidos.'; exit 0" INT TERM

(cd frontend && npm run dev -- --host)
