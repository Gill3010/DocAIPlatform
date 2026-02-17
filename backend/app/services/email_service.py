"""
Email service - verificación de email y recuperación de contraseña.
Usa Amazon SES cuando está configurado; si no, solo registra en logs (para desarrollo).
"""
from __future__ import annotations

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str, full_name: Optional[str] = None) -> bool:
    """
    Envía email de verificación de cuenta.
    Si SES no está configurado, registra en log y retorna True (para desarrollo).
    """
    verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/verify-email?token={token}"
    subject = "Verifica tu correo - DocAI Platform"
    name = full_name or "Usuario"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Verifica tu correo</title></head>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>¡Hola, {name}!</h2>
        <p>Gracias por registrarte en DocAI Platform. Para activar tu cuenta, haz clic en el siguiente enlace:</p>
        <p style="margin: 24px 0;">
            <a href="{verify_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Verificar mi correo</a>
        </p>
        <p style="color: #666; font-size: 14px;">Este enlace expira en 24 horas. Si no creaste esta cuenta, ignora este correo.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px;">DocAI Platform - Conversión de documentos</p>
    </body>
    </html>
    """
    text_body = f"Hola {name},\n\nVerifica tu correo en: {verify_url}\n\nExpira en 24 horas."

    return _send_email(to_email, subject, html_body, text_body)


def send_password_reset_email(to_email: str, token: str, full_name: Optional[str] = None) -> bool:
    """
    Envía email con enlace para restablecer contraseña.
    Si SES no está configurado, registra en log y retorna True (para desarrollo).
    """
    reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/auth/reset-password?token={token}"
    subject = "Restablecer contraseña - DocAI Platform"
    name = full_name or "Usuario"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><title>Restablecer contraseña</title></head>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Hola, {name}</h2>
        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta. Haz clic en el enlace para continuar:</p>
        <p style="margin: 24px 0;">
            <a href="{reset_url}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Restablecer contraseña</a>
        </p>
        <p style="color: #666; font-size: 14px;">Este enlace expira en 1 hora. Si no solicitaste esto, ignora el correo y tu contraseña no cambiará.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #999; font-size: 12px;">DocAI Platform - Conversión de documentos</p>
    </body>
    </html>
    """
    text_body = f"Hola {name},\n\nRestablece tu contraseña en: {reset_url}\n\nExpira en 1 hora."

    return _send_email(to_email, subject, html_body, text_body)


def _send_email(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Envía email vía SES o registra en log si no está configurado."""
    if not settings.SES_ENABLED or not settings.SES_FROM_EMAIL:
        logger.info(
            "SES no configurado - email simulado: to=%s subject=%s (configure SES_FROM_EMAIL y SES_ENABLED=true)",
            to, subject
        )
        return True

    try:
        import boto3
        region = getattr(settings, "AWS_SES_REGION", None) or settings.AWS_REGION
        client = boto3.client("ses", region_name=region)
        client.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Email enviado a %s: %s", to, subject)
        return True
    except Exception as e:
        logger.exception("Error enviando email a %s: %s", to, e)
        return False
