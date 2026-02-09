"""
Base para el patrón Strategy en herramientas PDF.
Cada herramienta implementa run(work_dir, files, form) y devuelve ToolResult.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Resultado de ejecutar una herramienta PDF."""
    path: Optional[Path] = None
    paths: Optional[List[Path]] = None
    text: Optional[str] = None
    filename: str = ""
    media_type: str = "application/pdf"


class PDFToolStrategy(ABC):
    """Interfaz de una herramienta PDF: valida inputs, llama a la util y devuelve ToolResult."""

    tool_name: str = ""

    @abstractmethod
    def run(self, work_dir: Path, files: Dict[str, bytes], form: Dict[str, Any]) -> ToolResult:
        """
        Ejecuta la herramienta.
        :param work_dir: directorio de trabajo (ya creado)
        :param files: mapa nombre_lógico -> contenido bytes (ej. "file", "file_a", "file_b", "files_0", "signature_image")
        :param form: parámetros de formulario (angle, password, page_order, etc.)
        :return: ToolResult con path/paths/text, filename y media_type
        """
        pass
