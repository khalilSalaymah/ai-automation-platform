variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "ai-automation"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# RDS Variables
variable "rds_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "Maximum allocated storage in GB (for autoscaling)"
  type        = number
  default     = 100
}

variable "database_name" {
  description = "Name of the database"
  type        = string
  default     = "ai_agents"
}

variable "database_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "database_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "rds_backup_retention_period" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "rds_skip_final_snapshot" {
  description = "Skip final snapshot when destroying (use with caution!)"
  type        = bool
  default     = false
}

variable "rds_performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = false
}

# ElastiCache Variables
variable "redis_engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "redis_automatic_failover_enabled" {
  description = "Enable automatic failover"
  type        = bool
  default     = false
}

variable "redis_multi_az_enabled" {
  description = "Enable Multi-AZ"
  type        = bool
  default     = false
}

variable "redis_at_rest_encryption_enabled" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}

variable "redis_transit_encryption_enabled" {
  description = "Enable encryption in transit"
  type        = bool
  default     = false
}

variable "redis_snapshot_retention_limit" {
  description = "Number of days to retain snapshots"
  type        = number
  default     = 0
}

variable "redis_parameter_group_family" {
  description = "Redis parameter group family"
  type        = string
  default     = "redis7"
}

variable "redis_maxmemory_policy" {
  description = "Redis maxmemory policy"
  type        = string
  default     = "allkeys-lru"
}
