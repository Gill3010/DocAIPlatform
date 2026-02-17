"""
Resolución de estrategia de conversión: local, ECS o Word-to-JATS.

Centraliza la decisión de qué motor usar (evita lógica dispersa en el router).
Usa metadatos de los conversores (prefers_local) cuando están disponibles.

Variables de entorno que controlan la estrategia (.env):
- USE_ECS_CONVERTER: True para intentar ECS en docx→pdf y otras (cuando no prefers_local)
- USE_JATS_ENSEMBLE: True para usar Word-to-JATS (Bedrock/local) en docx→xml
"""
from enum import Enum
from typing import Optional

from app.core.config import settings
from app.utils import converters  # registro de conversores
from app.utils.base_converter import registry


class ConversionStrategy(str, Enum):
    """Motor a usar para la conversión."""
    LOCAL = "local"           # convert_file (registry)
    ECS = "ecs"               # AWS ECS Fargate (con fallback a local)
    JATS_ENSEMBLE = "jats_ensemble"  # Word-to-JATS (Bedrock o DocxToJATSConverter)


def resolve_strategy(
    source_format: str,
    target_format: str,
    use_ecs_setting: Optional[bool] = None,
    use_jats_ensemble_setting: Optional[bool] = None,
) -> ConversionStrategy:
    """
    Determina qué motor de conversión usar.

    Reglas (en orden):
    1. docx→xml con USE_JATS_ENSEMBLE → JATS_ENSEMBLE
    2. Si el conversor tiene prefers_local=True → LOCAL (evita ECS)
    3. docx→pdf y use_ecs → ECS (mejor calidad)
    4. Otras conversiones con use_ecs → ECS
    5. Por defecto → LOCAL

    Args:
        source_format: Formato origen (ej. 'docx', 'pdf')
        target_format: Formato destino (ej. 'xml', 'pdf')
        use_ecs_setting: Override de USE_ECS_CONVERTER (None = usar config)
        use_jats_ensemble_setting: Override de USE_JATS_ENSEMBLE (None = usar config)
    """
    source = source_format.lower().replace(".", "")
    target = target_format.lower().replace(".", "")

    use_jats = (
        use_jats_ensemble_setting
        if use_jats_ensemble_setting is not None
        else getattr(settings, "USE_JATS_ENSEMBLE", False)
    )
    use_ecs = (
        use_ecs_setting
        if use_ecs_setting is not None
        else getattr(settings, "USE_ECS_CONVERTER", False)
    )

    # 1. Word-to-JATS tiene prioridad para docx→xml cuando está habilitado
    if source == "docx" and target == "xml" and use_jats:
        return ConversionStrategy.JATS_ENSEMBLE

    # 2. Consultar al conversor si prefiere ejecución local (nunca ECS)
    try:
        converter = registry.get_converter(source, target)
        if getattr(converter, "prefers_local", True):
            return ConversionStrategy.LOCAL
    except Exception:
        pass  # Si no hay conversor, seguir con reglas por defecto

    # 3. docx→pdf: ECS opcional (mejor calidad de tablas/imágenes)
    if source == "docx" and target == "pdf":
        return ConversionStrategy.ECS if use_ecs else ConversionStrategy.LOCAL

    # 4. Otras conversiones: ECS solo si está habilitado
    return ConversionStrategy.ECS if use_ecs else ConversionStrategy.LOCAL
