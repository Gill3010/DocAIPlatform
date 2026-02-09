# Plan de migración a Amazon Linux 2023

Migración de la aplicación web (Flask/FastAPI + React + colaboración) desde Ubuntu a EC2 con Amazon Linux 2023 y Python 3.9.25.

---

## 1. Resumen de compatibilidad Python 3.9

Se han ajustado dependencias que en el `requirements.txt` original exigen Python ≥3.11 o versiones no publicadas para 3.9:

| Paquete      | Original   | Ajuste para Python 3.9      | Motivo                          |
|-------------|------------|-----------------------------|----------------------------------|
| click       | 8.3.1      | 8.1.x (<8.2)                | 8.3.1 no disponible en PyPI     |
| contourpy   | 1.3.3      | 1.2.x (<1.3)                | 1.3.x requiere Python ≥3.11     |
| matplotlib  | 3.10.8     | 3.8.x–3.9.x (<3.10)         | 3.10 requiere Python ≥3.10       |
| numpy       | 2.4.1      | 1.26–2.3 (<2.4)             | 2.4 requiere Python ≥3.11        |

El archivo **`backend/requirements-py39.txt`** contiene todas las dependencias con rangos compatibles con Python 3.9.25.

---

## 2. Secuencia de instalación (paso a paso)

### 2.1 Preparación del entorno

```bash
cd /home/ec2-user

# Entorno virtual (si no existe)
python3.9 -m venv .venv-new
source .venv-new/bin/activate

# Confirmar Python
python --version   # debe ser 3.9.x
pip --version
```

### 2.2 Backend principal (Python)

```bash
cd /home/ec2-user
source .venv-new/bin/activate

# Instalar dependencias compatibles con Python 3.9
pip install --upgrade pip
pip install -r backend/requirements-py39.txt

# Si falla algún paquete, instalar en este orden (resolución manual):
# pip install "numpy>=1.26,<2.4" "contourpy>=1.2,<1.3" "matplotlib>=3.8,<3.10"
# pip install -r backend/requirements-py39.txt
```

### 2.3 Backend colaborativo (Node/TypeScript)

```bash
cd /home/ec2-user/backend-collab
npm ci
npm run build
```

### 2.4 Frontend (React/Vite)

```bash
cd /home/ec2-user/frontend
npm ci
npm run build
```

Para producción, el backend sirve el frontend desde `frontend/dist` (ya configurado en `backend/main.py`).

### 2.5 Variables de entorno

- **Backend**: copiar `backend/.env.example` a `backend/.env` y rellenar (base de datos, `SECRET_KEY`, OAuth, OpenAI, etc.).
- **Backend-collab**: copiar `backend-collab/.env.example` a `backend-collab/.env` y configurar `JWT_SECRET_KEY` (mismo valor que `SECRET_KEY` del backend si usas el mismo JWT).

---

## 3. Configuración de PM2

### 3.1 Crear directorio de logs

```bash
mkdir -p /home/ec2-user/logs
```

### 3.2 Arrancar los tres servicios

```bash
cd /home/ec2-user
pm2 start ecosystem.config.cjs
```

Comandos útiles:

```bash
pm2 status
pm2 logs
pm2 logs backend
pm2 restart all
pm2 stop all
```

### 3.3 Persistir tras reinicio

```bash
pm2 save
pm2 startup
# Ejecutar el comando que PM2 muestre (sudo env PATH=... pm2 startup systemd -u ec2-user --hp /home/ec2-user)
```

### 3.4 Puertos

| Servicio        | Puerto | Notas                          |
|-----------------|--------|---------------------------------|
| Backend (FastAPI) | 5000 | API y servicio del frontend (dist) |
| Backend-collab    | 3001 | WebSocket colaboración (Yjs)   |
| Frontend (dev)    | 3000 | Solo si usas `npm run dev`     |

En producción suele bastar con **backend** y **backend-collab**; el frontend se sirve desde el backend.

---

## 4. Verificación y troubleshooting

### 4.1 Comprobar que los servicios responden

```bash
# Backend
curl -s http://localhost:5000/health
# Esperado: {"status":"healthy"}

# Collab
curl -s http://localhost:3001
# Esperado: texto "Y-WebSocket Collaboration Server..."
```

### 4.2 Si el backend no arranca

```bash
# Probar manualmente
cd /home/ec2-user
source .venv-new/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 5000

# Revisar imports (ruta y módulo)
python -c "from backend.main import app; print('OK')"
```

### 4.3 Errores típicos de dependencias

- **`contourpy` requiere Python >=3.11**: usar `requirements-py39.txt` y asegurar `contourpy<1.3`.
- **`click 8.3.1` no encontrado**: en 3.9 usar `click>=8.1,<8.2` (incluido en `requirements-py39.txt`).
- **`numpy` / `matplotlib`**: mantener `numpy<2.4` y `matplotlib<3.10` en 3.9.

### 4.4 Collab no compila o no arranca

```bash
cd /home/ec2-user/backend-collab
npm run build
node dist/server.js
```

### 4.5 Logs

```bash
tail -f /home/ec2-user/logs/backend-err.log
tail -f /home/ec2-user/logs/collab-out.log
pm2 logs --lines 100
```

---

## 5. Resumen de archivos creados/modificados

| Archivo | Descripción |
|--------|-------------|
| `backend/requirements-py39.txt` | Dependencias Python compatibles con 3.9.25 |
| `ecosystem.config.cjs` | Configuración PM2 para backend, backend-collab y frontend |
| `docs/PLAN-MIGRACION-AL2023.md` | Este plan |

---

## 6. Orden recomendado en la migración

1. Crear/activar `.venv-new` con Python 3.9.
2. Instalar dependencias del backend con `backend/requirements-py39.txt`.
3. Probar el backend en manual: `uvicorn backend.main:app --port 5000`.
4. Configurar `backend/.env` y `backend-collab/.env`.
5. Instalar y compilar backend-collab y frontend (`npm ci` + `npm run build`).
6. Crear `logs`, arrancar con PM2 y ejecutar `pm2 save` y `pm2 startup`.
7. Verificar con `curl` y con el navegador contra el backend (puerto 5000).

Con esto la aplicación debería comportarse igual que en el servidor original, usando Python 3.9.25 en Amazon Linux 2023.
