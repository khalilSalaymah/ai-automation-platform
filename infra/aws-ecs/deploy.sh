#!/bin/bash
# Deployment script for AWS ECS Fargate

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="${ECR_REPO:-ai-automation-platform}"
CLUSTER_NAME="${CLUSTER_NAME:-ai-automation-cluster}"
SERVICE_NAME="${SERVICE_NAME:-ai-automation-platform}"
TASK_FAMILY="${TASK_FAMILY:-ai-automation-platform}"

echo "🚀 Starting deployment to AWS ECS Fargate..."

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "📦 Building Docker image..."
docker build -f infra/aws-ecs/Dockerfile -t ${ECR_REPO}:latest .

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}

echo "📤 Pushing image to ECR..."
docker tag ${ECR_REPO}:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

echo "📝 Updating task definition..."
# Get the current task definition
TASK_DEF=$(aws ecs describe-task-definition --task-definition ${TASK_FAMILY} --region ${AWS_REGION})
TASK_DEF_REVISION=$(echo $TASK_DEF | jq -r '.taskDefinition.revision')

# Create new task definition with updated image
NEW_TASK_DEF=$(echo $TASK_DEF | jq --arg IMAGE "${ECR_URI}:latest" '.taskDefinition | .containerDefinitions[0].image = $IMAGE | del(.taskDefinitionArn) | del(.revision) | del(.status) | del(.requiresAttributes) | del(.compatibilities) | del(.registeredAt) | del(.registeredBy)')

# Register new task definition
aws ecs register-task-definition \
  --region ${AWS_REGION} \
  --cli-input-json "$NEW_TASK_DEF" > /dev/null

NEW_TASK_DEF_REVISION=$(aws ecs describe-task-definition --task-definition ${TASK_FAMILY} --region ${AWS_REGION} | jq -r '.taskDefinition.revision')

echo "🔄 Updating ECS service..."
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service ${SERVICE_NAME} \
  --task-definition ${TASK_FAMILY}:${NEW_TASK_DEF_REVISION} \
  --force-new-deployment \
  --region ${AWS_REGION} > /dev/null

echo "⏳ Waiting for service to stabilize..."
aws ecs wait services-stable \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION}

echo "✅ Deployment complete!"
echo "📊 Service status:"
aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query 'services[0].[status,runningCount,desiredCount]' \
  --output table
