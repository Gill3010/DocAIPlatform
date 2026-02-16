# Análisis: Sistema de Autenticación con Verificación de Email y Recuperación de Contraseña

**Proyecto:** DocAI Platform  
**Fecha:** Febrero 2025  
**Contexto:** Implementar verificación de email, recuperación de contraseña y evaluar arquitectura AWS óptima.

---

## 1. Estado Actual del Sistema

### 1.1 Lo que ya funciona
- **Registro** con email/contraseña → usuario activo inmediato, JWT al instante
- **Login** con email/contraseña (bcrypt, JWT)
- **OAuth Google y Facebook** (flujo completo, state CSRF)
- **Cloudflare Turnstile** (CAPTCHA en registro/login)
- **Base de datos:** SQLite (modelo User en `users` table)
- **JWT:** HS256, expiración configurable (7 días por defecto)

### 1.2 Lo que falta implementar
1. **Verificación de email** tras registro → cuenta no verificada hasta confirmar
2. **Forgot password** → token temporal, correo con enlace, reset seguro
3. **Bloquear login** de cuentas no verificadas (solo email/password; Google/Facebook ya verifican)

---

## 2. Opciones de Arquitectura AWS

### Opción A: Amazon Cognito (Fully Managed)

**Servicios:** Amazon Cognito User Pools

**Pros:**
- Todo administrado: verificación de email, forgot password, MFA, hosted UI opcional
- Sin servidor de correo propio: Cognito usa SES internamente para verificaciones
- Alta seguridad: tokens, rate limiting, bloqueo tras intentos fallidos
- Escalabilidad ilimitada
- Integración nativa con API Gateway, Lambda, AppSync
- Cumple compliance (SOC2, HIPAA, etc.)
- **Free Tier:** 50,000 MAU (usuarios activos/mes) gratis permanentemente

**Contras:**
- **Migración compleja:** Tu sistema actual usa JWT propio + SQLite. Cognito maneja su propio user pool.
- **Dos fuentes de usuarios:** Usuarios email/password en Cognito; Google/Facebook podrían seguir en tu DB o migrar a Cognito Identity Pools (Federated Identity).
- **Acoplamiento:** Si quieres mantener usuarios en SQLite (conversiones, créditos, planes premium, `organization_id`, etc.), necesitas **sincronizar** Cognito ↔ tu DB.
- **Customización limitada:** Emails, flujos y mensajes son configurables pero dentro del modelo de Cognito.
- **Coste creciente:** Tras 50k MAU, ~$0.0055/MAU (p.ej. 100k usuarios ≈ $275/mes).

**Arquitectura sugerida con Cognito:**
```
[React] → [Cognito User Pool] ← verificación email, forgot password
       → [API Gateway / FastAPI] ← JWT de Cognito validado
       → [SQLite/RDS] ← datos de usuario, créditos, planes
```
- **Sync:** Tras login con Cognito (o federated), tu backend crea/actualiza usuario en SQLite por `email` y asocia créditos/premium.
- **Complejidad:** Media-alta por migración y sincronización.

---

### Opción B: Custom con Amazon SES + FastAPI + SQLite

**Servicios:** Amazon SES, FastAPI (ya existente), SQLite

**Pros:**
- **Mínima complejidad:** No introduces Lambda, DynamoDB ni API Gateway nuevos.
- **Un solo lugar de verdad:** Todos los usuarios (email, Google, Facebook) siguen en tu `users` table.
- **SES Free Tier:** 62,000 emails/mes gratis (desde EC2/Lambda en AWS).
- **Control total:** Diseño de emails, flujos, mensajes y lógica en tu código.
- **Integración simple:** Tu FastAPI actual ya está en EC2; añadir SES es una dependencia `boto3` y configuración.
- **Mantenimiento bajo:** Un flujo más en el mismo backend.

**Contras:**
- Responsabilidad de implementar tokens seguros, expiración y rate limiting.
- SES requiere verificar dominio/email en sandbox antes de producción.

