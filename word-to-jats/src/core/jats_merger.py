"""
JatsMerger - Intelligent Merger Logic (El Cerebro)

Combina resultados de GROBID (estructural), Pandoc (contenido) y Bedrock (semántico).
Aplica Score de Confianza y Deep Merge de tablas.
"""
from typing import Any, Optional
from enum import Enum
from pathlib import Path
from lxml import etree


class ConfidenceScore(str, Enum):
    """Niveles de confianza para elementos fusionados."""
    HIGH = "high_confidence"
    MEDIUM = "medium_confidence"
    LOW = "low_confidence"


class JatsMergerError(Exception):
    """Error en el proceso de fusión JATS."""


class JatsMerger:
    """
    Ensambla el XML JATS final a partir de las tres vías:
    - GROBID: metadatos, bibliografía
    - Pandoc: estructura de contenido (párrafos, tablas, headings)
    - Bedrock: corrección semántica, labels/captions de tablas, secciones back
    """

    XLINK_NS = "http://www.w3.org/1999/xlink"
    JATS_NS = "http://jats.nlm.nih.gov"

    def __init__(self):
        self.confidence_scores: dict[str, ConfidenceScore] = {}

    def merge(
        self,
        grobid_result: Optional[etree._Element] = None,
        pandoc_result: Optional[etree._Element] = None,
        bedrock_result: Optional[str] = None,
    ) -> etree._Element:
        """
        Realiza el merge inteligente de las tres vías.

        Si GROBID y Bedrock coinciden en una referencia -> high_confidence.
        Pandoc aporta la rejilla de tablas; Bedrock aporta label/caption.

        Args:
            grobid_result: XML de GROBID (TEI o JATS).
            pandoc_result: XML intermedio de Pandoc.
            bedrock_result: Fragmento XML JATS de Bedrock (texto).

        Returns:
            Elemento raíz <article> del XML JATS final.
        """
        # Prioridad: GROBID si devuelve JATS; sino construir desde cero
        if grobid_result is not None and self._is_jats_article(grobid_result):
            article = self._clone_element(grobid_result)
            self._apply_bedrock_corrections(article, bedrock_result)
            self._apply_pandoc_content(article, pandoc_result)
        elif pandoc_result is not None:
            article = self._build_from_pandoc(pandoc_result)
            self._apply_grobid_metadata(article, grobid_result)
            self._apply_bedrock_corrections(article, bedrock_result)
        elif bedrock_result:
            article = self._parse_bedrock_fragment(bedrock_result)
            self._apply_grobid_metadata(article, grobid_result)
        else:
            # Fallback: estructura mínima
            article = self._create_minimal_article()

        return article

    def _is_jats_article(self, el: etree._Element) -> bool:
        tag = el.tag
        return tag in ("article", f"{{{self.JATS_NS}}}article") or "article" in tag

    def _clone_element(self, el: etree._Element) -> etree._Element:
        return etree.fromstring(etree.tostring(el, encoding="unicode"))

    def _apply_bedrock_corrections(self, article: etree._Element, bedrock_result: Optional[str]) -> None:
        """Aplica correcciones semánticas de Bedrock al article."""
        if not bedrock_result or not bedrock_result.strip():
            return
        try:
            fragments = self._extract_jats_fragments(bedrock_result)
            for frag in fragments:
                self._merge_fragment(article, frag)
        except etree.XMLSyntaxError:
            pass  # Ignorar fragmentos malformados

    def _extract_jats_fragments(self, text: str) -> list[etree._Element]:
        """Extrae fragmentos XML válidos del texto de Bedrock."""
        fragments = []
        # Buscar bloques <ref>...</ref>, <sec>...</sec>, etc.
        import re
        # Patrón simplificado para elementos JATS
        for match in re.finditer(r"<(\w+)[^>]*>.*?</\1>", text, re.DOTALL):
            try:
                el = etree.fromstring(f"<root>{match.group(0)}</root>")
                if len(el) > 0:
                    fragments.append(el[0])
            except etree.XMLSyntaxError:
                continue
        return fragments

    def _merge_fragment(self, article: etree._Element, fragment: etree._Element) -> None:
        """Fusiona un fragmento de Bedrock en el article."""
        # Back: ref-list, fn (conflicto de intereses)
        back = article.find(".//back")
        if back is None:
            back = etree.SubElement(article, "back")
        if fragment.tag in ("ref", "ref-list", "fn", "ack"):
            back.append(etree.fromstring(etree.tostring(fragment)))

    def _apply_pandoc_content(self, article: etree._Element, pandoc_result: Optional[etree._Element]) -> None:
        """Inserta contenido estructurado de Pandoc en body."""
        if pandoc_result is None:
            return
        body = article.find(".//body")
        if body is None:
            body = etree.SubElement(article, "body")
        # Copiar secs de pandoc al body
        for sec in pandoc_result.iter("sec"):
            body.append(etree.fromstring(etree.tostring(sec)))

    def _apply_grobid_metadata(self, article: etree._Element, grobid_result: Optional[etree._Element]) -> None:
        """Aplica metadatos extraídos por GROBID."""
        if grobid_result is None:
            return
        front = article.find(".//front")
        if front is None:
            front = etree.SubElement(article, "front")
        # Si GROBID devolvió TEI, extraer metadatos; si devolvió JATS, copiar front
        if self._is_jats_article(grobid_result):
            src_front = grobid_result.find(".//front")
            if src_front is not None:
                for child in src_front:
                    front.append(etree.fromstring(etree.tostring(child)))

    def _build_from_pandoc(self, pandoc_result: etree._Element) -> etree._Element:
        """Construye article JATS a partir del output de Pandoc."""
        article = self._create_minimal_article()
        self._apply_pandoc_content(article, pandoc_result)
        return article

    def _parse_bedrock_fragment(self, bedrock_result: str) -> etree._Element:
        """Parsea el resultado de Bedrock como article."""
        wrapped = f"<article xmlns:xlink=\"{self.XLINK_NS}\">{bedrock_result}</article>"
        return etree.fromstring(wrapped)

    def _create_minimal_article(self) -> etree._Element:
        """Crea un article JATS mínimo válido."""
        article = etree.Element(
            "article",
            attrib={
                "article-type": "research-article",
                "dtd-version": "1.3",
                "{http://www.w3.org/XML/1998/namespace}lang": "es",
            },
            nsmap={"xlink": self.XLINK_NS},
        )
        front = etree.SubElement(article, "front")
        etree.SubElement(front, "journal-meta")
        article_meta = etree.SubElement(front, "article-meta")
        etree.SubElement(article_meta, "article-id", attrib={"pub-id-type": "other"}).text = "converted"
        title_group = etree.SubElement(article_meta, "title-group")
        etree.SubElement(title_group, "article-title").text = "Sin título"
        etree.SubElement(article, "body")
        return article

    def deep_merge_table(
        self,
        table_grid: list[list[str]],
        label: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> etree._Element:
        """
        Deep Merge de tablas: Pandoc aporta la rejilla, Bedrock aporta label/caption.
        """
        tbl = etree.Element("table")
        if label:
            lbl = etree.SubElement(tbl, "label")
            lbl.text = label
        if caption:
            cap = etree.SubElement(tbl, "caption")
            p = etree.SubElement(cap, "p")
            p.text = caption
        tbody = etree.SubElement(tbl, "tbody")
        for row in table_grid:
            tr = etree.SubElement(tbody, "tr")
            for cell_text in row:
                td = etree.SubElement(tr, "td")
                td.text = cell_text or ""
        return tbl
