#!/bin/bash
# Initial setup script for AWS ECS Fargate deployment

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPO="${ECR_REPO:-ai-automation-platform}"
CLUSTER_NAME="${CLUSTER_NAME:-ai-automation-cluster}"
SERVICE_NAME="${SERVICE_NAME:-ai-automation-platform}"

echo "🔧 Setting up AWS ECS Fargate infrastructure..."

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
echo "📦 Creating ECR repository..."
aws ecr create-repository \
  --repository-name ${ECR_REPO} \
  --region ${AWS_REGION} \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 2>/dev/null || echo "Repository already exists"

# Create ECS cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster \
  --cluster-name ${CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 2>/dev/null || echo "Cluster already exists"

# Create CloudWatch log group
echo "📝 Creating CloudWatch log group..."
aws logs create-log-group \
  --log-group-name /ecs/${SERVICE_NAME} \
  --region ${AWS_REGION} 2>/dev/null || echo "Log group already exists"

# Create secrets in Secrets Manager
echo "🔐 Setting up secrets in Secrets Manager..."
SECRET_NAME="ai-automation"

# Check if secret exists
if ! aws secretsmanager describe-secret --secret-id ${SECRET_NAME} --region ${AWS_REGION} &>/dev/null; then
  echo "Creating secret ${SECRET_NAME}..."
  aws secretsmanager create-secret \
    --name ${SECRET_NAME} \
    --description "Secrets for AI Automation Platform" \
    --secret-string '{
      "database-url": "CHANGE_ME",
      "redis-url": "CHANGE_ME",
      "secret-key": "CHANGE_ME",
      "openai-api-key": "CHANGE_ME",
      "frontend-url": "CHANGE_ME"
    }' \
    --region ${AWS_REGION}
  
  echo "⚠️  Please update secrets in AWS Secrets Manager:"
  echo "   aws secretsmanager update-secret --secret-id ${SECRET_NAME} --secret-string file://secrets.json"
else
  echo "Secret ${SECRET_NAME} already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update secrets in AWS Secrets Manager"
echo "2. Create VPC, subnets, and security groups (or use Terraform)"
echo "3. Create Application Load Balancer and target group"
echo "4. Update task-definition.json with your ARNs"
echo "5. Update service-definition.json with your subnet and security group IDs"
echo "6. Register task definition: aws ecs register-task-definition --cli-input-json file://task-definition.json"
echo "7. Create service: aws ecs create-service --cli-input-json file://service-definition.json"
echo ""
echo "Or use the Terraform module in infra/terraform/ for complete infrastructure setup."
