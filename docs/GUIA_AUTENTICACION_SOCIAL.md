# Guía de Integración: Inicio de Sesión con Google y Facebook

**DocAI Platform** | Arquitectura y UX/UI para autenticación social

---

## Índice

1. [Seguridad y autenticación](#1-seguridad-y-autenticación)
2. [Experiencia de usuario (UX)](#2-experiencia-de-usuario-ux)
3. [Flujo Login vs Registro](#3-flujo-login-vs-registro)
4. [Integración técnica](#4-integración-técnica)
5. [Accesibilidad y cumplimiento](#5-accesibilidad-y-cumplimiento)
6. [Errores comunes a evitar](#6-errores-comunes-a-evitar)
7. [Plan de implementación recomendado](#7-plan-de-implementación-recomendado)

---

## 1. Seguridad y autenticación

### 1.1 Flujo OAuth 2.0 recomendado

**Enfoque recomendado: Backend (Authorization Code + PKCE)**

```
[Frontend] → Inicia flujo con redirect a Google/Facebook
[Google/Facebook] → Usuario autoriza
[Google/Facebook] → Redirige a tu backend con code
[Backend] → Intercambia code por tokens
[Backend] → Verifica ID token, crea/actualiza usuario
[Backend] → Emite JWT propio (igual que login tradicional)
[Frontend] → Recibe JWT, misma experiencia que login con contraseña
```

**Por qué backend y no solo frontend:**

| Aspecto | Frontend only | Backend (recomendado) |
|---------|---------------|------------------------|
| Exposición de Client Secret | Imposible ocultar en SPA | Secret nunca sale del servidor |
| Validación de ID token | Compleja en cliente | Centralizada y segura |
| Unificación de sesiones | Dos flujos distintos | Un solo JWT para todo |
| Revocación | Difícil | Control total desde backend |
| CSRF | Más vulnerable | state/nonce en servidor |

### 1.2 Tokens: manejo seguro

| Token | Almacenar en | Expiración | Uso |
|-------|--------------|------------|-----|
| **JWT propio** | localStorage / httpOnly cookie | 30 min (actual) | Sesión de tu app |
| **Google/Facebook access_token** | ❌ No almacenar en frontend | N/A | Solo intercambio en backend |
| **Google/Facebook id_token** | ❌ No almacenar | 1h | Validar en backend, descartar |
| **Refresh token** | Backend only (si Google lo ofrece) | Largo | Renovar sin re-autenticar |

**Recomendación:** Mantén tu flujo actual de JWT. El backend intercambia el código OAuth por datos del usuario, crea/actualiza el usuario en BD, y devuelve tu JWT estándar. El frontend no necesita saber que el login fue social.

### 1.3 Protección contra amenazas

| Amenaza | Solución |
|---------|----------|
| **CSRF** | Usar `state` en OAuth (obligatorio en Google/Meta). Generar state aleatorio, guardar en sesión/cookie, validar en callback. |
| **Phishing** | No implementar "login con contraseña de Google" en tu dominio. Siempre redirect a accounts.google.com / facebook.com. |
| **Duplicación de cuentas** | Identificar usuarios por `email` + `auth_provider` (google/facebook/email). Una cuenta puede tener varios proveedores (ver sección 3). |
| **Token hijacking** | JWT de corta vida, considerar refresh token. Evitar pasar tokens sociales al frontend. |

### 1.4 Cambios en el modelo de datos

Tu modelo actual:
```python
# User actual
email, hashed_password, full_name
```

**Recomendación para soportar social login:**

```python
# Campos a añadir
auth_provider = Column(String)  # 'email' | 'google' | 'facebook'
provider_user_id = Column(String, nullable=True)  # ID del usuario en el proveedor
hashed_password = Column(String, nullable=True)   # Nullable para usuarios solo-social
```

- `auth_provider`: origen del registro/login.
- `provider_user_id`: para vincular con la cuenta del proveedor (evitar duplicados por cambio de email).
- `hashed_password`: nullable cuando el usuario solo usa login social.

---

## 2. Experiencia de usuario (UX)

### 2.1 Ubicación de los botones

**Recomendación: Social primero, formulario después**

```
┌─────────────────────────────────────────┐
│         Iniciar sesión / Crear cuenta   │
│                                         │
│  [  G  Continuar con Google      ]     │  ← Primero (más usado)
│                                         │
│  [  f  Continuar con Facebook    ]     │  ← Segundo
│                                         │
│  ─────────── o ───────────             │  ← Separador visual
│                                         │
│  Email o Usuario                        │
│  [_____________________________]        │
│                                         │
│  Contraseña                             │
│  [_____________________________]        │
│                                         │
│  [    Iniciar sesión / Crear cuenta  ]  │
└─────────────────────────────────────────┘
```

**Justificación:** Los usuarios que prefieren social lo hacen por rapidez. Ponerlo arriba reduce fricción y abandono. El separador "o" deja claro que hay dos caminos equivalentes.

### 2.2 Textos recomendados

| Acción | Texto recomendado | Evitar |
|--------|-------------------|--------|
| Botón Google | "Continuar con Google" | "Login con Google", "Sign in with Google" (en español) |
| Botón Facebook | "Continuar con Facebook" | "Login con Facebook", "Entrar con FB" |
| Separador | "o" o "o continúa con email" | "O bien", "Alternativamente" |

### 2.3 Estados de la interfaz

| Estado | Comportamiento | Feedback visual |
|--------|----------------|-----------------|
| **Cargando** | Deshabilitar botones social y formulario | Spinner en el botón clickeado o overlay suave |
| **Error** | Mensaje bajo el botón o en banner superior | Texto claro, icono de error |
| **Usuario cancela** | Volver a la pantalla sin error | No mostrar "Error": el usuario eligió salir |
| **Redirect en curso** | Botón pulsado, deshabilitar otros | "Redirigiendo a Google..." |

### 2.4 Casos edge: mensajes al usuario

| Situación | Mensaje recomendado |
|-----------|---------------------|
| Email ya registrado con contraseña | "Este email ya tiene cuenta. Inicia sesión con contraseña o vincula Google/Facebook en configuración." |
| Proveedor no devuelve email | "No pudimos obtener tu email. Usa registro con email o verifica los permisos en tu cuenta de Google/Facebook." |
| Usuario rechaza permisos | Volver a la pantalla sin mensaje de error (cancelación voluntaria). |
| Cuenta desactivada | "Tu cuenta está desactivada. Contacta con soporte." |

---

## 3. Flujo Login vs Registro

### 3.1 Un solo flujo: "Continuar con X"

No es necesario distinguir botones de "Login" vs "Registro" para social. Un solo botón:

- **Usuario nuevo** → Se crea la cuenta automáticamente.
- **Usuario existente** → Se inicia sesión directamente.

El backend decide según si el email ya existe.

### 3.2 Lógica en backend

```
Recibir datos de Google/Facebook (email, name, provider_user_id)
    ↓
¿Existe usuario con este email?
    ├─ SÍ → ¿Tiene auth_provider = este proveedor o 'email'?
    │         ├─ SÍ → Login (emitir JWT)
    │         └─ NO → ¿Quieres vincular? (ver 3.4)
    └─ NO → Crear cuenta (auth_provider = google/facebook)
             → Emitir JWT
```

### 3.3 Vinculación de cuentas

Si el usuario tiene cuenta con **email+contraseña** y luego hace "Continuar con Google" con el mismo email:

**Opción A (simple):** Login directo. Asumir que es el mismo usuario.

**Opción B (más segura):** Mostrar modal:
> "Ya tienes una cuenta con este email. ¿Quieres vincular tu cuenta de Google para poder iniciar sesión de ambas formas?"
> [Vincular] [Cancelar]

La opción A es suficiente para la mayoría de productos. La B es recomendable si manejan datos sensibles.

### 3.4 Mensajes claros durante el flujo

| Momento | Mensaje (ejemplo) |
|---------|-------------------|
| Al hacer clic en Google | "Redirigiendo a Google..." (tooltip o estado del botón) |
| Al volver del proveedor | Sin mensaje; el backend procesa y redirige al dashboard. |
| Si es registro nuevo | Opcional: toast "¡Bienvenido! Tu cuenta se ha creado." |
| Si es login | Sin mensaje; redirección directa al dashboard. |

---

## 4. Integración técnica

### 4.1 Comparativa de enfoques

| Enfoque | Pros | Contras | Recomendación |
|---------|------|---------|---------------|
| **SDKs oficiales (Google Identity, FB SDK)** | Actualizados, soporte oficial | Más peso, dependencias | ✅ Para frontend |
| **Librerías (e.g. react-oauth2)** | Abstracción, menos código | Dependencia externa, posible obsolescencia | ⚠️ Solo si ahorra mucho trabajo |
| **Implementación manual OAuth** | Control total | Más código, mantenimiento | ❌ Solo si tienes requisitos muy específicos |

### 4.2 Recomendación para tu SPA (React + Vite)

**Frontend:**
- **Google:** [@react-oauth/google](https://www.npmjs.com/package/@react-oauth/google) o el script oficial de Google Identity Services.
- **Facebook:** [Facebook SDK for JavaScript](https://developers.facebook.com/docs/javascript) (script) o [react-facebook-login](https://github.com/keppelen/react-facebook-login) (más ligero pero menos mantenido).

**Backend (FastAPI):**
- Validar ID tokens con las librerías oficiales:
  - Google: `google-auth` (verificar `id_token`)
  - Facebook: `httpx` + llamada a `me?fields=id,email,name` con el access_token, o validar el token con el endpoint de debug de Facebook.

### 4.3 Flujo técnico resumido

**Google:**
1. Frontend: `GoogleOAuthProvider` + `useGoogleLogin` con `flow: 'auth-code'`.
2. Usuario autoriza → Google redirige a tu backend con `?code=...&state=...`.
3. Backend: intercambia `code` por `id_token` y `access_token`.
4. Backend: valida `id_token` con `google-auth`, extrae email y name.
5. Backend: crea/actualiza usuario, emite JWT, redirige a `/dashboard?token=XXX` o usa cookie.

**Facebook:**
1. Frontend: FB.login con `auth_type: 'rerequest'` si necesitas email.
2. Usuario autoriza → callback con `authResponse.accessToken`.
3. **Importante:** No enviar el token al frontend para uso prolongado. Enviar a tu backend.
4. Backend: `GET graph.facebook.com/me?fields=id,email,name&access_token=XXX`.
5. Backend: valida, crea/actualiza usuario, emite JWT.

### 4.4 Estrategias de fallback

| Fallo | Acción |
|-------|--------|
| Google/Facebook caído | Mostrar mensaje: "El inicio de sesión con [proveedor] no está disponible. Usa email y contraseña." |
| Timeout en redirect | Botón "Reintentar" o link "Volver al inicio de sesión". |
| Popup bloqueado (si usas popup) | Fallback a redirect en misma ventana. |
| Usuario sin cuenta de Google/FB | Siempre ofrecer formulario email/contraseña. |

### 4.5 Escalabilidad futura

- **Nuevos proveedores (Apple, GitHub, etc.):** Diseña un `AuthProvider` abstracto en backend; cada proveedor implementa `validate_token` y `get_user_info`.
- **Múltiples proveedores por usuario:** Tabla `user_oauth_accounts` con `user_id`, `provider`, `provider_user_id`.
- **Desvincular:** Permitir en "Configuración de cuenta" desvincular un proveedor si queda al menos uno (email o social).

---

## 5. Accesibilidad y cumplimiento

### 5.1 Accesibilidad (a11y)

| Requisito | Implementación |
|-----------|----------------|
| **Contraste** | Mínimo 4.5:1 para texto, 3:1 para iconos grandes (botones). |
| **Tamaño de área clicable** | Mínimo 44×44 px para botones. |
| **Focus visible** | `outline` o `box-shadow` en `:focus-visible`; no quitar focus outline. |
| **Lectores de pantalla** | `aria-label="Continuar con Google"` en el botón (el icono no es suficiente). |
| **Navegación por teclado** | Tab order lógico: Google → Facebook → Email → Contraseña → Enviar. |

Ejemplo de botón accesible:
```html
<button
  type="button"
  className="btn-social btn-google"
  onClick={handleGoogleLogin}
  aria-label="Continuar con Google"
  disabled={loading}
>
  <GoogleIcon aria-hidden="true" />
  Continuar con Google
</button>
```

### 5.2 Políticas de Google y Meta

**Google Identity Services:**
- Mostrar el botón con las [directrices de marca](https://developers.google.com/identity/branding-guidelines).
- Solicitar solo los scopes necesarios (`email`, `profile` para login básico).
- Incluir en tu Política de Privacidad el uso de datos de Google (qué recoges y para qué).

**Facebook Login:**
- Cumplir [Facebook Platform Terms](https://developers.facebook.com/terms/).
- No pedir permisos innecesarios; para login básico: `email`, `public_profile`.
- Mostrar el botón según [Brand Guidelines](https://developers.facebook.com/docs/facebook-login/web/login-button/#logininbutton).

### 5.3 Consideraciones legales

| Aspecto | Acción recomendada |
|---------|---------------------|
| **Consentimiento** | El consentimiento OAuth del proveedor cubre el uso de datos para autenticación. Aún así, mantén tu Política de Privacidad actualizada. |
| **Política de Privacidad** | Indicar: "Ofrecemos inicio de sesión con Google y Facebook. Recibimos tu email y nombre para crear y gestionar tu cuenta. Consulta nuestra Política de Privacidad." |
| **Uso de datos** | No usar datos del perfil social para marketing sin consentimiento adicional. |
| **Desuscripción** | Permitir eliminar cuenta y, si es posible, revocar acceso a la app en la cuenta de Google/Facebook. |

---

## 6. Errores comunes a evitar

| Error | Solución |
|-------|----------|
| Almacenar access_token de Google/FB en frontend | Usar solo en backend para obtener datos; luego emitir tu JWT. |
| No validar `state` en el callback | Siempre validar para prevenir CSRF. |
| Pedir demasiados scopes | Solo `email` y `profile`/`public_profile` para login. |
| Botones sin `aria-label` | Añadir descripción para lectores de pantalla. |
| Un solo método de login | Mantener siempre email+contraseña como alternativa. |
| Mensaje genérico "Error" | Usar mensajes específicos y accionables. |
| No manejar "usuario cancela" | No mostrar error; es una acción esperada. |
| Crear cuenta duplicada por mismo email | Unificar por email; `provider_user_id` como backup. |
| Olvidar el separador "o" | Aclarar visualmente que hay dos vías de acceso. |

---

## 7. Plan de implementación recomendado

### Fase 1: Backend (prioridad alta)
1. Añadir campos `auth_provider` y `provider_user_id` al modelo User.
2. Crear endpoint `POST /auth/google` que reciba `code` + `state`, valide, y devuelva JWT.
3. Crear endpoint `POST /auth/facebook` similar.
4. Hacer `hashed_password` nullable.
5. Migración de base de datos.

### Fase 2: Frontend (prioridad alta)
1. Integrar Google Identity (o @react-oauth/google).
2. Integrar Facebook SDK.
3. Añadir botones "Continuar con Google" y "Continuar con Facebook" arriba del formulario.
4. Implementar estados: loading, error, cancelación.
5. Redirigir al callback del backend con el código.

### Fase 3: UX y mensajes (prioridad media)
1. Mensajes específicos para cada caso edge.
2. Separador "o continúa con email".
3. Revisión de contraste y focus.

### Fase 4: Mejoras (prioridad baja)
1. Vinculación de cuentas en configuración.
2. Opción de desvincular proveedor.
3. Soporte para más proveedores (Apple, etc.).

---

## Referencias

- [Google Identity - OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login for the Web](https://developers.facebook.com/docs/facebook-login/web)
- [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [WCAG 2.1 - Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
