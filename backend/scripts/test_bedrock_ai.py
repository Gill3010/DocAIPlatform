#!/usr/bin/env python3
"""
Prueba de conexión a Bedrock para el Asistente IA.
Ejecutar desde raíz: python3 backend/scripts/test_bedrock_ai.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def main():
    region = getattr(settings, "BEDROCK_REGION", "us-east-2")
    model_id = getattr(settings, "BEDROCK_MODEL_ID", "anthropic.claude-sonnet-4-20250514-v1:0")
    print(f"Región: {region}, Modelo: {model_id}")
    print("Intentando invocar Bedrock...")
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("ERROR: boto3 no instalado. pip install boto3")
        sys.exit(1)

    client = boto3.client("bedrock-runtime", region_name=region)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": [{"type": "text", "text": "Di hola"}]}],
    }
    try:
        resp = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        data = json.loads(resp["body"].read())
        text = data.get("content", [{}])[0].get("text", "")
        print("OK:", text[:100] if text else "(vacío)")
        print("Bedrock funciona correctamente.")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        print(f"ERROR Bedrock ({code}): {e}")
        print("\nPosibles causas:")
        print("- Habilitar el modelo en AWS Console > Bedrock > Model access")
        print("- Verificar IAM: la instancia necesita bedrock:InvokeModel")
        print("- Comprobar que el modelo existe en la región", region)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
