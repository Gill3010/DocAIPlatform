# Configurar noreply@docaiplatform.com para envío a todos los usuarios

## Lo que necesitas lograr

1. **Remitente:** `noreply@docaiplatform.com` (en lugar de innovaproyectos507@gmail.com)
2. **Destinatarios:** Cualquier usuario (gmail.com, outlook.com, etc.), no solo direcciones verificadas

---

## Importante: no necesitas un “proveedor de correo gratis”

Para **enviar** correos con Amazon SES desde `noreply@docaiplatform.com`:

- No necesitas crear una cuenta de correo en Gmail, Outlook u otro proveedor.
- No necesitas un buzón real para `noreply@docaiplatform.com`.
- Solo debes **verificar que eres dueño del dominio** docaiplatform.com en SES añadiendo registros DNS.

SES solo necesita que puedas editar los DNS de `docaiplatform.com` para comprobar que eres el propietario del dominio.

---

## Pasos para usar noreply@docaiplatform.com

### 1. Verificar el dominio en Amazon SES

1. Entra a **Amazon SES** → **Identities** → **Create identity**
2. Elige **Domain**
3. Dominio: `docaiplatform.com`
4. Clic en **Create identity**
5. SES te mostrará varios registros **CNAME** que debes añadir en tu DNS

### 2. Añadir los registros DNS

Donde gestiones el DNS de docaiplatform.com (por ejemplo):

- **Cloudflare**
- **Route 53** (si el dominio está en AWS)
- **GoDaddy, Namecheap, Google Domains**, etc.

Copia cada registro CNAME que muestre SES y créalo en tu panel DNS. Suele haber 3 registros de tipo DKIM.

Espera a que DNS se propague (desde minutos hasta 24 horas).

### 3. Esperar verificación del dominio

Cuando los registros DNS estén correctos, SES marcará el dominio como **Verified**. Solo entonces podrás usar `noreply@docaiplatform.com` como remitente.

### 4. Actualizar el backend

En `backend/.env`:

```env
SES_FROM_EMAIL=noreply@docaiplatform.com
SES_ENABLED=true
AWS_SES_REGION=us-east-1
```

Reinicia el backend.

---

## Permitir envío a cualquier usuario (Production)

En modo **Sandbox**, SES solo envía a direcciones verificadas en SES.

Para que **cualquier usuario** reciba los correos (gmail, outlook, etc.):

1. Entra en **Amazon SES** → **Account dashboard**
2. Pulsa **Request production access**
3. Rellena el formulario (tipo de correo: transaccional, uso de verificación y recuperación de contraseña, etc.)

Normalmente la aprobación tarda hasta 24 horas.

---

## Resumen rápido

| Requisito              | Acción                                                                 |
|------------------------|------------------------------------------------------------------------|
| Usar noreply@docaiplatform.com | Verificar el dominio docaiplatform.com en SES y añadir registros DNS |
| Enviar a cualquier correo     | Solicitar **Production access** en SES                            |
| Sin proveedor de correo extra | No hace falta: solo DNS del dominio y SES                         |

---

## Si no controlas el DNS de docaiplatform.com

Si no puedes editar los DNS del dominio:

- **Opción A:** Pide acceso al panel de DNS (Cloudflare, Route 53, etc.) para añadir los registros.
- **Opción B:** Sigue usando `innovaproyectos507@gmail.com` como remitente (ya verificado). Funciona igual; solo cambia la apariencia del remitente.
