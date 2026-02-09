# Dónde ver los usuarios que iniciaron sesión con Google y Facebook

En DocAI Platform **todos los usuarios** (email, Google y Facebook) están en la **misma tabla** de la base de datos. El campo que indica cómo iniciaron sesión es **`auth_provider`**.

---

## En la base de datos

- **Tabla:** `users`
- **Campo:** `auth_provider` → valores: `'email'` | `'google'` | `'facebook'`

Así puedes distinguir:
- **`email`**: registro/inicio de sesión con correo y contraseña
- **`google`**: inicio de sesión con Google
- **`facebook`**: inicio de sesión con Facebook

La base de datos que usa la app es **una sola**: **`backend/sql_app.db`**. Para consultarla desde la terminal, usa el cliente `sqlite3` (no pegues el SELECT directamente en bash, o saldrá "command not found"):

```bash
cd /home/ubuntu && sqlite3 backend/sql_app.db "SELECT id, email, full_name, auth_provider FROM users ORDER BY id;"
```

O abre la base de datos y luego escribe el SELECT dentro de sqlite3:

```bash
cd /home/ubuntu && sqlite3 backend/sql_app.db
```

En el prompt `sqlite>` que aparece, pega:

```sql
SELECT id, email, full_name, auth_provider FROM users ORDER BY id;
```

Para salir de sqlite3: escribe `.quit` o pulsa Ctrl+D.

---

## Script para listarlos en consola

Desde la raíz del proyecto puedes ejecutar:

```bash
cd /home/ubuntu && source backend/venv/bin/activate && PYTHONPATH=. python backend/list_users.py
```

Ese script muestra todos los usuarios con su **id**, **email**, **nombre** y **con qué iniciaron sesión** (Email, Google o Facebook). Así ves quiénes son de Google/Facebook para decidir a quiénes eliminar.

---

## Cómo eliminarlos

Para **dejar solo un usuario** (por ejemplo Karina Gutierrez) y borrar el resto (incluidas sus conversiones), usa:

```bash
PYTHONPATH=. python backend/delete_users_except.py
```

Antes, edita en `backend/delete_users_except.py` la constante `KEEP_FULL_NAME` con el nombre exacto del usuario que quieres conservar. Los demás (Google, Facebook o email) se eliminan de la base de datos.

---

## Resumen

| Qué quieres hacer | Dónde / Cómo |
|-------------------|---------------|
| **Ver** todos los usuarios y si son Google/Facebook | Ejecutar `backend/list_users.py` o consultar la tabla `users`, campo `auth_provider` |
| **Eliminar** usuarios y dejar solo uno | Editar `KEEP_FULL_NAME` en `backend/delete_users_except.py` y ejecutar ese script |

Los usuarios de Google y Facebook **no** se gestionan en la consola de Google o Meta: se ven y se eliminan en **tu base de datos** (tabla `users`) o con los scripts anteriores.
