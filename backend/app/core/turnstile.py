"""Cloudflare Turnstile token verification."""

from __future__ import annotations

from typing import Optional

import httpx
from app.core.config import settings

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile_token(token: Optional[str], remote_ip: Optional[str] = None) -> bool:
    """
    Verifica un token de Turnstile con la API de Cloudflare.
    Retorna True si el token es válido, False en caso contrario.
    """
    if not settings.TURNSTILE_SECRET_KEY:
        return True  # Si no está configurado, no validamos

    if not token or not token.strip():
        return False

    async with httpx.AsyncClient() as client:
        data: dict[str, str] = {
            "secret": settings.TURNSTILE_SECRET_KEY,
            "response": token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        try:
            resp = await client.post(
                TURNSTILE_VERIFY_URL,
                json=data,
                timeout=10.0,
            )
            result = resp.json()
            return result.get("success") is True
        except Exception:
            return False
