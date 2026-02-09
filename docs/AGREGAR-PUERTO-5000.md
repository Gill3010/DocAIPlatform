# Cómo agregar el puerto 5000 al Security Group

## Paso a paso en la consola de AWS

1. En la vista que tienes abierta (Security group rules), haz clic en **"Edit inbound rules"** (botón arriba a la derecha).

2. Clic en **"Add rule"**.

3. Configura la nueva regla:
   - **Type**: Custom TCP
   - **Port range**: 5000
   - **Source**: 
     - `0.0.0.0/0` (cualquier IP puede conectar al puerto 5000), o
     - Tu IP específica si quieres restringir (ej. `190.35.122.115/32`)
   - **Description**: Backend API (PM2)

4. Clic en **"Save rules"**.

5. Espera ~10 segundos y recarga `http://3.129.43.75:5173/login` en tu navegador. El error `ERR_CONNECTION_REFUSED` al puerto 5000 debería desaparecer.

---

## Alternativa: usar puerto 8000 en PM2

Si prefieres usar el puerto 8000 (que ya está abierto), puedes:

1. Cambiar `ecosystem.config.cjs` para que el backend use `--port 8000` en lugar de `--port 5000`.
2. Cambiar `frontend/.env` para que use `VITE_API_URL=http://3.129.43.75:8000`.
3. Reiniciar con PM2: `pm2 restart backend && pm2 restart frontend`.

Esto evita abrir un puerto nuevo, pero entonces tendrías backend en 8000 con PM2 y con run.sh (potencial conflicto).
