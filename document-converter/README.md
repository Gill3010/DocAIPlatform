# Sistema de Conversión de Documentos AWS

Sistema de conversión de documentos usando **ECS Fargate + LibreOffice** en AWS (us-east-2).

## Formatos Soportados

- PDF ↔ Word
- Excel → PDF
- PowerPoint → PDF
- PDF → Excel, PDF → PowerPoint
- PDF → Texto, Word → Texto, Texto → Word

## Estructura del Proyecto

```
document-converter/
├── docker/
│   ├── Dockerfile      # Imagen Ubuntu + LibreOffice + AWS CLI
│   ├── converter.py    # Lógica de conversión
│   └── requirements.txt
├── scripts/
│   ├── deploy.sh       # Build y push a ECR
│   ├── setup-ecs.sh    # Cluster ECS, buckets S3, task definition
│   └── test-conversion.sh  # Ejecuta tarea de prueba
└── docs/
    └── IAM-PERMISOS-REQUERIDOS.md
```

## Requisitos Previos

1. **Permisos IAM** - Ver `docs/IAM-PERMISOS-REQUERIDOS.md`
2. **Docker** ejecutándose (`sudo systemctl start docker`)
3. **AWS CLI** configurado

## Despliegue

```bash
chmod +x scripts/*.sh
./scripts/deploy.sh      # Construye y sube imagen a ECR
./scripts/setup-ecs.sh   # Configura ECS, S3, IAM
./scripts/test-conversion.sh  # Prueba la conversión
```

## Uso del Conversor

El contenedor acepta un evento JSON vía argumento:

```bash
# Ejemplo (desde una tarea ECS o Lambda que invoque el contenedor)
python3 converter.py '{"input_key": "docs/archivo.pdf", "output_format": "docx"}'
```

Los archivos se leen de `INPUT_BUCKET` y se escriben en `OUTPUT_BUCKET/converted/`.

## Costo Estimado

< $5/mes con créditos disponibles (~$131).

## Validaciones Post-Despliegue

- [ ] Imagen en ECR: `aws ecr describe-images --repository-name document-converter --region us-east-2`
- [ ] Cluster ECS activo: `aws ecs describe-clusters --cluster document-converter-cluster --region us-east-2`
- [ ] Buckets S3: `aws s3 ls | grep docai-converter`
- [ ] Logs CloudWatch: `/ecs/document-converter`
