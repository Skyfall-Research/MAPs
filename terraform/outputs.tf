output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = var.aws_region
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "ec2_public_ip" {
  description = "EC2 public IP (Elastic IP)"
  value       = aws_eip.app.public_ip
}

output "ec2_private_ip" {
  description = "EC2 private IP"
  value       = aws_instance.app.private_ip
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "Application Load Balancer ARN"
  value       = aws_lb.main.arn
}

output "backend_ecr_repository_url" {
  description = "Backend ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "website_ecr_repository_url" {
  description = "Website ECR repository URL"
  value       = aws_ecr_repository.website.repository_url
}

output "dynamodb_table_name" {
  description = "DynamoDB table name (using existing)"
  value       = var.dynamodb_table_name
}

output "s3_bucket_name" {
  description = "S3 bucket name (using existing)"
  value       = var.s3_bucket_name
}

output "github_actions_role_arn" {
  description = "GitHub Actions IAM role ARN"
  value       = aws_iam_role.github_actions.arn
}

# COMMENTED OUT TEMPORARILY - Using HTTP only for now
# output "acm_certificate_arn" {
#   description = "ACM certificate ARN"
#   value       = aws_acm_certificate.main.arn
# }

output "website_url" {
  description = "Website URL (HTTP only for now - HTTPS to be added later)"
  value       = "http://${var.domain_name}"
}

output "ssh_command" {
  description = "SSH command to connect to EC2 instance"
  value       = "ssh -i terraform/${var.project_name}-key.pem ec2-user@${aws_eip.app.public_ip}"
}

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    website_url          = "http://${var.domain_name}"  # TEMPORARY: HTTP only
    ec2_ip               = aws_eip.app.public_ip
    backend_ecr          = aws_ecr_repository.backend.repository_url
    website_ecr          = aws_ecr_repository.website.repository_url
    github_actions_role  = aws_iam_role.github_actions.arn
    cloudwatch_logs      = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#logsV2:log-groups"
  }
}
