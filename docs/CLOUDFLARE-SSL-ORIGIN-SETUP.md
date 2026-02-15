# Configurar SSL con Certificado Origin de Cloudflare

Esto permitirá usar **Full (strict)** en Cloudflare y que los WebSockets funcionen correctamente.

## Paso 1: Crear el certificado en Cloudflare

1. Entra en **Cloudflare** → tu dominio **docaiplatform.com**
2. Menú lateral: **SSL/TLS** → **Origin Server**
3. Clic en **Create Certificate**
4. Opciones recomendadas:
   - **Private key type**: ECDSA (más rápido) o RSA
   - **Hostnames**: `docaiplatform.com` y `*.docaiplatform.com` (para cubrir www)
   - **Validity**: 15 years
5. Clic en **Create**
6. Se muestran dos bloques de texto:
   - **Origin Certificate**: copia TODO (incluyendo `-----BEGIN CERTIFICATE-----` y `-----END CERTIFICATE-----`)
   - **Private Key**: copia TODO (incluyendo `-----BEGIN PRIVATE KEY-----` y `-----END PRIVATE KEY-----`)
7. Guarda ambos en un lugar seguro (los necesitarás en el Paso 2)

## Paso 2: Guardar los archivos en el servidor

En tu servidor (via SSH o Session Manager), ejecuta:

```bash
# Crear directorio para certificados
sudo mkdir -p /etc/nginx/ssl

# Crear archivo del certificado (pega el Origin Certificate cuando lo pida)
sudo nano /etc/nginx/ssl/docaiplatform-cert.pem
# Pega el contenido del certificado, guarda con Ctrl+O, Enter, Ctrl+X

# Crear archivo de la clave privada (pega el Private Key cuando lo pida)
sudo nano /etc/nginx/ssl/docaiplatform-key.pem
# Pega el contenido de la clave privada, guarda con Ctrl+O, Enter, Ctrl+X

# Asegurar permisos
sudo chmod 600 /etc/nginx/ssl/docaiplatform-key.pem
sudo chmod 644 /etc/nginx/ssl/docaiplatform-cert.pem
```

## Paso 3: Actualizar nginx

Ya existe el archivo `docaiplatform-nginx-ssl.conf` con la configuración SSL. Cópialo:

```bash
sudo cp /home/ec2-user/docaiplatform-nginx-ssl.conf /etc/nginx/conf.d/docaiplatform.conf
sudo nginx -t
sudo systemctl reload nginx
```

## Paso 4: Cambiar Cloudflare a Full (strict)

1. Cloudflare → **SSL/TLS** → **Overview**
2. Cambia el modo a **Full (strict)**
3. Guarda

## Paso 5: Probar

1. Abre https://docaiplatform.com/collab/54
2. Verifica que aparezca **Conectado** en lugar de Desconectado
