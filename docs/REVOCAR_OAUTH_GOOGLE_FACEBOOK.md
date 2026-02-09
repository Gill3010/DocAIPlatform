# Dónde revocar el acceso de DocAI Platform (Google y Facebook)

Si iniciaste sesión con **Google** o **Facebook** en DocAI Platform y quieres que la aplicación deje de tener acceso a tu cuenta, debes revocarlo en la configuración de cada proveedor.

---

## Google

1. Entra en **Cuenta de Google**: [https://myaccount.google.com/](https://myaccount.google.com/)
2. En el menú izquierdo, ve a **Seguridad** (o **Security**).
3. En la sección **“Acceso de terceros a tu cuenta”** (o **“Third-party apps with account access”**), haz clic en **“Acceso de terceros a tu cuenta”**.
4. Ahí verás la lista de aplicaciones que tienen acceso. Busca **DocAI Platform** (o el nombre que tenga tu app en la consola de Google Cloud).
5. Haz clic en la app y luego en **“Quitar acceso”** / **“Revoke access”**.

**Enlace directo (si está disponible en tu cuenta):**  
[https://myaccount.google.com/permissions](https://myaccount.google.com/permissions)

---

## Facebook (Meta)

1. Entra en **Facebook** e inicia sesión.
2. Ve a **Configuración y privacidad** → **Configuración** (o [https://www.facebook.com/settings](https://www.facebook.com/settings)).
3. En el menú izquierdo, entra en **Seguridad** → **Aplicaciones y sitios web** (o **Apps and Websites**).
4. En **“Aplicaciones, sitios web y juegos”** verás las apps con acceso. Busca **DocAI Platform** (o el nombre de tu app en Meta for Developers).
5. Haz clic en la app y elige **“Quitar”** / **“Remove”**.

**Enlace directo:**  
[https://www.facebook.com/settings?tab=applications](https://www.facebook.com/settings?tab=applications)

---

## Nota

Al revocar el acceso, la **próxima vez** que intentes iniciar sesión en DocAI Platform con ese proveedor, se te pedirá autorizar de nuevo. Los usuarios que ya existen en la base de datos de DocAI Platform no se borran automáticamente al revocar en Google/Facebook; para eliminarlos hay que borrarlos en tu base de datos (por ejemplo con el script `delete_users_except.py`).
