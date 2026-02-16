#!/bin/bash
REGION="us-east-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CLUSTER_NAME="document-converter-cluster"
SERVICE_NAME="document-converter-service"
TASK_FAMILY="document-converter-task"

echo "🏗️ Configurando infraestructura ECS..."

aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $REGION 2>/dev/null || echo "Cluster ya existe"

echo "👤 Creando rol IAM..."
cat > /tmp/trust-policy.json << 'TRUST'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
TRUST

aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document file:///tmp/trust-policy.json 2>/dev/null || echo "Rol ya existe"
aws iam attach-role-policy --role-name ecsTaskExecutionRole --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy 2>/dev/null || true

# Crear rol para acceso S3 (task role)
aws iam create-role --role-name ecsTaskS3Role --assume-role-policy-document file:///tmp/trust-policy.json 2>/dev/null || echo "Rol S3 ya existe"

cat > /tmp/s3-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::docai-converter-input-$ACCOUNT_ID",
        "arn:aws:s3:::docai-converter-input-$ACCOUNT_ID/*",
        "arn:aws:s3:::docai-converter-output-$ACCOUNT_ID",
        "arn:aws:s3:::docai-converter-output-$ACCOUNT_ID/*"
      ]
    }
  ]
}
EOF

aws iam put-role-policy --role-name ecsTaskS3Role --policy-name S3Access --policy-document file:///tmp/s3-policy.json 2>/dev/null || true

echo "🪣 Creando buckets S3..."
aws s3 mb s3://docai-converter-input-$ACCOUNT_ID --region $REGION 2>/dev/null || echo "Bucket input ya existe"
aws s3 mb s3://docai-converter-output-$ACCOUNT_ID --region $REGION 2>/dev/null || echo "Bucket output ya existe"

echo "📝 Creando task definition..."
# Usar ARM64 para compatibilidad con instancia t4g
cat > /tmp/task-definition.json << TASK
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "2048",
  "runtimePlatform": {
    "cpuArchitecture": "ARM64",
    "operatingSystemFamily": "LINUX"
  },
  "executionRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::$ACCOUNT_ID:role/ecsTaskS3Role",
  "containerDefinitions": [
    {
      "name": "document-converter",
      "image": "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/document-converter:latest",
      "essential": true,
      "environment": [
        {
          "name": "INPUT_BUCKET",
          "value": "docai-converter-input-$ACCOUNT_ID"
        },
        {
          "name": "OUTPUT_BUCKET",
          "value": "docai-converter-output-$ACCOUNT_ID"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/document-converter",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
TASK

aws logs create-log-group --log-group-name /ecs/document-converter --region $REGION 2>/dev/null || echo "Log group ya existe"
aws ecs register-task-definition --cli-input-json file:///tmp/task-definition.json --region $REGION

echo "✅ Infraestructura ECS configurada!"
