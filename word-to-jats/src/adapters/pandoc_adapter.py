"""
Pandoc Adapter - Vía de Contenido

Convierte Word a estructura XML/JATS usando Pandoc.
Pandoc debe estar instalado en el sistema (apt install pandoc).
Para Lambda: usar Lambda Layer con binario Pandoc o imagen Docker.
"""
from pathlib import Path
from typing import Optional
import subprocess
import tempfile

from lxml import etree


class PandocAdapterError(Exception):
    """Error al ejecutar Pandoc."""


def convert_to_jats(doc_path: str, timeout: int = 60) -> Optional[etree._Element]:
    """
    Convierte un documento Word/PDF a JATS XML usando Pandoc.

    Args:
        doc_path: Ruta al archivo .docx o .pdf.
        timeout: Timeout en segundos.

    Returns:
        Elemento raíz del XML generado por Pandoc, o None si falla.
    """
    suffix = Path(doc_path).suffix.lower()
    if suffix not in (".docx", ".doc", ".odt", ".pdf"):
        return None

    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        out_path = tmp.name

    try:
        subprocess.run(
            ["pandoc", doc_path, "-o", out_path, "-t", "jats", "--wrap=none"],
            check=True,
            capture_output=True,
            timeout=timeout,
        )
        tree = etree.parse(out_path)
        return tree.getroot()
    except FileNotFoundError as e:
        raise PandocAdapterError("Pandoc no está instalado. Ejecute: apt install pandoc") from e
    except subprocess.CalledProcessError as e:
        raise PandocAdapterError(f"Pandoc falló: {e.stderr.decode() if e.stderr else str(e)}") from e
    except subprocess.TimeoutExpired:
        raise PandocAdapterError(f"Pandoc superó el timeout de {timeout}s") from None
    finally:
        Path(out_path).unlink(missing_ok=True)