**Arquitectura:**
```
[React] → [FastAPI en EC2] → [SQLite]
                ↓
         [Amazon SES] → correos verificación + reset
```
- Tokens: guardados en tabla `email_verification_tokens` o `password_reset_tokens` (o columna en `users`).
- Sin Lambda, sin DynamoDB, sin API Gateway adicional.

---

### Opción C: Custom con Lambda + DynamoDB + API Gateway + SES

**Servicios:** Lambda, DynamoDB, API Gateway, SES

**Pros:**
- Serverless puro, escalado automático.
- DynamoDB para tokens con TTL nativo (expiración automática).

**Contras:**
- **Alta complejidad:** Nuevos servicios, nuevas cuentas, permisos IAM, deployments.
- **Dos bases de datos:** SQLite para usuarios/créditos + DynamoDB para tokens (o migrar todo).
- **Mantenimiento elevado:** Más piezas que monitorear y configurar.
- **Overkill** para un proyecto con tráfico moderado y Free Tier como objetivo.

---

## 3. Comparativa Resumida

| Criterio           | Cognito              | Custom SES + FastAPI   | Lambda + DynamoDB + SES |
|--------------------|----------------------|------------------------|-------------------------|
| **Complejidad**    | Media-Alta           | Baja                   | Alta                    |
| **Mantenimiento**  | Bajo                 | Bajo                   | Medio-Alto              |
| **Migración**      | Sí (importante)      | No (extender actual)   | Sí                      |
| **Free Tier**      | 50k MAU              | SES 62k emails         | Lambda 1M invocaciones  |
| **Seguridad**      | Muy alta             | Alta (si se implementa)| Alta                    |
| **Escalabilidad**  | Excelente            | Buena (SQLite → RDS)   | Excelente               |
| **Control**        | Limitado             | Total                  | Total                   |
| **Afectar lo actual** | Sí (cambios grandes) | Mínimo                 | Sí                      |

---

## 4. Recomendación Final: Opción B (Custom SES + FastAPI)

Para DocAI Platform, que busca **reducir mantenimiento**, **optimizar Free Tier** y **no afectar lo que ya funciona**:

### Por qué Opción B

1. **No migras usuarios:** Google y Facebook siguen igual; solo extiendes el flujo de email/password.
2. **SES encaja:** 62k emails/mes gratis, suficiente para verificación + reset de contraseña.
3. **Un solo backend:** Toda la lógica en FastAPI; sin Lambda ni DynamoDB nuevos.
4. **Implementación acotada:** 2–3 tablas nuevas, 4–6 endpoints, plantillas de email.
5. **Seguridad manejable:** Tokens aleatorios (no JWT para reset), expiración, rate limiting con dependencias ya usadas o simples middlewares.
6. **Escalabilidad futura:** Si creces, migrar SQLite a RDS es más sencillo que introducir Cognito o serverless.

### Cuándo reconsiderar Cognito

- Si planeas **migrar completamente** a Cognito (todos los usuarios) y reescribir auth.
- Si necesitas **MFA, social federation centralizada** y no quieres mantener código de auth.
- Si superas **50k MAU** y el coste de Cognito sigue siendo aceptable vs. desarrollo custom.

---

## 5. Diseño Técnico Recomendado (Opción B)

### 5.1 Modelo de datos (SQLite)

```sql
-- Nueva columna en users
ALTER TABLE users ADD COLUMN email_verified_at DATETIME NULL;

-- Nueva tabla para tokens de verificación y reset
CREATE TABLE auth_tokens (
    id INTEGER PRIMARY KEY,
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- SHA256 del token enviado
    user_id INTEGER NOT NULL REFERENCES users(id),
    purpose VARCHAR(32) NOT NULL,  -- 'email_verification' | 'password_reset'
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_auth_tokens_token ON auth_tokens(token_hash);
CREATE INDEX idx_auth_tokens_user_purpose ON auth_tokens(user_id, purpose);
```

