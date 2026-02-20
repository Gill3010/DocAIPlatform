"""
Merger Lambda - Invoca JatsMerger y orquesta las tres vías.

Lee el resultado del pre-processor, descarga el Word desde S3,
invoca GROBID (si está disponible), Pandoc y Bedrock,
y fusiona los resultados con JatsMerger.
"""
from typing import Any
import os
import json
import tempfile
import subprocess
from pathlib import Path

import boto3
from lxml import etree

# Imports relativos al paquete src
import sys
# Añadir el directorio padre para imports cuando Lambda tiene src como raíz
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.jats_merger import JatsMerger
from adapters.grobid_client import GrobidClient, GrobidClientError
from adapters.bedrock_client import BedrockClient, BedrockClientError


def handler(event: dict, context: Any) -> dict:
    """
    Lambda handler para el Merger.

    Espera el output del pre-processor:
    - job_id, bucket, key, output_bucket, output_prefix, file_ext
    """
    output_bucket = os.environ.get("OUTPUT_BUCKET", "")
    grobid_url = os.environ.get("GROBID_URL", "http://localhost:8070")

    # Obtener payload del Step Function o invocación directa
    payload = event.get("Payload") if "Payload" in event else event
    job_id = payload.get("job_id", "")
    bucket = payload.get("bucket", "")
    key = payload.get("key", "")
    out_prefix = payload.get("output_prefix", f"jobs/{job_id}")
    file_ext = payload.get("file_ext", "docx")

    if not job_id or not key:
        return {"statusCode": 400, "error": "Missing job_id or key", "quality_score": 0.0}

    s3 = boto3.client("s3")

    try:
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as tmp:
            s3.download_file(bucket, key, tmp.name)
            doc_path = tmp.name

        with open(doc_path, "rb") as f:
            doc_bytes = f.read()

        merger = JatsMerger()
        grobid_result = None
        pandoc_result = None
        bedrock_result = None

        # Vía GROBID
        try:
            grobid = GrobidClient(base_url=grobid_url)
            if grobid.is_alive():
                grobid_result = grobid.process_document(doc_bytes, f"doc.{file_ext}")
        except GrobidClientError:
            pass

        # Vía Pandoc (conversión Word -> JATS XML)
        try:
            pandoc_result = _run_pandoc(doc_path)
        except Exception:
            pass

        # Vía Bedrock (fragmento de texto para enriquecimiento semántico)
        try:
            bedrock = BedrockClient()
            # Extraer texto plano para Bedrock (simplificado)
            text_sample = _extract_text_sample(doc_bytes, file_ext)
            if text_sample:
                bedrock_result = bedrock.convert_fragment_to_jats(text_sample)
        except BedrockClientError:
            pass

        article = merger.merge(
            grobid_result=grobid_result,
            pandoc_result=pandoc_result,
            bedrock_result=bedrock_result,
        )

        # Serializar XML
        xml_bytes = etree.tostring(
            article,
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=True,
            method="xml",
        )

        # Subir a S3
        out_key = f"{out_prefix}/output.xml"
        s3.put_object(
            Bucket=output_bucket,
            Key=out_key,
            Body=xml_bytes,
            ContentType="application/xml",
        )

        return {
            "statusCode": 200,
            "job_id": job_id,
            "output_key": out_key,
            "quality_score": 0.9,  # El validador lo refinará
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e),
            "job_id": job_id,
            "quality_score": 0.0,
        }


def _run_pandoc(doc_path: str) -> etree._Element | None:
    """Ejecuta Pandoc para convertir Word a JATS XML."""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        out_path = tmp.name
    try:
        subprocess.run(
            ["pandoc", doc_path, "-o", out_path, "-t", "jats", "--wrap=none"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        tree = etree.parse(out_path)
        return tree.getroot()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _extract_text_sample(doc_bytes: bytes, ext: str) -> str:
    """Extrae una muestra de texto para Bedrock (máx ~4k caracteres)."""
    if ext == "docx":
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(doc_bytes))
            paras = [p.text for p in doc.paragraphs[:50] if p.text]
            return "\n".join(paras)[:4000]
        except Exception:
            return ""
    return ""
