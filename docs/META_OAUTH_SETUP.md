# Configuración de Inicio de Sesión con Facebook (Meta)

## 1. Crear app en Meta for Developers

1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Inicia sesión y haz clic en **"Mis aplicaciones"**
3. Clic en **"Crear aplicación"** → elige **"Consumidor"** (o "Otros" si no ves esa opción)
4. Nombre de la app: `DocAI Platform` (o el que prefieras)
5. Correo de contacto y completa el formulario
6. Crea la app

## 2. Añadir producto "Facebook Login"

1. En el panel de tu app, busca **"Facebook Login"** o **"Inicio de sesión con Facebook"**
2. Clic en **"Configurar"**
3. Elige **"Web"** como plataforma

## 3. Configurar OAuth

1. Ve a **Configuración** → **Básica**
2. Anota el **ID de la aplicación** y el **Secreto de la aplicación** (clic en "Mostrar" para ver el secreto)

3. Ve a **Productos** → **Facebook Login** → **Configuración**
4. En **"URIs de redireccionamiento de OAuth válidos"**, añade:
   - `http://localhost:5173/auth/callback/facebook`
   - `http://localhost:5174/auth/callback/facebook` (si usas el puerto 5174)
   - Para producción: `https://tu-dominio.com/auth/callback/facebook`

5. En **"Dominios del cliente OAuth"** (si aplica), añade:
   - `localhost`
   - Tu dominio de producción

## 4. Solicitar permisos de email

1. Ve a **Facebook Login** → **Permisos y características**
2. Asegúrate de tener **email** y **public_profile** solicitados
3. El permiso `email` es necesario para obtener el correo del usuario

## 5. Configurar variables de entorno

Edita `backend/.env`:

```env
FACEBOOK_APP_ID=tu-app-id
FACEBOOK_APP_SECRET=tu-secreto-de-la-app
```

## 6. Modo desarrollo

- La app empieza en **modo desarrollo**
- Solo los **administradores**, **desarrolladores** y **probadores** de la app pueden iniciar sesión
- Añade usuarios de prueba en **Roles** → **Probadores** si necesitas que otros prueben

## 7. Reiniciar el backend

Después de añadir las variables, reinicia el servidor FastAPI para cargar la configuración.

---

**Nota:** Si Facebook no devuelve el email, el usuario puede tener el email oculto en su perfil. Pide que revise la visibilidad del email en su cuenta de Facebook.
