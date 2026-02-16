# Permisos IAM Requeridos para el Sistema de Conversión de Documentos

## Problema Detectado

El rol `EC2-SessionManager-Role` asociado a la instancia no tiene permisos para:
- **ECR**: `ecr:GetAuthorizationToken` (autenticación Docker)
- **ECR**: `ecr:BatchGetImage`, `ecr:PutImage`, `ecr:InitiateLayerUpload`, etc. (push de imágenes)

## Solución: Política IAM a Adjuntar

Crea una política IAM con el siguiente JSON y adjuntala al rol de la instancia EC2 (o usa AWS CloudShell que tiene credenciales con permisos amplios):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:DescribeImages"
      ],
      "Resource": "arn:aws:ecr:us-east-2:766092484543:repository/document-converter"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:CreateCluster",
        "ecs:DescribeClusters",
        "ecs:RegisterTaskDefinition",
        "ecs:RunTask",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "iam:GetRole",
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::766092484543:role/ecsTaskExecutionRole",
        "arn:aws:iam::766092484543:role/ecsTaskS3Role"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::docai-converter-input-766092484543",
        "arn:aws:s3:::docai-converter-input-766092484543/*",
        "arn:aws:s3:::docai-converter-output-766092484543",
        "arn:aws:s3:::docai-converter-output-766092484543/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:DescribeLogGroups",
        "logs:PutLogEvents",
        "logs:CreateLogStream"
      ],
      "Resource": "arn:aws:logs:us-east-2:766092484543:log-group:/ecs/document-converter:*"
    }
  ]
}
```

## Alternativa: Ejecutar en AWS CloudShell

Si prefieres no modificar el rol de la instancia, ejecuta los scripts desde **AWS CloudShell** (disponible en la consola AWS), que tiene credenciales con permisos suficientes:

1. Abre AWS CloudShell en la consola (us-east-2)
2. Clona o copia el proyecto `document-converter`
3. Ejecuta: `./scripts/deploy.sh` luego `./scripts/setup-ecs.sh` y `./scripts/test-conversion.sh`

## Comandos para aplicar permisos (desde cuenta con acceso IAM)

```bash
# Crear la política
aws iam create-policy \
  --policy-name DocumentConverterDeployPolicy \
  --policy-document file://iam-policy.json

# Adjuntar al rol de la instancia (reemplaza con el nombre real del rol)
aws iam attach-role-policy \
  --role-name EC2-SessionManager-Role \
  --policy-arn arn:aws:iam::766092484543:policy/DocumentConverterDeployPolicy
```

**Nota**: Si no tienes permisos para modificar IAM, contacta al administrador de la cuenta AWS.
