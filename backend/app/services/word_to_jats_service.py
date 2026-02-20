"""
Servicio de integración Word-to-JATS con DocAI Platform.

Cuando USE_BEDROCK_FOR_JATS=true: intenta Bedrock (Claude) para conversión
de mayor calidad. Si falla (sin tokens, error), hace fallback a DocxToJATSConverter.
"""
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging_config import get_logger
from app.utils.base_converter import ConversionError
from app.utils.converters.jats_converters import DocxToJATSConverter

_logger = get_logger(__name__)


def convert_docx_to_jats_local(
    input_path: str,
    output_path: str,
    grobid_url: Optional[str] = None,
    use_bedrock: Optional[bool] = None,
) -> bool:
    """
    Convierte DOCX a JATS XML compatible con OJS.

    Si use_bedrock=True (o USE_BEDROCK_FOR_JATS en config): intenta Bedrock primero.
    Fallback a DocxToJATSConverter si Bedrock no está disponible o falla.
    """
    try_bedrock = use_bedrock if use_bedrock is not None else getattr(settings, "USE_BEDROCK_FOR_JATS", False)

    if try_bedrock:
        try:
            from app.services.bedrock_jats_service import convert_docx_to_jats_via_bedrock
            region = getattr(settings, "BEDROCK_REGION", None) or getattr(settings, "AWS_REGION", "us-east-1")
            model_id = getattr(settings, "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
            convert_docx_to_jats_via_bedrock(input_path, output_path, region=region, model_id=model_id)
            _logger.info("Word→XML convertido con Bedrock (IA)")
            return True
        except Exception as e:
            _logger.warning("Bedrock no disponible, usando conversión local: %s", e)

    try:
        converter = DocxToJATSConverter()
        return converter.convert(input_path, output_path)
    except Exception as e:
        raise ConversionError(f"Conversión Word a JATS falló: {e}") from e
