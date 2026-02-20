"""
AWS Bedrock Client - Vía Semántica

Especializado en identificar secciones mal etiquetadas,
extraer el sentido de tablas complejas y validar coherencia IMRaD.
"""
from typing import Optional
import json
import boto3
from botocore.exceptions import ClientError


class BedrockClientError(Exception):
    """Error al invocar Bedrock."""


class BedrockClient:
    """Cliente para AWS Bedrock (Claude 3.5 Sonnet)."""

    MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def __init__(self, region: Optional[str] = None):
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """
        Invoca Claude 3.5 Sonnet con system y user prompts.

        Returns:
            Contenido de texto de la respuesta.
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
            ],
        }
        try:
            r = self.client.invoke_model(
                modelId=self.MODEL_ID,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
        except ClientError as e:
            raise BedrockClientError(f"Bedrock invoke failed: {e}") from e

        response_body = json.loads(r["body"].read())
        if "content" not in response_body or not response_body["content"]:
            raise BedrockClientError("Empty response from Bedrock")

        return response_body["content"][0]["text"]

    def convert_fragment_to_jats(self, fragment: str, context: Optional[str] = None) -> str:
        """
        Convierte un fragmento de texto a nodos XML JATS usando el prompt de expert.

        Args:
            fragment: Fragmento de texto extraído de Word.
            context: Contexto opcional (ej. metadatos ya extraídos).

        Returns:
            Fragmento XML JATS.
        """
        from ..core.bedrock_prompts import JATS_EXPERT_SYSTEM_PROMPT

        user_content = fragment
        if context:
            user_content = f"Contexto previo:\n{context}\n\nFragmento a convertir:\n{fragment}"

        return self.invoke(
            system_prompt=JATS_EXPERT_SYSTEM_PROMPT,
            user_prompt=user_content,
            max_tokens=8192,
            temperature=0.2,
        )
