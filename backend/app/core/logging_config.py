"""
Configuración centralizada de logging para la aplicación.
Uso: from app.core.logging_config import get_logger
     logger = get_logger(__name__)
"""
import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Devuelve un logger con nombre de módulo. Si es la primera vez, configura el handler raíz."""
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def setup_logging(level: str = "INFO") -> None:
    """
    Configura el logging de la aplicación: formato, nivel y handler en stderr.
    Llamar una vez al arranque (p. ej. en main.py).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    root = logging.getLogger()
    root.setLevel(log_level)
    if not root.handlers:
        root.addHandler(handler)
