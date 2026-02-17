"""
Orquestador de conversiones: ejecuta la conversión según la estrategia resuelta.

Centraliza la lógica de ejecución (local, ECS, Word-to-JATS) sin que el router
conozca los detalles. El router solo llama a execute_conversion.
"""
from app.core.config import settings
from app.core.logging_config import get_logger
from app.services.conversion_strategy import resolve_strategy, ConversionStrategy
from app.utils.converter import convert_file
from app.utils.base_converter import ConversionError

_logger = get_logger(__name__)


def execute_conversion(
    input_path: str,
    output_path: str,
    source_format: str,
    target_format: str,
) -> bool:
    """
    Ejecuta la conversión según la estrategia (local, ECS o JATS ensemble).

    Args:
        input_path: Ruta del archivo de entrada
        output_path: Ruta del archivo de salida
        source_format: Formato origen (ej. 'docx', 'pdf')
        target_format: Formato destino (ej. 'xml', 'pdf')

    Returns:
        True si la conversión fue exitosa

    Raises:
        ConversionError: Si la conversión falla
    """
    strategy = resolve_strategy(source_format, target_format)

    if strategy == ConversionStrategy.JATS_ENSEMBLE:
        _logger.info("Using Word-to-JATS ensemble for docx->xml")
        from app.services.word_to_jats_service import convert_docx_to_jats_local
        return convert_docx_to_jats_local(
            input_path,
            output_path,
            grobid_url=settings.GROBID_URL or None,
            use_bedrock=getattr(settings, "USE_BEDROCK_FOR_JATS", False),
        )

    if strategy == ConversionStrategy.ECS:
        _logger.info("Using ECS converter for %s->%s", source_format, target_format)
        from app.services.ecs_converter_service import convert_via_ecs
        try:
            convert_via_ecs(input_path, output_path, source_format, target_format)
            _logger.info("ECS conversion completed successfully")
            return True
        except ConversionError as e:
            _logger.warning("ECS failed, falling back to local: %s", e)
            return convert_file(input_path, output_path, source_format, target_format)

    # LOCAL (por defecto)
    _logger.info("Using local converter for %s->%s", source_format, target_format)
    return convert_file(input_path, output_path, source_format, target_format)