- **email_verified_at:** NULL = no verificado; valor = fecha de verificación.
- **auth_tokens:** Un registro por token; `token_hash` para no guardar el token plano.
- **purpose:** Distingue verificación de email vs. reset de contraseña.

### 5.2 Tokens: JWT vs. Tokens aleatorios

| Uso                    | Recomendación        | Motivo                                             |
|------------------------|----------------------|----------------------------------------------------|
| **Access token (login)** | JWT (actual)         | Stateless, ya lo usas, bien para sesiones           |
| **Verificación email**  | Token aleatorio     | Un solo uso, corto, no necesita claims complejos   |
| **Reset contraseña**    | Token aleatorio     | Un solo uso, invalidar tras uso, no en URL larga   |

**Tokens aleatorios:**
- `secrets.token_urlsafe(32)` → ~43 caracteres, seguro para URL.
- Se guarda `SHA256(token)` en DB; el valor plano se envía solo por email.
- Un solo uso: al verificar/resetear, se marca `used_at` y no se reutiliza.

### 5.3 Flujos

#### Registro con verificación
1. Usuario se registra → se crea usuario con `email_verified_at = NULL`.
2. Se genera token de verificación, se guarda hash en `auth_tokens`.
3. Se envía email con enlace: `{FRONTEND}/auth/verify-email?token=...`
4. No se devuelve JWT (o se devuelve JWT con flag `email_verified: false`).
5. Frontend puede mostrar “Revisa tu correo para activar la cuenta”.
6. Al hacer clic en el enlace → `GET/POST /auth/verify-email?token=...` → valida token, actualiza `email_verified_at`, invalida token.
7. A partir de ahí, login normal funciona.

**Opcional:** Permitir login con cuenta no verificada pero limitar acciones (ej. no convertir hasta verificar). Para simplicidad, se puede bloquear login hasta verificar.

#### Recuperación de contraseña
1. Usuario pide "Olvidé mi contraseña" → `POST /auth/forgot-password` con `email`.
2. Si el email existe (y es auth_provider=email): generar token, guardar hash, enviar correo con enlace.
3. Siempre devolver "Si el email existe, recibirás un correo" (evitar enumeración).
4. Enlace: `{FRONTEND}/auth/reset-password?token=...`
5. `POST /auth/reset-password` con `token` + `new_password` → validar token, actualizar contraseña, invalidar token.
6. Usuario inicia sesión con la nueva contraseña.

### 5.4 Amazon SES - Configuración

**Desarrollo/Sandbox:**
- Verificar emails de prueba (desarrolladores).
- Solo enviar a direcciones verificadas.

**Producción:**
- Verificar dominio (ej. `docaiplatform.com`) en SES.
- Configurar DKIM para mejor deliverability.
- Usar región cercana (ej. `us-east-2` si la app está en Ohio).

**Integración en FastAPI:**
```python
# requirements: boto3
import boto3
from app.core.config import settings

def send_email_via_ses(to: str, subject: str, html_body: str, text_body: str = None):
    client = boto3.client('ses', region_name=settings.AWS_REGION)
    client.send_email(
        Source=settings.SES_FROM_EMAIL,
        Destination={'ToAddresses': [to]},
        Message={
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                'Text': {'Data': text_body or subject, 'Charset': 'UTF-8'},
            }
        }
    )
```

### 5.5 Seguridad

| Aspecto            | Implementación                                                |
|--------------------|---------------------------------------------------------------|
| **Hashing contraseña** | bcrypt (actual)                                             |
| **Token reset**    | `secrets.token_urlsafe(32)`, guardar SHA256                  |
| **Expiración**     | Verificación: 24h; Reset: 1h                                 |
| **Un solo uso**    | Marcar `used_at` al consumir                                 |
| **Rate limiting**  | 5 solicitudes/15min por IP para `/forgot-password`           |
| **Enumeración**     | Mismo mensaje si el email existe o no en forgot-password     |

### 5.6 Rate limiting

