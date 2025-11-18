variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "theme-park"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "maps.skyfall.ai"
}

variable "admin_email" {
  description = "Email address for CloudWatch alerts"
  type        = string
}

variable "admin_ip" {
  description = "Your IP address for SSH access (format: x.x.x.x/32)"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository in format: org/repo"
  type        = string
  default     = "TalkShopClub/theme-park"
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "ec2_volume_size" {
  description = "EC2 root volume size in GB"
  type        = number
  default     = 30
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PROVISIONED"
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (only for PROVISIONED mode)"
  type        = number
  default     = 5
}

variable "s3_bucket_name" {
  description = "S3 bucket name for trajectory storage"
  type        = string
  default     = "skyfall-maps-leaderboard-saved-trajectories"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for leaderboard"
  type        = string
  default     = "maps_leaderboard"
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed EC2 monitoring"
  type        = bool
  default     = true
}

# ==============================================================================
# Auto Scaling Group Variables
# ==============================================================================

variable "asg_instance_type" {
  description = "EC2 instance type for ASG instances"
  type        = string
  default     = "t3.medium"
}

variable "asg_min_size" {
  description = "Minimum number of instances in ASG"
  type        = number
  default     = 1
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in ASG"
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of instances in ASG"
  type        = number
  default     = 4
}

variable "asg_volume_size" {
  description = "EC2 root volume size in GB for ASG instances"
  type        = number
  default     = 30
}
