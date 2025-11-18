# Application Load Balancer Configuration

# ==============================================================================
# Application Load Balancer
# ==============================================================================

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  enable_deletion_protection = false  # Set to true for production
  enable_http2              = true
  enable_cross_zone_load_balancing = true
  idle_timeout              = 300  # 5 minutes to support long-lived WebSocket connections

  # Access logs (optional - requires S3 bucket)
  # access_logs {
  #   bucket  = aws_s3_bucket.alb_logs.id
  #   enabled = true
  # }

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# ==============================================================================
# Target Groups
# ==============================================================================

# Target Group for Backend (port 3000)
resource "aws_lb_target_group" "backend" {
  name     = "${var.project_name}-backend-tg"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  # Health check configuration
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/v1/health"
    matcher             = "200"
    protocol            = "HTTP"
  }

  # Deregistration delay for graceful shutdown (increased for ASG instance refresh)
  deregistration_delay = 120

  # Stickiness for WebSocket connections
  stickiness {
    enabled         = true
    type            = "lb_cookie"
    cookie_duration = 86400  # 24 hours
  }

  tags = {
    Name = "${var.project_name}-backend-tg"
  }
}

# Target Group for Website (port 3001)
resource "aws_lb_target_group" "website" {
  name     = "${var.project_name}-website-tg"
  port     = 3001
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  # Health check configuration
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
    protocol            = "HTTP"
  }

  # Deregistration delay for graceful shutdown (increased for ASG instance refresh)
  deregistration_delay = 120

  tags = {
    Name = "${var.project_name}-website-tg"
  }
}

# ==============================================================================
# Target Group Attachments
# ==============================================================================

# EC2 target group attachments removed - ASG instances are registered via asg.tf

# ==============================================================================
# SSL/TLS Certificate
# ==============================================================================

# Request ACM certificate for HTTPS
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-cert"
  }
}

# DNS validation will be handled manually in Cloudflare (not Route53)

# ==============================================================================
# ALB Listeners
# ==============================================================================

# HTTPS Listener (port 443)
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"  # Modern TLS policy
  certificate_arn   = aws_acm_certificate.main.arn

  # Default action: forward to website
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.website.arn
  }
}

# HTTPS Listener rule for backend API paths
resource "aws_lb_listener_rule" "backend_https" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  condition {
    path_pattern {
      values = ["/v1/*", "/socket.io/*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# HTTP Listener (port 80) - Redirect to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  # Default action: redirect to HTTPS
  default_action {
    type = "redirect"

    redirect {
      host        = "#{host}"
      path        = "/#{path}"
      port        = "443"
      protocol    = "HTTPS"
      query       = "#{query}"
      status_code = "HTTP_301"
    }
  }
}