- Opción 1: **slowapi** (wrapper de limits para FastAPI).
- Opción 2: **Redis** si ya lo usas (o planeas usarlo).
- Opción 3: **In-memory** por IP (simple, suficiente para un solo proceso).

Para Free Tier y una sola instancia, in-memory o slowapi sin Redis es suficiente.

### 5.7 Políticas de expiración recomendadas

| Token               | Duración  | Motivo                          |
|---------------------|-----------|----------------------------------|
| **Email verification** | 24 horas | Dar tiempo sin ser excesivo      |
| **Password reset**     | 1 hora   | Acortar ventana de riesgo       |
| **JWT access**         | 7 días   | Ya configurado                  |

---

## 6. Plan de Implementación (No destructivo)

### Fase 1: Infraestructura
1. Configurar SES (verificar dominio en producción).
2. Añadir variables: `SES_FROM_EMAIL`, `AWS_REGION` (ya existe).
3. Crear módulo `app/services/email_service.py` con `send_verification_email`, `send_password_reset_email`.

### Fase 2: Base de datos
1. Añadir `email_verified_at` a `User` (nullable).
2. Crear modelo `AuthToken` y migración/tabla `auth_tokens`.
3. Usuarios existentes: `email_verified_at = created_at` (considerar verificados) o NULL si quieres forzar re-verificación.

### Fase 3: Backend
1. **Registro:** Generar token, guardar, enviar email, no dar JWT (o JWT con restricciones).
2. **GET/POST /auth/verify-email:** Validar token, actualizar `email_verified_at`, invalidar token.
3. **POST /auth/forgot-password:** Validar email, generar token, enviar correo, mismo mensaje siempre.
4. **POST /auth/reset-password:** Validar token + nueva contraseña, actualizar, invalidar token.
5. **Login:** Rechazar si `auth_provider=email` y `email_verified_at IS NULL`.
6. Rate limiting en `forgot-password`.

### Fase 4: Frontend
1. Página `/auth/verify-email?token=...` que llama al backend y redirige a login.
2. Página `/auth/forgot-password` con formulario de email.
3. Página `/auth/reset-password?token=...` con formulario de nueva contraseña.
4. Mensajes en LoginForm: "Revisa tu correo" tras registro; enlace "¿Olvidaste tu contraseña?".

### Fase 5: OAuth (sin cambios)
- Google y Facebook: los usuarios se crean con `email_verified_at = now()` o se consideran verificados por el proveedor.

---

## 7. Costos Free Tier (AWS)

| Servicio   | Free Tier                         | Uso estimado DocAI          |
|------------|------------------------------------|-----------------------------|
| **SES**    | 62,000 emails/mes (desde EC2)      | Verificación + reset << 1k  |
| **EC2**    | Ya en uso                          | -                           |
| **Cognito**| 50,000 MAU                         | No aplica (Opción B)        |
| **Lambda** | 1M solicitudes/mes                 | No aplica (Opción B)        |

Con Opción B, el coste adicional por emails será **$0** dentro del Free Tier.

---

## 8. Checklist Pre-producción

- [ ] Dominio verificado en SES
- [ ] DKIM configurado para el dominio
- [ ] `SES_FROM_EMAIL` con dominio verificado
- [ ] Rate limiting en `/forgot-password`
- [ ] Logs de envío (sin datos sensibles)
- [ ] Plantillas de email en HTML responsive
- [ ] Pruebas E2E de flujo completo

---

## 9. Resumen Ejecutivo

| Decisión            | Valor                                       |
|---------------------|---------------------------------------------|
| **Arquitectura**    | Custom con Amazon SES + FastAPI + SQLite   |
| **Verificación**    | Token aleatorio, 24h, un solo uso          |
| **Reset password**  | Token aleatorio, 1h, un solo uso           |
| **Emails**          | Amazon SES (62k/mes gratis)                 |
| **Migración**       | Mínima; extendemos el sistema actual        |

**Siguiente paso:** Implementar Fase 1–5 siguiendo este diseño, sin tocar los flujos de Google y Facebook.
