# Configuración de Resend para correos transaccionales

DocAI Platform soporta dos proveedores de correo: **Resend** (prioridad 1) y **Amazon SES** (prioridad 2). Si `RESEND_API_KEY` está definido, se usa Resend. En caso contrario, se usa SES si está configurado.

## Ventajas de Resend

- No requiere solicitud de aprobación (SES sí en producción)
- Plan gratuito: 3.000 emails/mes
- Integración simple vía API REST
- Buen deliverability para transaccionales

---

## Paso 1: Crear cuenta en Resend

1. Ve a [resend.com](https://resend.com) y crea una cuenta.
2. Verifica tu correo si lo solicitan.

---

## Paso 2: Verificar el dominio docaiplatform.com

1. En el dashboard de Resend, ve a **Domains** → **Add Domain**.
2. Introduce `docaiplatform.com`.
3. Resend te mostrará registros DNS (SPF, DKIM) que debes añadir en tu proveedor DNS.

**Registros típicos (ejemplo):**
- Tipo **MX** o **TXT** para verificación
- Registros **CNAME** para DKIM (3 registros similares a `resend._domainkey`)

4. Añade los registros en tu panel DNS (Cloudflare, Route53, etc.).
5. Espera a que Resend marque el dominio como **Verified** (puede tardar unos minutos u horas).

---

## Paso 3: Crear API Key

1. En Resend: **API Keys** → **Create API Key**.
2. Pon un nombre (ej. "DocAI Platform producción").
3. Copia la clave (empieza por `re_`) — solo se muestra una vez.
4. Guarda la clave en un lugar seguro.

---

## Paso 4: Configurar el backend

Edita `backend/.env` y añade:

```env
# Resend (prioridad sobre SES cuando está definido)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx

# Remitente (compartido Resend/SES) - debe estar verificado en Resend
SES_FROM_EMAIL=noreply@docaiplatform.com
```

**Opcional:** Si usas solo Resend, puedes desactivar SES para evitar intentos fallidos:

```env
SES_ENABLED=false
```

---

## Paso 5: Reiniciar el backend

```bash
pm2 restart backend
# o
cd backend && uvicorn main:app --reload
```

---

## Comprobar que funciona

1. **Registro:** Crea una cuenta nueva con un email real → debería llegar el correo de verificación.
2. **Recuperación:** Usa "¿Olvidaste tu contraseña?" con un email registrado → debería llegar el enlace de reset.

---

## Resolución de problemas

| Problema | Solución |
|----------|----------|
| Email no llega | Revisa que el dominio esté **Verified** en Resend. |
| Error 403 | API key inválida o sin permisos; genera una nueva. |
| Emails en spam | Verifica SPF/DKIM en el dominio; Revisa la carpeta spam temporalmente. |
| `SES_FROM_EMAIL` vacío | El remitente es obligatorio; debe ser `noreply@docaiplatform.com` (o similar). |

---

## Volver a SES más adelante

Para usar de nuevo Amazon SES en producción:

1. En `.env`: borra o comenta `RESEND_API_KEY`.
2. Mantén `SES_ENABLED=true` y `SES_FROM_EMAIL=noreply@docaiplatform.com`.
3. Reinicia el backend.

La prioridad es: Resend (si API key) > SES (si enabled) > log solamente.
