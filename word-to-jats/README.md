# Word-to-JATS Conversion Platform

Plataforma de conversión de Word a XML JATS de alta precisión, compatible con OJS 3.x.

## Arquitectura

- **Vía Estructural (GROBID):** Metadatos y bibliografía.
- **Vía de Contenido (Pandoc):** Estructura de estilos Word → XML.
- **Vía Semántica (Bedrock/Claude 3.5 Sonnet):** Corrección semántica, tablas, IMRaD.

## Requisitos

- Python 3.12+
- AWS CLI configurado
- Node.js (para CDK)
- Pandoc (para vía de contenido): `apt install pandoc`

## Instalación

```bash
cd word-to-jats
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Deploy AWS

```bash
./scripts/deploy.sh
```

O manualmente:

```bash
pip install aws-cdk-lib constructs
cdk bootstrap
cdk deploy
```

## Validación

```bash
xmllint --schema https://jats.nlm.nih.gov/publishing/1.3/xsd/JATS-journalpublishing1-3.xsd output.xml
```

## Integración con DocAI

El módulo se integra con el backend FastAPI existente mediante un servicio que invoca la Step Function o ejecuta la conversión de forma local/síncrona.
