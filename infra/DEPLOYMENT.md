# Deployment Guide

This guide provides instructions for deploying the AI Automation Platform to various cloud platforms.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Deploy Options](#quick-deploy-options)
  - [Fly.io](#flyio) ⚡ Fastest
  - [Render.com](#rendercom) 🎯 Easiest
  - [AWS ECS Fargate](#aws-ecs-fargate) 🏢 Enterprise
- [Infrastructure as Code](#infrastructure-as-code)
  - [Terraform Module](#terraform-module)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

1. **Application Requirements**:
   - PostgreSQL database (with pgvector extension)
   - Redis instance
   - OpenAI API key
   - Google OAuth credentials (optional)

2. **Platform-Specific Requirements**:
   - See individual platform guides for CLI tools and accounts

## Quick Deploy Options

### Fly.io ⚡

**Best for**: Quick deployments, global edge network, simple scaling

**Time to deploy**: ~10 minutes

**Cost**: Pay-as-you-go, free tier available

#### Quick Start

```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
flyctl auth login

# 3. Navigate to Fly.io config
cd infra/flyio

# 4. Create database and Redis
flyctl postgres create --name ai-automation-db
flyctl redis create --name ai-automation-redis

# 5. Set secrets
flyctl secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  OPENAI_API_KEY="your-key" \
  FRONTEND_URL="https://your-app.fly.dev"

# 6. Deploy
flyctl deploy
```

📖 [Full Fly.io Guide](./flyio/README.md)

---

### Render.com 🎯

**Best for**: Zero-config deployments, automatic SSL, Git-based deploys

**Time to deploy**: ~15 minutes

**Cost**: Free tier available, pay-as-you-go

#### Quick Start

1. **Via Dashboard**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your Git repository
   - Render will detect `render.yaml` automatically
   - Set environment variables in dashboard
   - Click "Apply"

2. **Via CLI**:
   ```bash
   # Install Render CLI
   npm install -g render-cli
   
   # Login
   render login
   
   # Deploy
   cd infra/render
   render blueprint launch
   ```

📖 [Full Render.com Guide](./render/README.md)

---

### AWS ECS Fargate 🏢

**Best for**: Enterprise deployments, AWS ecosystem integration, full control

**Time to deploy**: ~30-45 minutes (first time)

**Cost**: Pay-per-use, can be cost-effective at scale

#### Quick Start

```bash
# 1. Setup infrastructure
cd infra/aws-ecs
chmod +x setup.sh
./setup.sh

# 2. Configure secrets in AWS Secrets Manager
# (See AWS ECS README for details)

# 3. Deploy
chmod +x deploy.sh
./deploy.sh
```

📖 [Full AWS ECS Guide](./aws-ecs/README.md)

---

## Infrastructure as Code

### Terraform Module

For AWS deployments, use the Terraform module to provision managed PostgreSQL and Redis:

```bash
# 1. Configure
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# 2. Initialize
terraform init

# 3. Plan
terraform plan

# 4. Apply
terraform apply

# 5. Get connection strings
terraform output database_url
terraform output redis_url
```

📖 [Full Terraform Guide](./terraform/README.md)

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `SECRET_KEY` | JWT secret key | Generate with `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `FRONTEND_URL` | Frontend application URL | `https://your-app.com` |

### Optional Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth redirect URI |
| `SERVICE_PORT` | Backend service port (default: 8080) |
| `SERVICE_HOST` | Backend service host (default: 0.0.0.0) |

## Database Setup

### PostgreSQL with pgvector

The application requires PostgreSQL with the `pgvector` extension.

#### Using Terraform (AWS)

The Terraform module automatically configures pgvector. After deployment:

```bash
# Connect to database
psql -h $(terraform output -raw database_endpoint) -U postgres -d ai_agents

# Enable extension
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Manual Setup

```sql
-- Connect to your PostgreSQL instance
CREATE DATABASE ai_agents;

-- Connect to the database
\c ai_agents

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Redis

Redis is used for caching and session management. Any Redis 6.0+ instance will work.

## Platform Comparison

| Feature | Fly.io | Render.com | AWS ECS |
|---------|--------|-------------|---------|
| **Setup Time** | ⚡ Fast (~10 min) | ⚡ Fast (~15 min) | 🐢 Slower (~45 min) |
| **Ease of Use** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost (Dev)** | 💰 Low | 💰 Low (Free tier) | 💰 Medium |
| **Cost (Prod)** | 💰 Medium | 💰 Medium | 💰 Low (at scale) |
| **Scaling** | ✅ Auto | ✅ Auto | ✅ Manual/Auto |
| **Global CDN** | ✅ Yes | ✅ Yes | ⚠️ Manual setup |
| **SSL/HTTPS** | ✅ Auto | ✅ Auto | ⚠️ Manual (ALB) |
| **Git Deploy** | ✅ Yes | ✅ Yes | ⚠️ Manual |
| **Enterprise Features** | ⚠️ Limited | ⚠️ Limited | ✅ Full |

## Choosing a Platform

### Choose Fly.io if:
- ✅ You want the fastest deployment
- ✅ You need global edge network
- ✅ You prefer simple CLI-based deployments
- ✅ You want automatic SSL and CDN

### Choose Render.com if:
- ✅ You want zero-configuration deployment
- ✅ You prefer Git-based automatic deploys
- ✅ You want a free tier for development
- ✅ You prefer dashboard-based management

### Choose AWS ECS if:
- ✅ You need enterprise-grade infrastructure
- ✅ You want full control over networking
- ✅ You're already using AWS services
- ✅ You need compliance/certifications
- ✅ You want to use Terraform for infrastructure

## Deployment Checklist

Before deploying to production:

- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Configure `DATABASE_URL` with production database
- [ ] Configure `REDIS_URL` with production Redis
- [ ] Set `FRONTEND_URL` to production domain
- [ ] Enable database backups
- [ ] Configure custom domain with SSL
- [ ] Set up monitoring and alerts
- [ ] Configure CORS appropriately
- [ ] Review security groups/firewall rules
- [ ] Enable logging and log retention
- [ ] Set up CI/CD pipeline
- [ ] Configure auto-scaling (if needed)
- [ ] Test disaster recovery procedures

## Troubleshooting

### Common Issues

#### Database Connection Errors

1. **Check connection string format**:
   ```
   postgresql://username:password@host:port/database
   ```

2. **Verify network connectivity**:
   - Check security groups/firewall rules
   - Ensure database is accessible from application
   - Verify VPC/subnet configuration (AWS)

3. **Check credentials**:
   - Verify username and password
   - Check database exists
   - Verify user has proper permissions

#### Redis Connection Errors

1. **Check connection string format**:
   ```
   redis://host:port/db_number
   ```

2. **Verify Redis is running**:
   - Check service status
   - Verify port is correct (default: 6379)

3. **Check network access**:
   - Verify security groups allow access
   - Check firewall rules

#### Application Won't Start

1. **Check logs**:
   ```bash
   # Fly.io
   flyctl logs
   
   # Render.com
   # View in dashboard
   
   # AWS ECS
   aws logs tail /ecs/ai-automation-platform --follow
   ```

2. **Verify environment variables**:
   - Ensure all required variables are set
   - Check for typos in variable names
   - Verify values are correct

3. **Check health endpoint**:
   ```bash
   curl https://your-app.com/health
   ```

### Getting Help

- **Fly.io**: [Community Forum](https://community.fly.io)
- **Render.com**: [Documentation](https://render.com/docs) | [Community](https://community.render.com)
- **AWS ECS**: [AWS Documentation](https://docs.aws.amazon.com/ecs/) | [AWS Support](https://aws.amazon.com/support/)

## Next Steps

After deployment:

1. **Configure Custom Domain**: Set up your domain with SSL
2. **Set Up Monitoring**: Configure alerts and dashboards
3. **Enable Backups**: Ensure database backups are configured
4. **Set Up CI/CD**: Automate deployments
5. **Configure Scaling**: Set up auto-scaling if needed
6. **Security Hardening**: Review security best practices
7. **Performance Tuning**: Optimize based on usage patterns

## Additional Resources

- [Main README](../README.md) - Application documentation
- [Architecture Guide](../packages/gateway/ARCHITECTURE.md) - System architecture
- [Development Guide](../README.md#development) - Local development setup

---

**Need help?** Open an issue or check the platform-specific guides in each directory.
