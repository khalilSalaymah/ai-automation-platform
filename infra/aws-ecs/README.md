# AWS ECS Fargate Deployment Guide

This guide will help you deploy the AI Automation Platform to AWS ECS Fargate.

## Prerequisites

1. AWS CLI installed and configured
2. Docker installed
3. AWS account with appropriate permissions:
   - ECS (create cluster, services, task definitions)
   - ECR (create repository, push images)
   - VPC (create subnets, security groups)
   - IAM (create roles, policies)
   - Secrets Manager (create and manage secrets)
   - CloudWatch Logs (create log groups)
   - Application Load Balancer (create ALB, target groups)

## Quick Setup

### 1. Run Initial Setup

```bash
cd infra/aws-ecs
chmod +x setup.sh
./setup.sh
```

This will create:
- ECR repository
- ECS cluster
- CloudWatch log group
- Secrets Manager secret (placeholder)

### 2. Configure Secrets

Update secrets in AWS Secrets Manager:

```bash
# Get secret ARN
SECRET_ARN=$(aws secretsmanager describe-secret --secret-id ai-automation --query ARN --output text)

# Update individual secrets
aws secretsmanager update-secret \
  --secret-id ai-automation/database-url \
  --secret-string "postgresql://user:pass@rds-endpoint:5432/ai_agents"

aws secretsmanager update-secret \
  --secret-id ai-automation/redis-url \
  --secret-string "redis://elasticache-endpoint:6379/0"

aws secretsmanager update-secret \
  --secret-id ai-automation/secret-key \
  --secret-string "$(openssl rand -hex 32)"

aws secretsmanager update-secret \
  --secret-id ai-automation/openai-api-key \
  --secret-string "your-openai-api-key"

aws secretsmanager update-secret \
  --secret-id ai-automation/frontend-url \
  --secret-string "https://your-domain.com"
```

Or use a JSON file:

```json
{
  "database-url": "postgresql://user:pass@rds-endpoint:5432/ai_agents",
  "redis-url": "redis://elasticache-endpoint:6379/0",
  "secret-key": "your-secret-key-here",
  "openai-api-key": "your-openai-api-key",
  "frontend-url": "https://your-domain.com"
}
```

```bash
aws secretsmanager update-secret \
  --secret-id ai-automation \
  --secret-string file://secrets.json
```

### 3. Create IAM Roles

#### Task Execution Role

```bash
# Create trust policy
cat > trust-policy.json <<EOF
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
EOF

# Create role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://trust-policy.json

# Attach managed policy
aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Add Secrets Manager access
aws iam put-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-name SecretsManagerAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": "*"
      }
    ]
  }'
```

#### Task Role (for application)

```bash
aws iam create-role \
  --role-name ecsTaskRole \
  --assume-role-policy-document file://trust-policy.json

# Add any additional permissions your app needs
```

### 4. Create VPC Infrastructure

You can use the Terraform module in `infra/terraform/` or create manually:

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query Vpc.VpcId --output text)

# Create subnets (at least 2 in different AZs)
SUBNET_1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --query Subnet.SubnetId --output text)
SUBNET_2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --query Subnet.SubnetId --output text)

# Create internet gateway
IGW_ID=$(aws ec2 create-internet-gateway --query InternetGateway.InternetGatewayId --output text)
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create route table
RT_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query RouteTable.RouteTableId --output text)
aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Associate subnets
aws ec2 associate-route-table --subnet-id $SUBNET_1 --route-table-id $RT_ID
aws ec2 associate-route-table --subnet-id $SUBNET_2 --route-table-id $RT_ID

# Create security group
SG_ID=$(aws ec2 create-security-group --group-name ai-automation-sg --description "Security group for AI Automation Platform" --vpc-id $VPC_ID --query GroupId --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8080 --cidr 0.0.0.0/0
```

### 5. Create Application Load Balancer

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name ai-automation-alb \
  --subnets $SUBNET_1 $SUBNET_2 \
  --security-groups $SG_ID \
  --query LoadBalancers[0].LoadBalancerArn \
  --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name ai-automation-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --query TargetGroups[0].TargetGroupArn \
  --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

### 6. Update Configuration Files

Update `task-definition.json`:
- Replace `YOUR_ACCOUNT_ID` with your AWS account ID
- Replace `REGION` with your AWS region
- Update secret ARNs if using different secret names
- Update execution and task role ARNs

Update `service-definition.json`:
- Replace subnet IDs
- Replace security group ID
- Replace target group ARN
- Update cluster name if different

### 7. Register Task Definition

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json \
  --region us-east-1
```

### 8. Create ECS Service

```bash
aws ecs create-service \
  --cli-input-json file://service-definition.json \
  --region us-east-1
```

### 9. Deploy Updates

```bash
chmod +x deploy.sh
./deploy.sh
```

Or manually:

```bash
# Build and push image
docker build -f infra/aws-ecs/Dockerfile -t ai-automation-platform:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag ai-automation-platform:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-automation-platform:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ai-automation-platform:latest

# Update service
aws ecs update-service \
  --cluster ai-automation-cluster \
  --service ai-automation-platform \
  --force-new-deployment \
  --region us-east-1
```

## Using Terraform

For a complete infrastructure setup, use the Terraform module:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

See `infra/terraform/README.md` for details.

## Environment Variables

All sensitive values should be stored in AWS Secrets Manager and referenced in the task definition.

Required secrets:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key
- `OPENAI_API_KEY` - OpenAI API key
- `FRONTEND_URL` - Frontend application URL

Optional secrets:
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_REDIRECT_URI` - OAuth redirect URI

## Monitoring

### CloudWatch Logs

```bash
# View logs
aws logs tail /ecs/ai-automation-platform --follow --region us-east-1
```

### ECS Service Metrics

View in AWS Console:
- ECS → Clusters → ai-automation-cluster → Services → ai-automation-platform → Metrics

### Application Load Balancer Metrics

View in CloudWatch:
- ALB → ai-automation-alb → Monitoring

## Scaling

### Manual Scaling

```bash
aws ecs update-service \
  --cluster ai-automation-cluster \
  --service ai-automation-platform \
  --desired-count 4 \
  --region us-east-1
```

### Auto Scaling

Create auto-scaling configuration:

```bash
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/ai-automation-cluster/ai-automation-platform \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/ai-automation-cluster/ai-automation-platform \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

## Troubleshooting

### Service Won't Start

1. Check task logs in CloudWatch
2. Verify secrets are accessible
3. Check security group rules
4. Verify task definition is correct

### Container Health Check Failing

1. Verify `/health` endpoint exists
2. Check container logs
3. Verify port mapping is correct
4. Check security group allows traffic

### Image Pull Errors

1. Verify ECR repository exists
2. Check IAM permissions for ECR
3. Verify image tag is correct

## Cost Optimization

- Use Fargate Spot for non-production workloads
- Right-size CPU and memory based on actual usage
- Use CloudWatch Insights to analyze costs
- Enable auto-scaling to scale down during low traffic

## Security Best Practices

1. Use Secrets Manager for all sensitive data
2. Enable VPC flow logs
3. Use security groups to restrict access
4. Enable CloudTrail for audit logging
5. Regularly rotate secrets
6. Use least-privilege IAM roles
