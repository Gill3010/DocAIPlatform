# Análisis de problemas de despliegue - DocAI Platform

## Resumen ejecutivo

Se han identificado **3 causas principales** que explican los errores observados:

1. **Desajuste de puertos**: PM2 arranca el backend en el puerto **5000**, pero el frontend siempre llama a **8000**
2. **Formato de sesión anónima inválido**: El fallback de `generateSessionId()` genera un valor que NO es UUID válido
3. **Configuración de inicio automático incompleta**: PM2 está activo pero con configuración incorrecta; además no está claro quién sirve el frontend en producción

---

## 1. Problema: Backend no arranca automáticamente en el puerto correcto

### Diagnóstico

| Componente | Puerto esperado | Puerto real (PM2) | Resultado |
|------------|-----------------|-------------------|-----------|
| Backend API | 8000 | **5000** (ecosystem.config.cjs) | ❌ Desajuste |
| Frontend | Servido por backend en 8000 | Vite dev en 5173 (PM2) | ❌ Inconsistente |

**Evidencia:**
- `ecosystem.config.cjs` línea 14: `--port 5000`
- `frontend/src/services/api/config.ts` línea 8: `window.location.hostname:8000`
- El usuario accede a `http://3.129.43.75:8000/dashboard` → el frontend construido espera API en `:8000`
- `run.sh` usa puerto 8000 y funciona porque coinciden

**Por qué funciona con `run.sh`:**
- `run.sh` mata procesos previos y arranca el backend en **8000**
- El backend sirve el frontend (desde `frontend/dist`) y la API en el mismo puerto 8000
- Todo está en el mismo origen; las llamadas API llegan al backend correctamente

**Por qué falla sin `run.sh`:**
- PM2 (systemd) ejecuta `pm2 resurrect` al arrancar
- El `ecosystem` guardado inicia el backend en **5000**
- El frontend (servido desde `frontend/dist` por el backend) se carga desde `:8000` cuando hay algo ahí
- Si no hay nada en 8000: no se carga nada, o nginx/otro proxy sirve estáticos pero las llamadas API fallan
- Si el usuario accede a `:5173` (Vite dev de PM2), el frontend llama a `hostname:8000` para la API → nada en 8000 → fallo

---

## 2. Problema: "Invalid X-Anonymous-Session-Id format"

### Diagnóstico

El backend exige que `X-Anonymous-Session-Id` sea un **UUID válido**:

```python
# backend/app/routers/convert.py
uuid.UUID(x_anonymous_session_id)  # Lanza ValueError si no es UUID
```

En el frontend, la generación tiene un **fallback no compatible**:

```typescript
// frontend/src/hooks/useAnonymousSession.ts
function generateSessionId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
```

- `crypto.randomUUID()` genera algo como `a1b2c3d4-e5f6-7890-abcd-ef1234567890` ✅
- El fallback genera algo como `1739257200000-x7k2m9p` ❌ (no es UUID)

Si `crypto.randomUUID` no existe (navegadores antiguos, algún entorno raro) o falla, el fallback se usa y el backend rechaza la petición con "Invalid X-Anonymous-Session-Id format".

**Otras causas posibles:**
- `localStorage` con un valor corrupto o vacío de una sesión anterior
- Acceso desde distintos orígenes/puertos que comparten/mezclan datos de sesión

---

## 3. Problema: "No quedan créditos. Regístrate para obtener más"

### Diagnóstico

En `AIAssistantFAB.tsx`:

```typescript
} catch (error) {
    console.error('Failed to load credits:', error);
    if (!token) setCredits(0);  // Cualquier fallo → créditos 0
}
```

Cuando falla la llamada a `getAICredits(sessionId)` por:
- Backend caído o en puerto incorrecto (5000 vs 8000)
- "Invalid X-Anonymous-Session-Id format"
- Error de red o CORS

… el frontend pone `credits = 0` y muestra "No quedan créditos. Regístrate para obtener más."

**Por qué mejora al ejecutar `run.sh` y hacer login:**
1. El backend pasa a estar en el puerto 8000 correcto
2. Tras el login se usa autenticación por token; ya no se depende de la sesión anónima
3. Las llamadas a `/users/me/stats` y créditos funcionan porque el backend está accesible

---

## 4. Soluciones paso a paso

### Solución A: Backend en el puerto correcto y arranque automático

**1. Corregir `ecosystem.config.cjs` para usar puerto 8000**

