#!/bin/bash
# DocAI Platform - Ejecutar proyecto completo (backend + frontend + colaboración)
# Uso: ./run.sh   o   bash run.sh

cd "$(dirname "$0")"
# No usar set -e: pkill y curl pueden fallar sin que debamos salir

echo "🚀 DocAI Platform - Iniciando proyecto completo"
echo "==============================================="

# Detener servicios previos y liberar puertos 8000, 5173, 3001
echo "   Liberando puertos 8000, 5173 y 3001..."
pkill -9 -f "uvicorn backend.main" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
pkill -9 -f "backend-collab/dist/server" 2>/dev/null || true
for port in 8000 5173 3001; do
  pid=$(lsof -ti :$port 2>/dev/null)
  [ -n "$pid" ] && kill -9 $pid 2>/dev/null || true
done
# Limpiar logs antiguos
rm -f /tmp/docai-backend.log /tmp/docai-collab.log
sleep 3

# --- Backend (en segundo plano) ---
echo ""
echo "🔧 Iniciando Backend (FastAPI) en segundo plano..."
# Usar backend/venv (tiene las versiones correctas de bcrypt/passlib)
if [ -d backend/venv ] && [ -x backend/venv/bin/uvicorn ]; then
  BACKEND_VENV="${PWD}/backend/venv"
elif [ -x .venv-new/bin/uvicorn ]; then
  BACKEND_VENV="${PWD}/.venv-new"
else
  echo "📦 Creando entorno virtual y instalando dependencias del backend..."
  (cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt) || { echo "❌ Error al crear venv. Instala: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"; exit 1; }
  BACKEND_VENV="${PWD}/backend/venv"
fi
source "$BACKEND_VENV/bin/activate"
export PYTHONPATH="${PWD}:${PYTHONPATH}"

[ -f backend/sql_app.db ] || { echo "🗄️  Inicializando BD..."; (cd . && source "$BACKEND_VENV/bin/activate" && export PYTHONPATH="${PWD}:${PYTHONPATH}" && python backend/init_db.py) 2>/dev/null || true; }

echo "🗄️  Migraciones (freemium, avatar, ai_credits, admin_panel)..."
python backend/migrate_freemium.py 2>/dev/null || true
python backend/migrate_avatar.py 2>/dev/null || true
python backend/migrate_ai_credits.py 2>/dev/null || true
python backend/migrate_admin_panel.py 2>/dev/null || true
python backend/migrate_admin_audit.py 2>/dev/null || true

# Ruta absoluta al uvicorn (nohup no hereda el venv activado)
(cd backend && nohup "$BACKEND_VENV/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 > /tmp/docai-backend.log 2>&1 &)
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
  echo "   Continuando..."
fi

# --- Servidor de Colaboración (en segundo plano) ---
echo ""
echo "🤝 Iniciando Servidor de Colaboración (WebSocket)..."
if [ ! -d backend-collab/node_modules ]; then
  echo "📦 Instalando dependencias..."
  (cd backend-collab && npm install) || { echo "⚠ Error instalando deps de colaboración"; }
fi

if [ ! -f backend-collab/dist/server.js ]; then
  echo "📦 Compilando servidor..."
  (cd backend-collab && npm run build) || { echo "⚠ Error compilando servidor de colaboración"; }
fi

nohup node backend-collab/dist/server.js > /tmp/docai-collab.log 2>&1 &
COLLAB_PID=$!
echo "   ✓ Colaboración PID: $COLLAB_PID (logs: /tmp/docai-collab.log)"

# Esperar a que el servidor de colaboración responda
echo "   Esperando servidor de colaboración..."
COLLAB_OK=0
for i in $(seq 1 10); do
  if curl -s -o /dev/null http://127.0.0.1:3001/ 2>/dev/null; then
    COLLAB_OK=1
    break
  fi
  sleep 1
done
if [ "$COLLAB_OK" -eq 1 ]; then
  echo "   ✓ Colaboración lista en ws://localhost:3001"
else
  echo "   ⚠ Servidor de colaboración no respondió. Revisa: tail -30 /tmp/docai-collab.log"
fi

# --- Frontend (en primer plano) ---
echo ""
echo "🎨 Iniciando Frontend (Vite)..."
if [ ! -d frontend/node_modules ]; then
  if ! command -v make &>/dev/null; then
    echo "❌ Falta 'make' para compilar paquetes nativos (bufferutil). Instala con:"
    echo "   sudo dnf install -y make gcc-c++"
    exit 1
  fi
  echo "📦 Instalando deps (--legacy-peer-deps por conflicto TipTap)..."
  (cd frontend && npm install --legacy-peer-deps) || { echo "❌ Error instalando deps del frontend. Ejecuta: cd frontend && npm install --legacy-peer-deps"; exit 1; }
fi
echo "   ✓ Frontend en http://localhost:5173"
echo ""
echo "==============================================="
echo "   El proyecto ESTÁ CORRIENDO."
echo "   Abre en el navegador: http://localhost:5173"
echo "   IP pública: http://$(curl -s ifconfig.me 2>/dev/null || echo 'TU_IP'):5173"
echo ""
echo "   Servicios activos:"
echo "   • Backend FastAPI (PID: $BACKEND_PID)"
echo "   • Colaboración WebSocket (PID: $COLLAB_PID)"
echo "   • Frontend Vite (este proceso)"
echo ""
echo "   Este proceso debe quedar abierto. Ctrl+C detiene todo."
echo "   Para liberar memoria y estabilizar SSH: ./stop-app-services.sh"
echo "==============================================="
echo ""

# Al terminar con Ctrl+C, matar todos los servicios
trap "kill $BACKEND_PID $COLLAB_PID 2>/dev/null || true; echo ''; echo '👋 Todos los servicios detenidos.'; exit 0" INT TERM

(cd frontend && npx vite --host)
