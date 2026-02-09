# Security Group y variables de entorno – Migración AL2023

## 1. Variables de entorno (.env)

### Backend (`backend/.env`)
- **Ya existe** en este servidor. Revisa que estén definidos:
  - `SECRET_KEY`: valor fuerte en producción (ej. `openssl rand -hex 32`)
  - `FRONTEND_URL`: URL del frontend en producción (ej. `https://tu-dominio.com` o `http://TU_IP:5173`)
  - `OPENAI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FACEBOOK_*` si usas esas funciones
  - `SUPERADMIN_EMAILS`: emails separados por coma para superadmin
- Referencia: `backend/.env.example`

### Backend-collab (`backend-collab/.env`)
- **Creado** con valores mínimos:
  - `PORT=3001` (debe coincidir con el proxy en el backend)
  - `JWT_SECRET_KEY`: debe ser el **mismo** que `SECRET_KEY` del backend si usas JWT para el collab
- En producción cambia `JWT_SECRET_KEY` por un valor seguro y consistente con el backend.
- Referencia: `backend-collab/.env.example` (incluye opcionales Redis/PostgreSQL si los usas).

### Frontend
- Si el frontend necesita API URL u otras variables, crea `frontend/.env` (o `.env.production` para el build). Referencia: `frontend/.env.example`.

---

## 2. Security Group de AWS – Puertos a abrir

**Importante:** Si el frontend muestra "Failed to fetch" o `ERR_CONNECTION_REFUSED` en la consola del navegador, casi siempre es porque el **backend no es accesible desde tu navegador**. El frontend está configurado con `VITE_API_URL=http://TU_IP:5000`; las peticiones van desde tu PC al puerto **5000** de la instancia. Si el Security Group **no** permite entrada en el puerto 5000, la conexión se rechaza y verás ese error. **Abre el puerto 5000** en el Security Group para que el login y la API funcionen.

Para acceder a la aplicación desde internet, en la consola de AWS (EC2 → Security Groups → tu grupo):

| Tipo        | Puerto | Origen (ejemplo)     | Descripción              |
|------------|--------|----------------------|--------------------------|
| Custom TCP | **5000** | 0.0.0.0/0 o tu IP   | Backend (API) – PM2      |
| Custom TCP | **3001** | 0.0.0.0/0 o tu IP   | Colaboración WebSocket   |
| Custom TCP | **5173** | 0.0.0.0/0 o tu IP   | Frontend (Vite dev)       |
| Custom TCP | **8000** | 0.0.0.0/0 o tu IP   | Backend si usas `run.sh` (puerto 8000) |

- Si solo usas **PM2**: abre **5000**, **3001**, **5173** (o el puerto que use tu frontend en producción).
- Si usas **run.sh** para el backend: abre **8000** en lugar de 5000 (o además de 5000).
- **SSH (22)** debe estar abierto para tu IP o tu bastión.

Pasos en consola AWS:
1. EC2 → Instances → selecciona la instancia → pestaña Security.
2. Clic en el Security Group asociado.
3. Edit inbound rules → Add rule:
   - Type: Custom TCP, Port: 5000, Source: 0.0.0.0/0 (o restringe a tu IP).
   - Repite para 3001, 5173 (y 8000 si aplica).
4. Save.

---

## 3. PM2 – Arranque automático

- **pm2 save**: ya ejecutado; la lista actual se guarda en `~/.pm2/dump.pm2`.
- **pm2 startup**: ya configurado (systemd, usuario `ec2-user`). Tras un reinicio de la instancia, PM2 levantará los 3 servicios automáticamente.

Para comprobar tras un reinicio:
```bash
export PATH="/usr/lib/nodejs18/lib/node_modules/pm2/bin:$PATH"
pm2 status
curl -s http://127.0.0.1:5000/health
```
