# Resumen: ejecución en orden y qué hacer en cada caso

## 1. Si ejecuto `run.sh` – ¿qué hace o qué error da?

### Qué hace
- Libera puertos **8000**, **5173** y **3001** (mata procesos previos).
- Inicia el **backend** (FastAPI) en segundo plano en el puerto **8000**, usando `backend/venv` y `backend/requirements.txt`.
- Ejecuta migraciones (freemium, avatar, ai_credits, admin_panel, admin_audit).
- Inicia el **servidor de colaboración** (Node) en el puerto **3001**.
- Inicia el **frontend** (Vite) en **primer plano** en el puerto **5173** (el script se queda abierto hasta Ctrl+C).

### Errores que pueden aparecer
1. **Backend no responde**  
   - **Causa**: `run.sh` usaba `nohup uvicorn ...` sin ruta completa; en ese contexto `uvicorn` no estaba en el PATH (venv no aplicado a `nohup`).  
   - **Solución aplicada**: en `run.sh` se usa la ruta completa al ejecutable: `backend/venv/bin/uvicorn`.  
   - Si usas **Python 3.9** y `backend/venv` se creó con `requirements.txt` antiguo, puede fallar por dependencias. En ese caso crea un venv con Python 3.9 e instala con `pip install -r backend/requirements-py39.txt` y ajusta `run.sh` para usar ese venv (o usa PM2 con `.venv-new`).

2. **Frontend: `npm install` falla (ERESOLVE)**  
   - Conflicto de peers: `@tiptap/extension-collaboration-cursor@2.26.2` pide `@tiptap/core@^2.7.0` y el proyecto usa `@tiptap/core@3.19.0`.  
   - **Solución**: instalar con `npm install --legacy-peer-deps` en `frontend/`, o actualizar/cambiar la extensión de colaboración para que sea compatible con TipTap 3.

3. **Frontend: `vite: command not found`**  
   - Si `npm install` falló, `node_modules/.bin/vite` no existe.  
   - **Solución**: resolver el paso anterior (`--legacy-peer-deps` o dependencias compatibles) y volver a `npm install` y `npm run dev`.

---

## 2. Si ejecuto los servicios con PM2 – ¿cómo verifico que todo está bien?

### Cómo arrancar
```bash
# PM2 puede no estar en PATH; usar ruta completa si hace falta
export PATH="/usr/lib/nodejs18/lib/node_modules/pm2/bin:$PATH"
cd /home/ec2-user
mkdir -p logs
pm2 start ecosystem.config.cjs
```

### Comprobaciones
```bash
# Estado de los procesos
pm2 status

# Backend (puerto 5000 en ecosystem.config.cjs)
curl -s http://127.0.0.1:5000/health
# Esperado: {"status":"healthy"}

# Colaboración (puerto 3001)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001/
# Esperado: 200

# Logs
pm2 logs
pm2 logs backend --lines 50
```

### Nota sobre puertos
- **run.sh**: backend **8000**, frontend **5173**, collab **3001**.
- **ecosystem.config.cjs**: backend **5000**, collab **3001**, frontend (dev) **3000**.
Si quieres que `run.sh` y PM2 coincidan, cambia en `ecosystem.config.cjs` el puerto del backend a **8000** o adapta `run.sh` al **5000**.

---

## 3. Si ejecuto `pip install -r requirements-py39.txt` – ¿qué hago si falla?

### Ya probado
En este entorno `pip install -r backend/requirements-py39.txt` con el venv `.venv-new` (Python 3.9) **completó correctamente**.

### Si en tu máquina falla
1. **Error de versión de Python**  
   - Asegúrate de usar Python 3.9: `python --version` o `python3.9 --version`.  
   - Crea/activa el venv con ese intérprete: `python3.9 -m venv .venv-new && source .venv-new/bin/activate`.

2. **Paquete que pide Python ≥ 3.10 o 3.11**  
   - Instala primero las dependencias “problemáticas” con restricción explícita, luego el resto:
   ```bash
   pip install "numpy>=1.26,<2.4" "contourpy>=1.2,<1.3" "matplotlib>=3.8,<3.10" "click>=8.1,<8.2"
   pip install -r backend/requirements-py39.txt
   ```

3. **Error de compilación (ej. cffi, cryptography)**  
   - Instala herramientas de build:  
     `sudo dnf install -y python3-devel gcc libffi-devel` (Amazon Linux 2023).  
   - Vuelve a intentar el `pip install -r backend/requirements-py39.txt`.

4. **Conflicto entre paquetes**  
   - Prueba en un venv limpio:  
     `python3.9 -m venv .venv-new && source .venv-new/bin/activate`  
     `pip install --upgrade pip`  
     `pip install -r backend/requirements-py39.txt`

### Compatibilidad con Python 3.9
En el backend se añadió `from __future__ import annotations` y se sustituyó `str | None` / `User | None` por `Optional[str]` / `Optional[User]` en los **routers** (auth, ai, users) para que FastAPI/Pydantic no fallen al evaluar anotaciones en Python 3.9. Si añades más rutas con anotaciones con `|`, usa `Optional[...]` o `Union[...]` en los parámetros que FastAPI inspecciona.

---

## Resumen rápido

| Acción              | Resultado / qué hacer |
|---------------------|------------------------|
| **run.sh**          | Backend 8000, collab 3001, frontend 5173. Corregido uso de `uvicorn` con ruta completa. Si falla frontend: `npm install --legacy-peer-deps` en `frontend/`. |
| **PM2**             | Backend 5000, collab 3001, frontend (dev) 3000. Verificar con `pm2 status`, `curl localhost:5000/health` y `curl localhost:3001/`. |
| **pip requirements-py39.txt** | En las pruebas instaló bien. Si falla: venv con Python 3.9, deps conflictivas a mano, o instalar paquetes de desarrollo del SO. |
