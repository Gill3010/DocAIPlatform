# Configuración de Inicio de Sesión con Google

## 1. Crear credenciales en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Activa la **API de Google+** (o "Google Identity") si se solicita
4. Ve a **APIs y servicios** → **Credenciales**
5. Clic en **Crear credenciales** → **ID de cliente OAuth**
6. Tipo de aplicación: **Aplicación web**
7. Nombre: `DocAI Platform` (o el que prefieras)
8. **URIs de redirección autorizados** (importante):
   - Desarrollo: `http://localhost:5173/auth/callback`
   - Producción: `https://tu-dominio.com/auth/callback`
9. Guarda y copia el **ID de cliente** y el **Secreto del cliente**

## 2. Configurar variables de entorno

Crea o edita `backend/.env`:

```env
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-secret
FRONTEND_URL=http://localhost:5173
```

Para producción, usa tu dominio real:

```env
FRONTEND_URL=https://tu-dominio.com
```

## 3. Reiniciar el backend

Después de añadir las variables, reinicia el servidor FastAPI para que cargue la configuración.

## 4. Verificar

1. Abre la aplicación en el navegador
2. En la pantalla de login debería aparecer el botón **"Continuar con Google"**
3. Al hacer clic, te redirige a Google para autorizar
4. Tras autorizar, vuelves a la app ya autenticado

---

**Nota:** Si no configuras las credenciales, el botón de Google no se mostrará y el login por email seguirá funcionando con normalidad.
