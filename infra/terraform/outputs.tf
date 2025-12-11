output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "app_security_group_id" {
  description = "Application security group ID"
  value       = aws_security_group.app.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "elasticache_security_group_id" {
  description = "ElastiCache security group ID"
  value       = aws_security_group.elasticache.id
}

output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "database_address" {
  description = "RDS PostgreSQL address"
  value       = aws_db_instance.postgres.address
}

output "database_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "database_username" {
  description = "Database username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "database_url" {
  description = "PostgreSQL connection URL"
  value       = "postgresql://${aws_db_instance.postgres.username}:${var.database_password}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis primary endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}/0"
  sensitive   = true
}

output "redis_configuration_endpoint" {
  description = "ElastiCache Redis configuration endpoint (for cluster mode)"
  value       = try(aws_elasticache_replication_group.redis.configuration_endpoint_address, null)
}
