# Paso a paso: AWS SES para DocAI Platform

## Confirmación

Sí, si configuras SES correctamente:

- **Cualquier persona** que se registre en docaiplatform.com recibirá los correos de verificación y restablecimiento de contraseña.
- **No necesitas** un proveedor de correo externo (Gmail, Outlook, etc.).
- Los correos se enviarán desde **noreply@docaiplatform.com** (o el correo que configures).

---

# Guía paso a paso en AWS SES

## Parte 1: Verificar el dominio para usar noreply@docaiplatform.com

### Paso 1.1: Ir a SES

1. Entra a la **consola de AWS**: https://console.aws.amazon.com
2. En el buscador, escribe **SES** o **Simple Email Service**
3. Haz clic en **Amazon Simple Email Service**
4. En el selector de región (arriba a la derecha), elige **US East (N. Virginia)** o la región donde ya tengas `innovaproyectos507@gmail.com` verificada

### Paso 1.2: Crear identidad de dominio

1. En el menú izquierdo, ve a **Configuration** → **Identities**
2. Haz clic en **Create identity**
3. En **Identity type**, elige **Domain**
4. En **Domain**, escribe: `docaiplatform.com`
5. Marca **Use a custom MAIL FROM domain** si quieres (opcional; puedes dejarlo sin marcar)
6. Haz clic en **Create identity**

### Paso 1.3: Añadir los registros DNS

En SES verás algo como:

| Type | Record name | Record value |
|------|-------------|--------------|
| CNAME | `h7x9k2m1._domainkey.docaiplatform.com` | `h7x9k2m1.dkim.amazonses.com` |
| CNAME | `p3q8r5t2._domainkey.docaiplatform.com` | `p3q8r5t2.dkim.amazonses.com` |
| CNAME | `w6y1z4a7._domainkey.docaiplatform.com` | `w6y1z4a7.dkim.amazonses.com` |

#### En Cloudflare

1. Entra a **Cloudflare** → selecciona **docaiplatform.com** → pestaña **DNS** → **Records**
2. Haz clic en **Add record**
3. Para **cada uno de los 3 registros**:

   | Campo en Cloudflare | Qué poner | Ejemplo (Record 1) |
   |--------------------|-----------|-------------------|
   | **Type** | CNAME | CNAME |
   | **Name** | Solo la parte ANTES de `.docaiplatform.com`<br>Es decir: `xxx._domainkey` | `h7x9k2m1._domainkey` |
   | **Target** | El valor completo que termina en `.dkim.amazonses.com` | `h7x9k2m1.dkim.amazonses.com` |
   | **Proxy status** | **DNS only** (nube gris, NO naranja) | ⚠️ Importante |
   | **TTL** | Auto o 300 | — |

4. Repite para los 3 registros. Guarda cada uno.

**Resumen de qué copiar:**

- **Name:** Si SES dice `abc123._domainkey.docaiplatform.com` → pon **`abc123._domainkey`** (sin el dominio)
- **Target/Value:** Copia todo tal cual, p. ej. `abc123.dkim.amazonses.com`

#### En Route 53 (AWS)

1. Route 53 → **Hosted zones** → **docaiplatform.com** → **Create record**
2. **Record name:** `abc123._domainkey` (solo la parte antes de .docaiplatform.com)
3. **Record type:** CNAME
4. **Value:** `abc123.dkim.amazonses.com`

#### En GoDaddy, Namecheap u otros

- Si pide "Host" o "Name": solo la parte `xxx._domainkey` (sin docaiplatform.com)
- Si pide "Value", "Target" o "Points to": el valor completo `xxx.dkim.amazonses.com`

⚠️ **Importante:** NO copies `.docaiplatform.com` en el campo Name. Cloudflare y la mayoría de paneles añaden el dominio automáticamente.

### Paso 1.4: Esperar la verificación

1. Vuelve a SES → **Identities**
2. El dominio `docaiplatform.com` aparecerá con estado **Verification pending**
3. Espera entre unos minutos y 72 horas (normalmente menos de 1 hora)
4. Cuando el estado pase a **Verified**, podrás usar `noreply@docaiplatform.com` como remitente

---

## Parte 2: Solicitar Production Access (enviar a cualquier persona)

### Paso 2.1: Ir al Account dashboard

1. En SES, en el menú izquierdo ve a **Get set up** → **Account dashboard**
   - O abre: https://us-east-1.console.aws.amazon.com/ses/home?region=us-east-1#/account

### Paso 2.2: Solicitar producción

1. Si ves **Account status: Sandbox**, haz clic en **Request production access**
2. Completa el formulario:
   - **Mail type**: Transactional
   - **Website URL**: `https://docaiplatform.com`
   - **Use case description** (ejemplo):
     ```
     DocAI Platform envía correos transaccionales a usuarios que se registran:
     1) Verificación de email al crear cuenta
     2) Restablecimiento de contraseña cuando olvidan su contraseña
     Los usuarios se registran voluntariamente y solicitan estos correos.
     No enviamos newsletters ni marketing.
     ```
   - **Compliance**: Indica que cumples con las políticas (no spam, etc.)
3. Haz clic en **Submit**
4. AWS revisará la solicitud (normalmente en menos de 24 horas) y te enviará un correo a la cuenta de AWS

---

## Parte 3: Configurar el backend

### Paso 3.1: Actualizar variables de entorno

Cuando el dominio esté **Verified** en SES, edita `backend/.env`:

```env
# Amazon SES
AWS_SES_REGION=us-east-1
SES_FROM_EMAIL=noreply@docaiplatform.com
SES_ENABLED=true
```

### Paso 3.2: Reiniciar el backend

```bash
pkill -f "uvicorn main:app" 2>/dev/null
sleep 2
cd /home/ec2-user/backend && nohup venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/docai-backend.log 2>&1 &
```

---

## Resumen de orden recomendado

| Orden | Acción | Dónde |
|-------|--------|-------|
| 1 | Crear identidad de dominio `docaiplatform.com` | SES → Identities |
| 2 | Añadir 3 registros CNAME al DNS | Panel DNS (Cloudflare, Route 53, etc.) |
| 3 | Esperar que el dominio pase a Verified | SES → Identities |
| 4 | Solicitar Production access | SES → Account dashboard |
| 5 | Actualizar `SES_FROM_EMAIL=noreply@docaiplatform.com` | backend/.env |
| 6 | Reiniciar backend | Terminal |

---

## Notas importantes

- **Dominio vs correo:** Verificas el **dominio** docaiplatform.com, no el correo noreply@ en sí. Al verificar el dominio, puedes usar cualquier dirección @docaiplatform.com.
- **Production:** Hasta que no aprueben Production access, SES seguirá en Sandbox y solo enviará a direcciones verificadas.
- **Región:** Usa la misma región donde verificaste `innovaproyectos507@gmail.com` (p. ej. us-east-1). `AWS_SES_REGION` en `.env` debe coincidir.
