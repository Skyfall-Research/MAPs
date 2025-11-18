# Auto Scaling Group Configuration
# This replaces the single EC2 instance with an auto-scaling group
# Note: Uses data.aws_caller_identity.current from main.tf

# ==============================================================================
# Launch Template
# ==============================================================================

resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-lt-"
  image_id      = data.aws_ami.amazon_linux_2023.id
  instance_type = var.asg_instance_type

  # Use the same key pair as single EC2
  key_name = aws_key_pair.ec2_key.key_name

  # Security groups
  vpc_security_group_ids = [aws_security_group.ec2.id]

  # IAM instance profile for DynamoDB/S3 access
  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  # Root volume configuration
  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = var.asg_volume_size
      volume_type           = "gp3"
      encrypted             = true
      delete_on_termination = true
    }
  }

  # User data for instance initialization
  user_data = filebase64("${path.module}/user_data_asg.sh")

  # Metadata options for IMDSv2 with Docker support
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Require IMDSv2
    http_put_response_hop_limit = 2           # Allow Docker containers to access metadata
    instance_metadata_tags      = "enabled"
  }

  # Enable detailed monitoring
  monitoring {
    enabled = var.enable_detailed_monitoring
  }

  # Tag specifications for instances launched from this template
  tag_specifications {
    resource_type = "instance"

    tags = {
      Name        = "${var.project_name}-asg-instance"
      Environment = "production"
      ManagedBy   = "ASG"
    }
  }

  tag_specifications {
    resource_type = "volume"

    tags = {
      Name        = "${var.project_name}-asg-volume"
      Environment = "production"
    }
  }

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-launch-template"
  }
}

# ==============================================================================
# Auto Scaling Group
# ==============================================================================

resource "aws_autoscaling_group" "app" {
  name = "${var.project_name}-asg"

  # Subnet configuration - deploy across both AZs
  vpc_zone_identifier = [
    aws_subnet.public_1.id,
    aws_subnet.public_2.id
  ]

  # Capacity configuration
  min_size         = var.asg_min_size
  desired_capacity = var.asg_desired_capacity
  max_size         = var.asg_max_size

  # Health check configuration
  health_check_type         = "ELB"  # Use ALB health checks
  health_check_grace_period = 300    # 5 minutes for initialization

  # Launch template configuration
  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"  # Always use latest version
  }

  # Attach to ALB target groups
  target_group_arns = [
    aws_lb_target_group.backend.arn,
    aws_lb_target_group.website.arn
  ]

  # Wait for instances to be healthy before considering ASG created
  wait_for_capacity_timeout = "10m"

  # Instance refresh configuration for zero-downtime deployments
  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 0  # With 1 instance, we need to allow 0 to replace it
      instance_warmup        = 300 # 5 minutes
    }
  }

  # Termination policies
  termination_policies = ["OldestLaunchTemplate", "OldestInstance"]

  # Enable metrics collection
  enabled_metrics = [
    "GroupDesiredCapacity",
    "GroupInServiceInstances",
    "GroupMinSize",
    "GroupMaxSize",
    "GroupTotalInstances"
  ]

  # Tags
  tag {
    key                 = "Name"
    value               = "${var.project_name}-asg-instance"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = "production"
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "ASG"
    propagate_at_launch = true
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [desired_capacity] # Allow auto-scaling to manage this
  }
}

# ==============================================================================
# Auto Scaling Policies
# ==============================================================================

# Simple scaling policy - scale up
resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.project_name}-scale-up"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300 # 5 minutes
  autoscaling_group_name = aws_autoscaling_group.app.name
}

# Simple scaling policy - scale down
resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.project_name}-scale-down"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300 # 5 minutes
  autoscaling_group_name = aws_autoscaling_group.app.name
}

# Target tracking scaling policy (recommended - more sophisticated)
resource "aws_autoscaling_policy" "target_tracking" {
  name                   = "${var.project_name}-target-tracking"
  policy_type            = "TargetTrackingScaling"
  autoscaling_group_name = aws_autoscaling_group.app.name

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 60.0 # Maintain 60% CPU on average
  }
}

# ==============================================================================
# CloudWatch Alarms for Scaling
# ==============================================================================

# High CPU alarm - triggers scale up
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.project_name}-asg-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "Triggers when CPU exceeds 70%"
  alarm_actions       = [aws_autoscaling_policy.scale_up.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }

  tags = {
    Name = "${var.project_name}-cpu-high-alarm"
  }
}

# Low CPU alarm - triggers scale down
resource "aws_cloudwatch_metric_alarm" "cpu_low" {
  alarm_name          = "${var.project_name}-asg-cpu-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 30
  alarm_description   = "Triggers when CPU falls below 30%"
  alarm_actions       = [aws_autoscaling_policy.scale_down.arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app.name
  }

  tags = {
    Name = "${var.project_name}-cpu-low-alarm"
  }
}

# Unhealthy instances alarm
resource "aws_cloudwatch_metric_alarm" "unhealthy_instances" {
  alarm_name          = "${var.project_name}-asg-unhealthy-instances"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UnhealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Alert when any instances are unhealthy"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-unhealthy-instances-alarm"
  }
}
