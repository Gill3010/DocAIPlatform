#!/bin/bash
REGION="us-east-2"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="document-converter"
IMAGE_TAG="latest"

echo "🚀 Iniciando despliegue..."

aws ecr create-repository --repository-name $ECR_REPO --region $REGION 2>/dev/null || echo "Repositorio ya existe"

echo "🔐 Autenticando con ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "🔨 Construyendo imagen Docker..."
cd $(dirname $0)/../docker
docker build -t $ECR_REPO:$IMAGE_TAG .

echo "🏷️ Etiquetando imagen..."
docker tag $ECR_REPO:$IMAGE_TAG $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

echo "⬆️ Subiendo imagen a ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

echo "✅ Imagen subida exitosamente!"
echo "URI: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
cd - > /dev/null
