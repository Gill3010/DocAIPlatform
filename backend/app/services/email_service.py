"""
Email service - verificación de email y recuperación de contraseña.
Proveedores: Resend (prioridad 1) > Amazon SES (prioridad 2) > log solamente (desarrollo).
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def _get_from_email() -> str:
    """Remitente compartido para todos los proveedores."""
    return settings.SES_FROM_EMAIL or ""


def _send_via_resend(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Envía email vía Resend API."""
    from_email = _get_from_email()
    if not from_email:
        logger.warning("Resend configurado pero SES_FROM_EMAIL vacío - no se puede enviar")
        return False

    payload = {
        "from": from_email,
        "to": [to],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code in (200, 201):
            logger.info("Email enviado (Resend) a %s: %s", to, subject)
            return True
        logger.error(
            "Resend error %s: %s - %s",
            resp.status_code,
            resp.text,
            to,
        )
        return False
    except Exception as e:
        logger.exception("Error enviando email (Resend) a %s: %s", to, e)
        return False


def _send_via_ses(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Envía email vía Amazon SES."""
    try:
        import boto3

        region = getattr(settings, "AWS_SES_REGION", None) or settings.AWS_REGION
        client = boto3.client("ses", region_name=region)
        client.send_email(
            Source=_get_from_email(),
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Email enviado (SES) a %s: %s", to, subject)
        return True
    except Exception as e:
        logger.exception("Error enviando email (SES) a %s: %s", to, e)
        return False


def _send_email(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """
    Envía email.
    Prioridad: Resend (si RESEND_API_KEY) > SES (si SES_ENABLED) > log solamente.
    """
    from_email = _get_from_email()

    if not from_email:
        logger.info(
            "Email no configurado - simulado: to=%s subject=%s "
            "(añade RESEND_API_KEY o SES_FROM_EMAIL + SES_ENABLED)",
            to,
            subject,
        )
        return True

    if settings.RESEND_API_KEY:
        return _send_via_resend(to, subject, html_body, text_body)

    if settings.SES_ENABLED:
        return _send_via_ses(to, subject, html_body, text_body)

    logger.info(
        "Email simulado (sin proveedor): to=%s subject=%s",
        to,
        subject,
    )
    return True


def send_verification_email(to_email: str, token: str, full_name: Optional[str] = None) -> bool:
    """
    Envía email de verificación de cuenta.
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
