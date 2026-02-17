"""Tests for conversion orchestrator and strategy (refactor modular)."""
import os
import tempfile

import pytest

from app.services.conversion_strategy import resolve_strategy, ConversionStrategy
from app.services.conversion_orchestrator import execute_conversion


def test_resolve_strategy_pdf_docx_local():
    """PDF->DOCX debe ser siempre local (prefers_local en conversor)."""
    r = resolve_strategy("pdf", "docx")
    assert r == ConversionStrategy.LOCAL


def test_resolve_strategy_png_pdf_local():
    """PNG->PDF debe ser siempre local."""
    r = resolve_strategy("png", "pdf")
    assert r == ConversionStrategy.LOCAL


def test_resolve_strategy_docx_pdf_ecs_when_enabled():
    """DOCX->PDF usa ECS cuando USE_ECS_CONVERTER=true."""
    r = resolve_strategy("docx", "pdf", use_ecs_setting=True)
    assert r == ConversionStrategy.ECS


def test_resolve_strategy_docx_pdf_local_when_ecs_disabled():
    """DOCX->PDF usa local cuando USE_ECS_CONVERTER=false."""
    r = resolve_strategy("docx", "pdf", use_ecs_setting=False)
    assert r == ConversionStrategy.LOCAL


def test_resolve_strategy_docx_xml_jats_when_enabled():
    """DOCX->XML usa JATS ensemble cuando USE_JATS_ENSEMBLE=true."""
    r = resolve_strategy("docx", "xml", use_jats_ensemble_setting=True)
    assert r == ConversionStrategy.JATS_ENSEMBLE


def test_resolve_strategy_docx_xml_local_when_jats_disabled():
    """DOCX->XML usa local cuando USE_JATS_ENSEMBLE=false."""
    r = resolve_strategy("docx", "xml", use_jats_ensemble_setting=False)
    assert r == ConversionStrategy.LOCAL


def test_execute_conversion_png_to_pdf():
    """PNG->PDF ejecuta correctamente (estrategia local)."""
    from PIL import Image

    img = Image.new("RGB", (10, 10), color="blue")
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "test.png")
        out_path = os.path.join(tmpdir, "out.pdf")
        img.save(in_path)
        result = execute_conversion(in_path, out_path, "png", "pdf")
        assert result is True
        assert os.path.exists(out_path)


def test_execute_conversion_txt_to_docx():
    """TXT->DOCX ejecuta correctamente."""
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "test.txt")
        out_path = os.path.join(tmpdir, "out.docx")
        with open(in_path, "w") as f:
            f.write("Test content")
        result = execute_conversion(in_path, out_path, "txt", "docx")
        assert result is True
        assert os.path.exists(out_path)


@pytest.mark.skipif(
    os.environ.get("USE_ECS_CONVERTER", "").lower() == "true",
    reason="DOCX->PDF uses ECS when enabled; skip to avoid AWS dependency",
)
def test_execute_conversion_docx_to_pdf_local():
    """DOCX->PDF usa conversión local cuando ECS está deshabilitado."""
    from docx import Document

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = os.path.join(tmpdir, "test.docx")
        out_path = os.path.join(tmpdir, "out.pdf")
        doc = Document()
        doc.add_paragraph("Test")
        doc.save(in_path)
        result = execute_conversion(in_path, out_path, "docx", "pdf")
        assert result is True
        assert os.path.exists(out_path)
