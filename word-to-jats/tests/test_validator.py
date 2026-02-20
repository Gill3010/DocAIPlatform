"""Tests para JatsSchemaValidator."""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.jats_schema_validator import JatsSchemaValidator, ValidationResult


MINIMAL_JATS = """<?xml version="1.0" encoding="UTF-8"?>
<article article-type="research-article" dtd-version="1.3" xmlns:xlink="http://www.w3.org/1999/xlink">
  <front>
    <article-meta>
      <title-group><article-title>Test</article-title></title-group>
      <contrib-group>
        <contrib contrib-type="author"><name><surname>Apellido</surname><given-names>Nombre</given-names></name></contrib>
      </contrib-group>
    </article-meta>
  </front>
  <body><sec><p>Contenido.</p></sec></body>
</article>
"""


def test_validate_minimal_jats():
    """XML mínimo válido pasa validación de estructura."""
    v = JatsSchemaValidator()
    r = v.validate(xml_path=None, xml_content=MINIMAL_JATS.encode("utf-8"))
    assert r.is_valid is True
    assert r.quality_score > 0


def test_validate_invalid_xml():
    """XML malformado debe fallar."""
    v = JatsSchemaValidator()
    r = v.validate(xml_path=None, xml_content=b"<article><unclosed>")
    assert r.is_valid is False
    assert len(r.errors) > 0
