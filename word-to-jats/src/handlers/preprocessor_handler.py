"""
Pre-processor Lambda - Ingesta y distribución inicial.

Recibe el documento Word, lo limpia y prepara para las tres vías.
Guarda en S3 y devuelve referencias para el Merger.
"""
from typing import Any
import os
import json
import uuid
from pathlib import Path

# Lambda se ejecuta con src/handlers como raíz cuando el asset es handlers/
# Por tanto los imports relativos al proyecto deben ajustarse


def handler(event: dict, context: Any) -> dict:
    """
    Lambda handler para el pre-procesador.

    Espera event con:
    - bucket: nombre del bucket S3 de entrada
    - key: clave del objeto (documento Word)

    O para invocación directa:
    - body (base64) del documento

    Devuelve:
    - job_id, input_key, output_prefix, file_ext
    """
    input_bucket = os.environ.get("INPUT_BUCKET", "")
    output_bucket = os.environ.get("OUTPUT_BUCKET", "")

    if not input_bucket or not output_bucket:
        return {
            "statusCode": 500,
            "error": "INPUT_BUCKET or OUTPUT_BUCKET not configured",
            "job_id": None,
        }

    job_id = str(uuid.uuid4())

    # Si el event viene de API Gateway/Step Functions con bucket/key
    bucket = event.get("bucket") or event.get("input_bucket") or input_bucket
    key = event.get("key") or event.get("input_key", "")

    if not key:
        return {
            "statusCode": 400,
            "error": "Missing input key (S3 object key)",
            "job_id": job_id,
        }

    # Determinar extensión
    ext = Path(key).suffix.lower().replace(".", "") or "docx"
    if ext not in ("docx", "doc", "pdf"):
        return {
            "statusCode": 400,
            "error": f"Unsupported format: {ext}",
            "job_id": job_id,
        }

    output_prefix = f"jobs/{job_id}"

    return {
        "statusCode": 200,
        "job_id": job_id,
        "bucket": bucket,
        "key": key,
        "output_bucket": output_bucket,
        "output_prefix": output_prefix,
        "file_ext": ext,
    }
