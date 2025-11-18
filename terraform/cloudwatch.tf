# CloudWatch Monitoring and Alarms Configuration

# ==============================================================================
# CloudWatch Log Groups
# ==============================================================================

# Log group for backend application
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/theme-park/backend"
  retention_in_days = 7  # Adjust as needed (7, 14, 30, 60, 90, etc.)

  tags = {
    Name = "${var.project_name}-backend-logs"
  }
}

# Log group for website application
resource "aws_cloudwatch_log_group" "website" {
  name              = "/aws/theme-park/website"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-website-logs"
  }
}

# Log group for X-Ray daemon
resource "aws_cloudwatch_log_group" "xray" {
  name              = "/aws/theme-park/xray"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-xray-logs"
  }
}

# Log group for EC2 instance
resource "aws_cloudwatch_log_group" "ec2" {
  name              = "/aws/ec2/${var.project_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-ec2-logs"
  }
}

# ==============================================================================
# SNS Topic for Alerts
# ==============================================================================

resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name = "${var.project_name}-alerts"
  }
}

# Email subscription for alerts
resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.admin_email
}

# ==============================================================================
# CloudWatch Alarms
# ==============================================================================

# Alarm: EC2 High CPU Usage
resource "aws_cloudwatch_metric_alarm" "ec2_high_cpu" {
  alarm_name          = "${var.project_name}-ec2-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "EC2 CPU usage is above 80%"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  tags = {
    Name = "${var.project_name}-ec2-high-cpu-alarm"
  }
}

# Alarm: EC2 Status Check Failed
resource "aws_cloudwatch_metric_alarm" "ec2_status_check" {
  alarm_name          = "${var.project_name}-ec2-status-check-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "EC2 instance status check failed"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = aws_instance.app.id
  }

  tags = {
    Name = "${var.project_name}-ec2-status-check-alarm"
  }
}

# Alarm: ALB 5XX Errors
resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  alarm_name          = "${var.project_name}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "ALB is returning too many 5XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-5xx-alarm"
  }
}

# Alarm: ALB Unhealthy Targets (Backend)
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_backend" {
  alarm_name          = "${var.project_name}-alb-unhealthy-backend"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "No healthy backend targets behind ALB"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    TargetGroup  = aws_lb_target_group.backend.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-unhealthy-backend-alarm"
  }
}

# Alarm: ALB Unhealthy Targets (Website)
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_website" {
  alarm_name          = "${var.project_name}-alb-unhealthy-website"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Average"
  threshold           = 1
  alarm_description   = "No healthy website targets behind ALB"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    TargetGroup  = aws_lb_target_group.website.arn_suffix
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-unhealthy-website-alarm"
  }
}

# Alarm: DynamoDB Throttled Requests (using existing table)
resource "aws_cloudwatch_metric_alarm" "dynamodb_throttles" {
  alarm_name          = "${var.project_name}-dynamodb-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "DynamoDB is being throttled"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    TableName = var.dynamodb_table_name
  }

  tags = {
    Name = "${var.project_name}-dynamodb-throttles-alarm"
  }
}

# Alarm: ALB High Response Time
resource "aws_cloudwatch_metric_alarm" "alb_high_response_time" {
  alarm_name          = "${var.project_name}-alb-high-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 1  # 1 second
  alarm_description   = "ALB target response time is above 1 second"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
  }

  tags = {
    Name = "${var.project_name}-alb-response-time-alarm"
  }
}