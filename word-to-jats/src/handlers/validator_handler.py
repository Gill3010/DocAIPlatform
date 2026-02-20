"""
Validator Lambda - Valida el XML JATS generado.

Verifica esquema JATS 1.3 y reglas de dominio.
Devuelve quality_score; si < 0.95 puede disparar Human Review.
"""
from typing import Any
import os
from pathlib import Path

import boto3

import sys
_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from core.jats_schema_validator import JatsSchemaValidator, ValidationResult


def handler(event: dict, context: Any) -> dict:
    """
    Lambda handler para el Validador.

    Espera el output del Merger:
    - job_id, output_key, quality_score (opcional)

    Descarga el XML de S3, valida, y devuelve resultado.
    """
    output_bucket = os.environ.get("OUTPUT_BUCKET", "")

    payload = event.get("Payload") if "Payload" in event else event
    job_id = payload.get("job_id", "")
    output_key = payload.get("output_key", "")
    if not output_key:
        output_key = f"jobs/{job_id}/output.xml"

    if not output_bucket:
        return {"statusCode": 500, "error": "OUTPUT_BUCKET not configured", "quality_score": 0.0}

    s3 = boto3.client("s3")

    try:
        obj = s3.get_object(Bucket=output_bucket, Key=output_key)
        xml_content = obj["Body"].read()

        # XSD path opcional (puede estar en schema/ dentro del deployment)
        schema_dir = Path(__file__).resolve().parent.parent.parent / "schema"
        xsd_path = schema_dir / "JATS-journalpublishing1-3.xsd" if schema_dir.exists() else None
        if xsd_path and not xsd_path.exists():
            xsd_path = None

        validator = JatsSchemaValidator(xsd_path=xsd_path)
        result = validator.validate(xml_content=xml_content)

        return {
            "statusCode": 200 if result.is_valid else 422,
            "job_id": job_id,
            "is_valid": result.is_valid,
            "quality_score": result.quality_score,
            "errors": result.errors,
            "warnings": result.warnings,
            "needs_human_review": result.quality_score < 0.95,
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e),
            "job_id": job_id,
            "quality_score": 0.0,
            "needs_human_review": True,
        }
