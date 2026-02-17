# Configuración de SES para verificación de email y recuperación de contraseña

## Resumen

El sistema de verificación de email y recuperación de contraseña usa **Amazon SES** para enviar correos. Si SES no está configurado, los emails se registran en logs (modo desarrollo).

## Variables de entorno

Añadir al `.env` del backend:

```env
# Amazon SES
SES_FROM_EMAIL=noreply@docaiplatform.com
SES_ENABLED=true

# Ya existente - debe coincidir con tu dominio
FRONTEND_URL=https://docaiplatform.com
AWS_REGION=us-east-2
```

## Pasos en AWS

### 1. Verificar dominio en SES

1. Ir a **Amazon SES** → **Verified identities**
2. Crear identidad → **Domain**
3. Dominio: `docaiplatform.com`
4. Seguir pasos para configurar registros DNS (DKIM, etc.)

### 2. Sandbox (desarrollo)

En sandbox, SES solo envía a direcciones de email verificadas:

1. **Identities** → **Create identity** → **Email address**
2. Verificar el email de pruebas (ej. tu correo personal)

### 3. Solicitar salida de Sandbox (producción)

Para enviar a cualquier email en producción:

1. **Account dashboard** → **Request production access**
2. Completar el formulario (tipo de emails, volumen estimado, etc.)

### 4. Permisos IAM (si la app corre en EC2 con rol IAM)

El rol de la instancia EC2 debe tener:

```json
{
  "Effect": "Allow",
  "Action": ["ses:SendEmail", "ses:SendRawEmail"],
  "Resource": "*"
}
```

## Flujos implementados

| Flujo | Endpoint | Descripción |
|-------|----------|-------------|
| Registro | POST /auth/register | Crea usuario, envía email de verificación, no da JWT hasta verificar |
| Verificación | POST /auth/verify-email | Valida token, marca usuario verificado |
| Olvidé contraseña | POST /auth/forgot-password | Envía email con enlace (rate limit: 5/15min por IP) |
| Restablecer | POST /auth/reset-password | Valida token, actualiza contraseña |

## Desarrollo sin SES

Si `SES_ENABLED` es false o `SES_FROM_EMAIL` está vacío, el backend **no envía** emails pero registra en logs:

```
INFO - SES no configurado - email simulado: to=user@example.com subject=Verifica tu correo...
```

Para probar el flujo completo en desarrollo puedes:
- Usar un email verificado en SES Sandbox
- O inspeccionar los logs para obtener el token (en desarrollo) y probar manualmente
