#!/usr/bin/env python3
"""
Migración: añade email_verified_at a users y crea tabla auth_tokens.
Ejecutar una vez: python -m backend.migrate_auth_tokens
"""
import asyncio
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR / "sql_app.db"


def run_migration():
    if not DB_PATH.exists():
        print(f"DB no encontrada: {DB_PATH}. Saltando migración.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Añadir email_verified_at si no existe
    cur.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cur.fetchall()]
    if "email_verified_at" not in columns:
        cur.execute("ALTER TABLE users ADD COLUMN email_verified_at DATETIME")
        print("  + Columna email_verified_at añadida a users")
    else:
        print("  - email_verified_at ya existe")

    # 2. Crear auth_tokens si no existe
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='auth_tokens'"
    )
    if cur.fetchone() is None:
        cur.execute("""
            CREATE TABLE auth_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash VARCHAR(64) NOT NULL UNIQUE,
                user_id INTEGER NOT NULL REFERENCES users(id),
                purpose VARCHAR(32) NOT NULL,
                expires_at DATETIME NOT NULL,
                used_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("CREATE INDEX idx_auth_tokens_token ON auth_tokens(token_hash)")
        cur.execute("CREATE INDEX idx_auth_tokens_user_purpose ON auth_tokens(user_id, purpose)")
        print("  + Tabla auth_tokens creada")
    else:
        print("  - auth_tokens ya existe")

    # 3. Marcar usuarios existentes como verificados (para no romper logins actuales)
    cur.execute(
        "UPDATE users SET email_verified_at = datetime('now') WHERE email_verified_at IS NULL"
    )
    if cur.rowcount > 0:
        print(f"  + {cur.rowcount} usuarios existentes marcados como verificados")

    conn.commit()
    conn.close()
    print("Migración completada.")


if __name__ == "__main__":
    run_migration()
