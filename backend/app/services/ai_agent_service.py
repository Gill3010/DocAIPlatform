"""
AI Agent Service - Comunicación con Amazon Bedrock (Claude).

Sigue el mismo patrón que bedrock_jats_service para invocación:
- Misma resolución de region y model_id (BEDROCK_REGION, BEDROCK_MODEL_ID, AWS_REGION)
- Mismo cliente boto3 bedrock-runtime
- Mismo formato de body (anthropic_version, system, messages con content tipo text)
"""
from __future__ import annotations

import json
from typing import Optional

from app.core.config import settings
from app.services.ai_agent_tools import build_tools_section

TOOLS_SECTION = build_tools_section()

SYSTEM_PROMPT = """Eres el Asistente de IA de DocAI Platform, una plataforma especializada en conversión de documentos y herramientas PDF.

## TU ROL
- Ayudar con el uso de la aplicación
- Recomendar conversiones de formato y herramientas PDF según las necesidades del usuario
- Responder preguntas sobre documentos (contenido, formato, edición)
- Dar consejos prácticos de conversión y optimización
Sé conciso, amigable y orientado a la acción.

""" + TOOLS_SECTION + """

## REGLA CRÍTICA: SMART LINKS (enlaces internos)
Cuando recomiendes una conversión, herramienta PDF o página de DocAI, SIEMPRE incluye el enlace en formato Markdown:
- Conversiones: [Convertir PDF a Word](/convert?from=pdf&to=docx)
- Herramientas PDF: [Unir PDF](/pdf-tools?tool=unir-pdf)
- Otras páginas: [Ver precios](/pricing)

Usa rutas relativas (empezando por /) para enlaces internos. El usuario debe poder hacer clic y navegar.

## ENLACES EXTERNOS DE REFERENCIA
Cuando el usuario pida ejemplos, documentación, estándares o recursos de aprendizaje, ADEMÁS de recomendar las herramientas de DocAI, incluye URLs externas en formato Markdown clicable, por ejemplo:
- JATS/XML: [Tag Suite de JATS (NLM)](https://jats.nlm.nih.gov/), [JATS4R](https://jats4r.org/)
- PDF: [Especificación PDF](https://www.adobe.com/devnet/pdf/pdf_reference.html)
- Otras referencias oficiales cuando sean relevantes

Usa el formato [Texto descriptivo](https://url-externa.com). Las URLs externas se abren en nueva pestaña. No inventes URLs; usa solo enlaces reales y verificables a documentación oficial o recursos reconocidos.

Responde en el mismo idioma que use el usuario.
"""


class AIAgentServiceError(Exception):
    """Error al invocar el servicio Bedrock."""


def _get_bedrock_config():
    """Misma lógica que word_to_jats_service: region y model_id desde settings."""
    region = getattr(settings, "BEDROCK_REGION", None) or getattr(settings, "AWS_REGION", "us-east-1")
    model_id = getattr(settings, "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
    return region, model_id


def invoke_claude(
    messages: list[dict],
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    """
    Invoca Claude en Amazon Bedrock. Mismo patrón que convert_docx_to_jats_via_bedrock.
    messages: lista de {"role": "user"|"assistant", "content": "..."}
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise AIAgentServiceError("boto3 no instalado")

    region, model_id = _get_bedrock_config()
    client = boto3.client("bedrock-runtime", region_name=region)
    system = system_prompt or SYSTEM_PROMPT

    # Formato idéntico a bedrock_jats_service: content como [{"type": "text", "text": "..."}]
    bedrock_messages = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role not in ("user", "assistant"):
            continue
        bedrock_messages.append({
            "role": role,
            "content": [{"type": "text", "text": str(content)}],
        })

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": bedrock_messages,
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if "ThrottlingException" in code:
            raise AIAgentServiceError("El servicio de IA está sobrecargado. Inténtalo en unos minutos.") from e
        if "AccessDeniedException" in code or "ValidationException" in code:
            raise AIAgentServiceError(f"Bedrock no disponible: {e}") from e
        raise AIAgentServiceError(str(e)) from e

    response_body = json.loads(response["body"].read())
    if "content" not in response_body or not response_body["content"]:
        raise AIAgentServiceError("Respuesta vacía de Bedrock")

    return response_body["content"][0]["text"].strip()
