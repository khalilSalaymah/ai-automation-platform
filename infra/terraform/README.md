# Terraform Module for Managed Postgres + Redis

This Terraform module provisions a complete AWS infrastructure for the AI Automation Platform, including:

- VPC with public and private subnets
- RDS PostgreSQL instance (with pgvector support)
- ElastiCache Redis cluster
- Security groups
- NAT Gateway for private subnet internet access
- All necessary networking components

## Prerequisites

1. AWS CLI installed and configured
2. Terraform >= 1.0 installed
3. AWS account with appropriate permissions
4. Valid AWS credentials configured

## Quick Start

### 1. Configure Variables

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and update:
- `database_password` - Strong password for PostgreSQL
- `project_name` - Your project name
- Other variables as needed

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

This will show you what resources will be created.

### 4. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted. This will create:
- VPC and networking infrastructure
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- Security groups and routing

### 5. Get Connection Strings

After deployment, get the connection strings:

```bash
# Database URL
terraform output database_url

# Redis URL
terraform output redis_url

# VPC and subnet IDs (for ECS deployment)
terraform output vpc_id
terraform output public_subnet_ids
terraform output private_subnet_ids
terraform output app_security_group_id
```

## Configuration Options

### RDS PostgreSQL

Key variables:
- `rds_instance_class` - Instance size (default: `db.t3.micro`)
- `rds_allocated_storage` - Initial storage in GB (default: 20)
- `rds_max_allocated_storage` - Max storage for autoscaling (default: 100)
- `rds_engine_version` - PostgreSQL version (default: `15.4`)
- `database_name` - Database name (default: `ai_agents`)
- `database_username` - Master username (default: `postgres`)
- `database_password` - Master password (required)

### ElastiCache Redis

Key variables:
- `redis_node_type` - Node size (default: `cache.t3.micro`)
- `redis_num_cache_nodes` - Number of nodes (default: 1)
- `redis_automatic_failover_enabled` - Enable failover (default: false)
- `redis_multi_az_enabled` - Enable Multi-AZ (default: false)
- `redis_engine_version` - Redis version (default: `7.0`)

### Network

- `vpc_cidr` - VPC CIDR block (default: `10.0.0.0/16`)
- `region` - AWS region (default: `us-east-1`)

## Outputs

The module provides these outputs:

| Output | Description |
|--------|-------------|
| `vpc_id` | VPC ID |
| `public_subnet_ids` | List of public subnet IDs |
| `private_subnet_ids` | List of private subnet IDs |
| `app_security_group_id` | Application security group ID |
| `database_endpoint` | RDS endpoint |
| `database_url` | PostgreSQL connection URL (sensitive) |
| `redis_endpoint` | Redis primary endpoint |
| `redis_url` | Redis connection URL (sensitive) |

## Using with ECS

After deploying this infrastructure, use the outputs in your ECS configuration:

```bash
# Get values
VPC_ID=$(terraform output -raw vpc_id)
SUBNET_IDS=$(terraform output -json public_subnet_ids | jq -r '.[]' | tr '\n' ' ')
SG_ID=$(terraform output -raw app_security_group_id)

# Update ECS service definition
# Use these values in service-definition.json
```

## Enabling pgvector Extension

After RDS is created, connect and enable pgvector:

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# Connect to database
psql -h $DB_ENDPOINT -U postgres -d ai_agents

# Enable extension
CREATE EXTENSION IF NOT EXISTS vector;
```

## Cost Optimization

### Development/Testing

Use these settings in `terraform.tfvars`:

```hcl
rds_instance_class = "db.t3.micro"
redis_node_type    = "cache.t3.micro"
redis_num_cache_nodes = 1
```

### Production

```hcl
rds_instance_class = "db.t3.medium"  # or larger
rds_allocated_storage = 100
rds_max_allocated_storage = 1000
redis_node_type = "cache.t3.medium"  # or larger
redis_num_cache_nodes = 2
redis_automatic_failover_enabled = true
redis_multi_az_enabled = true
```

## Security Best Practices

1. **Use strong passwords**: Set a strong `database_password`
2. **Enable encryption**: 
   - RDS encryption is enabled by default
   - Enable `redis_at_rest_encryption_enabled = true`
   - Enable `redis_transit_encryption_enabled = true` for production
3. **Backup retention**: Set appropriate `rds_backup_retention_period`
4. **Network isolation**: Resources are in private subnets
5. **Security groups**: Only allow access from application security group

## Monitoring

### RDS

- CloudWatch metrics are automatically enabled
- Performance Insights can be enabled with `rds_performance_insights_enabled = true`
- Logs are exported to CloudWatch

### ElastiCache

- CloudWatch metrics are automatically enabled
- Monitor cache hit/miss ratios
- Set up CloudWatch alarms for important metrics

## Backup and Recovery

### RDS Backups

- Automated backups are enabled (retention period configurable)
- Manual snapshots can be created via AWS Console or CLI
- Point-in-time recovery is available

### ElastiCache Snapshots

- Enable snapshots with `redis_snapshot_retention_limit > 0`
- Manual snapshots can be created via AWS Console or CLI

## Upgrading

### RDS

```bash
# Modify instance
terraform apply -var="rds_instance_class=db.t3.medium"
```

### ElastiCache

```bash
# Modify cluster
terraform apply -var="redis_node_type=cache.t3.medium"
```

## Troubleshooting

### Cannot Connect to Database

1. Check security group rules
2. Verify database is in private subnet
3. Check route tables
4. Verify database endpoint is correct

### High Costs

1. Review instance sizes
2. Check storage usage
3. Review backup retention
4. Consider reserved instances for production

### Performance Issues

1. Enable Performance Insights for RDS
2. Monitor CloudWatch metrics
3. Consider upgrading instance sizes
4. Review query performance

## Destroying Resources

⚠️ **Warning**: This will delete all resources including databases!

```bash
terraform destroy
```

To keep a final snapshot of RDS, set `rds_skip_final_snapshot = false` (default).

## Additional Resources

- [AWS RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS ElastiCache Documentation](https://docs.aws.amazon.com/elasticache/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
