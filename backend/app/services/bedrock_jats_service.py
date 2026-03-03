"""
Servicio Bedrock para conversión Word → JATS XML.

Cuando USE_BEDROCK_FOR_JATS=true y hay tokens disponibles, usa Claude para
producir XML JATS de mayor calidad. Si falla (sin tokens, error, timeout),
el llamador hace fallback a DocxToJATSConverter.
"""
import json
import re
import zipfile
from pathlib import Path
from typing import Optional, Tuple

from docx import Document
from lxml import etree

# Namespace JATS
JATS_NS = "http://jats.nlm.nih.gov"
XLINK_NS = "http://www.w3.org/1999/xlink"
NSMAP = {None: JATS_NS, "xlink": XLINK_NS}

BEDROCK_SYSTEM_PROMPT = """Eres un experto en JATS 1.1 (NISO Z39.96) para publicaciones académicas.

Tu tarea: convertir el contenido de un manuscrito académico (extraído de Word) a XML JATS válido.

Reglas obligatorias:
1. Genera XML JATS 1.1 completo: article, front (journal-meta, article-meta), body, back.
2. En journal-meta: journal-id, journal-title-group, Y SIEMPRE publisher con publisher-name (requerido por OJS Lens).
3. En article-meta: title-group, contrib-group (autores con contrib-type="author", name, surname, given-names), abstract.
4. Mapea secciones IMRaD a sec sec-type: intro, methods, results, discussion, conclusions.
5. Para referencias: ref-list con ref id="B1", "B2"... y elements apropiados (element-citation, etc.).
6. Usa namespace: xmlns="http://jats.nlm.nih.gov" y xlink para href.
7. Devuelve ÚNICAMENTE el XML, sin explicaciones, sin markdown, sin ```xml.
8. Si hay N figuras, incluye en back: <fig id="fig1"><label>Figura 1</label><graphic xlink:href="FIG_PLACEHOLDER_1"/></fig> ... (el llamador reemplazará placeholders)."""


class BedrockJatsError(Exception):
    """Error al usar Bedrock para conversión JATS."""


def _extract_structured_text(doc: Document) -> str:
    """Extrae texto estructurado del Word para enviar a Bedrock."""
    from docx.oxml.ns import qn
    from docx.table import Table as DocxTable
    from docx.text.paragraph import Paragraph as DocxParagraph

    section_keywords = {"introducción", "introduction", "metodología", "methodology", "resultados", "results",
                       "conclusión", "conclusion", "discusión", "discussion", "referencias", "references"}
    body_parts = []
    refs_started = False

    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            para = DocxParagraph(child, doc)
            t = (para.text or "").strip()
            if not t:
                continue
            lower = t.lower()
            if any(k in lower for k in ["referencias", "references", "bibliografía", "bibliography"]):
                refs_started = True
                body_parts.append("\n## REFERENCES\n")
                continue
            if refs_started:
                body_parts.append(f"[REF] {t}")
                continue
            if any(k in lower for k in section_keywords) and len(t) < 100:
                body_parts.append(f"\n## {t}\n")
            else:
                body_parts.append(t)
        elif child.tag == qn("w:tbl"):
            tbl = DocxTable(child, doc)
            rows = []
            for r in tbl.rows:
                rows.append(" | ".join((c.text or "").strip() for c in r.cells))
            if rows:
                body_parts.append("[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]")

    return "\n".join(body_parts)[:80000]


def _extract_images_from_docx(input_path: str, output_base: str, output_dir: Path) -> list:
    """Extrae imágenes del DOCX y las guarda. Retorna lista de nombres de archivo."""
    result = []
    try:
        with zipfile.ZipFile(input_path, "r") as z:
            for i, name in enumerate(z.namelist(), 1):
                if not name.startswith("word/media/"):
                    continue
                data = z.read(name)
                ext = Path(name).suffix.lstrip(".").lower() or "png"
                if ext not in ("png", "jpeg", "jpg", "gif"):
                    ext = "png"
                fn = f"{output_base}_image_{i}.{ext}"
                (output_dir / fn).write_bytes(data)
                result.append(fn)
    except Exception:
        pass
    return result


def convert_docx_to_jats_via_bedrock(
    input_path: str,
    output_path: str,
    region: str = "us-east-1",
    model_id: str = "anthropic.claude-sonnet-4-20250514-v1:0",
) -> bool:
    """
    Convierte DOCX a JATS XML usando AWS Bedrock (Claude).
    Extrae imágenes localmente y las integra en el XML.
    """
    output_dir = Path(output_path).parent
    output_base = Path(output_path).stem
    
    doc = Document(input_path)
    structured_text = _extract_structured_text(doc)
    
    # Extraer imágenes (siempre local)
    image_filenames = _extract_images_from_docx(input_path, output_base, output_dir)
    
    user_prompt = f"""Convierte este manuscrito académico a XML JATS 1.1 completo.

Documento tiene {len(image_filenames)} figura(s). En back, incluye para cada una:
<fig id="figN"><label>Figura N</label><graphic xlink:href="nombre_archivo"/></fig>
Usa los nombres: {', '.join(image_filenames) if image_filenames else 'ninguna'}.

CONTENIDO:

{structured_text}"""

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise BedrockJatsError("boto3 no instalado")

    client = boto3.client("bedrock-runtime", region_name=region)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
        "temperature": 0.2,
        "system": BEDROCK_SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
        ],
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if "ThrottlingException" in code or "AccessDeniedException" in code or "ValidationException" in code:
            raise BedrockJatsError(f"Bedrock no disponible: {e}") from e
        raise BedrockJatsError(str(e)) from e

    response_body = json.loads(response["body"].read())
    if "content" not in response_body or not response_body["content"]:
        raise BedrockJatsError("Respuesta vacía de Bedrock")

    raw_text = response_body["content"][0]["text"].strip()
    # Quitar posible markdown
    raw_text = re.sub(r"^```(?:xml)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    # Extraer XML (puede venir envuelto)
    xml_match = re.search(r"<article[\s>].*</article>", raw_text, re.DOTALL | re.IGNORECASE)
    if xml_match:
        xml_str = xml_match.group(0)
    else:
        xml_str = raw_text

    # Asegurar namespace si no lo tiene
    if 'xmlns=' not in xml_str[:200]:
        xml_str = xml_str.replace("<article", '<article xmlns="http://jats.nlm.nih.gov"', 1)

    # Parsear y validar
    try:
        root = etree.fromstring(xml_str.encode("utf-8"))
    except etree.XMLSyntaxError as e:
        raise BedrockJatsError(f"XML inválido de Bedrock: {e}") from e

    # Asegurar publisher-name (requerido por OJS Lens; querySelector lo busca)
    jats_ns = "http://jats.nlm.nih.gov"
    journal_meta = root.find(f".//{{{jats_ns}}}journal-meta") or root.find(".//journal-meta")
    if journal_meta is not None:
        pub_name = journal_meta.find(f".//{{{jats_ns}}}publisher-name") or journal_meta.find(".//publisher-name")
        if pub_name is None:
            publisher = journal_meta.find(f".//{{{jats_ns}}}publisher") or journal_meta.find(".//publisher")
            if publisher is None:
                publisher = etree.SubElement(journal_meta, f"{{{jats_ns}}}publisher")
            pub_elem = etree.SubElement(publisher, f"{{{jats_ns}}}publisher-name")
            pub_elem.text = "Article"

    # Escribir XML
    tree = etree.ElementTree(root)
    tree.write(
        output_path,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8",
        doctype='<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" "https://jats.nlm.nih.gov/publishing/1.1/JATS-journalpublishing1.dtd">',
    )
    return True
