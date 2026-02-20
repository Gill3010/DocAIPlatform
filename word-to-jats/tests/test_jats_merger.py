"""Tests para JatsMerger."""
import pytest
from lxml import etree

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.jats_merger import JatsMerger, ConfidenceScore


def test_merge_minimal_creates_article():
    """Sin inputs, debe crear article mínimo."""
    merger = JatsMerger()
    article = merger.merge()
    assert article.tag in ("article", "{http://jats.nlm.nih.gov}article") or "article" in article.tag
    assert article.find(".//front") is not None
    assert article.find(".//body") is not None


def test_deep_merge_table():
    """Deep merge de tabla con label y caption."""
    merger = JatsMerger()
    grid = [["A", "B"], ["1", "2"]]
    tbl = merger.deep_merge_table(grid, label="Tabla 1", caption="Descripción")
    assert tbl.tag == "table"
    assert tbl.find("label") is not None
    assert tbl.find("label").text == "Tabla 1"
    assert tbl.find("caption") is not None
    tbody = tbl.find("tbody")
    assert tbody is not None
    assert len(tbody.findall("tr")) == 2