```javascript
// Cambiar en ecosystem.config.cjs, app 'backend':
args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
```

**2. Usar el mismo entorno virtual que `run.sh` (opcional pero recomendado)**

```javascript
// Si run.sh usa backend/venv:
script: '/home/ec2-user/backend/venv/bin/python',
```

O mantener `.venv-new` si ya está funcionando con las dependencias correctas.

**3. Ajustar la app "frontend" en PM2 para producción**

En producción lo más estable es **servir el frontend desde el backend** (archivos estáticos desde `frontend/dist`), no usar Vite en modo dev. Para eso:

- La app "frontend" en `ecosystem` puede **eliminarse** o deshabilitarse para producción
- El backend en 8000 ya monta `frontend/dist` y sirve el SPA

Si quieres seguir usando PM2 para el frontend en modo desarrollo:

```javascript
// En ecosystem, app frontend - asegurar que Vite use puerto adecuado
// y que VITE_API_URL apunte al backend (ej. :8000)
```

**4. Persistir la configuración de PM2**

```bash
cd /home/ec2-user
pm2 delete all
pm2 start ecosystem.config.cjs --only backend,backend-collab
# NO incluir frontend si el backend sirve frontend/dist
pm2 save
```

**5. Comprobar el arranque automático**

```bash
sudo systemctl status pm2-ec2-user
curl -s http://127.0.0.1:8000/health
```

---

### Solución B: Evitar "Invalid X-Anonymous-Session-Id format"

**1. Corregir el fallback en `useAnonymousSession.ts`**

Generar siempre un UUID válido:

```typescript
function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback que SÍ genera un UUID v4 válido
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
```

**2. Validar antes de enviar (opcional)**

En los servicios API (por ejemplo `ai.ts`, `convert.ts`), se puede validar que el ID tenga formato UUID antes de enviar el header, para evitar enviar datos inválidos.

---

### Solución C: Configuración estable en producción

**1. Servir frontend desde el backend (ya implementado)**

- El backend monta `frontend/dist` y sirve el SPA en `/`
- Esto evita depender de Vite en producción
- Asegurar que exista un build actualizado: `cd frontend && npm run build`

**2. Variable de entorno para la URL de la API (recomendado)**

Para poder cambiar el backend según entorno:

```bash
# En .env del frontend antes del build:
VITE_API_URL=http://3.129.43.75:8000
```

O, en despliegue dinámico, usar la misma base que la página:

```typescript
// config.ts - usar el mismo origen si la app se sirve desde el backend
const defaultBase = typeof window !== 'undefined'
  ? `${window.location.protocol}//${window.location.host}`
  : 'http://localhost:8000';
```

Así, si cargas `http://3.129.43.75:8000`, las peticiones API irán al mismo host/puerto.

**3. Systemd para PM2**

El servicio `pm2-ec2-user.service` ya está configurado. Solo falta que:

- `pm2 resurrect` restaure procesos con la configuración correcta
- Los procesos guardados usen puerto 8000

**4. Comprobaciones post-reinicio**

```bash
# Tras reiniciar la instancia:
curl -s http://127.0.0.1:8000/health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/dashboard
```

---

## 5. Checklist de implementación

| Paso | Acción |
|------|--------|
| 1 | Editar `ecosystem.config.cjs`: backend en puerto **8000** |
| 2 | Corregir `generateSessionId()` en `useAnonymousSession.ts` para generar siempre UUID válido |
| 3 | Opcional: deshabilitar/eliminar la app "frontend" de PM2 en producción |
| 4 | `pm2 delete all` → `pm2 start ecosystem.config.cjs --only backend,backend-collab` |
| 5 | `pm2 save` |
| 6 | `cd frontend && npm run build` (asegurar build actualizado) |
| 7 | Reiniciar y probar: `sudo reboot` o `pm2 restart all` |

---

## 6. Esquema del flujo objetivo

```
Usuario → http://3.129.43.75:8000/dashboard
                ↓
         Backend (uvicorn :8000)
                ↓
    ┌───────────┴───────────┐
    │                       │
  /api/v1/*             /* (SPA)
    │                       │
  FastAPI              frontend/dist
  (auth, convert,          (index.html + assets)
   ai, etc.)
```

- Un solo proceso (backend) en 8000 sirve API y frontend
- PM2 mantiene el backend vivo y lo reinicia si falla
- Systemd arranca PM2 al iniciar el servidor
