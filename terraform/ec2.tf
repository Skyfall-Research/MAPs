# EC2 Instance Configuration
#
# MIGRATION NOTE: This single EC2 instance is being replaced by an Auto Scaling Group (see asg.tf).
# During migration, this instance will run alongside the ASG instances.
# After successful ASG deployment and monitoring period, this instance will be terminated
# and these resources will be removed from Terraform state.
#
# Timeline:
# 1. ASG deployed (both EC2 and ASG instances serve traffic)
# 2. EC2 removed from ALB target groups (ASG serves all traffic)
# 3. Monitor for 48 hours
# 4. Stop EC2 instance (keep as backup)
# 5. After another 48h, terminate EC2 and remove from Terraform

# ==============================================================================
# Data Sources
# ==============================================================================

# Get latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

# ==============================================================================
# User Data Script for EC2 Initialization
# ==============================================================================

locals {
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Log all output to a file
    exec > >(tee /var/log/user-data.log)
    exec 2>&1

    echo "======================================"
    echo "Theme Park EC2 Setup Starting"
    echo "Time: $(date)"
    echo "======================================"

    # Update system
    echo "[1/10] Updating system packages..."
    yum update -y

    # Install Docker
    echo "[2/10] Installing Docker..."
    yum install -y docker
    systemctl start docker
    systemctl enable docker
    usermod -a -G docker ec2-user

    # Install Docker Compose
    echo "[3/10] Installing Docker Compose..."
    DOCKER_COMPOSE_VERSION="v2.23.0"
    curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

    # Install CloudWatch agent
    echo "[4/10] Installing CloudWatch agent..."
    wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
    rpm -U ./amazon-cloudwatch-agent.rpm
    rm -f ./amazon-cloudwatch-agent.rpm

    # Install X-Ray daemon
    echo "[5/10] Installing X-Ray daemon..."
    wget -q https://s3.${var.aws_region}.amazonaws.com/aws-xray-assets.${var.aws_region}/xray-daemon/aws-xray-daemon-3.x.rpm
    yum install -y aws-xray-daemon-3.x.rpm
    rm -f aws-xray-daemon-3.x.rpm

    # Install AWS CLI v2
    echo "[6/10] Installing AWS CLI v2..."
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    yum install -y unzip
    unzip -q awscliv2.zip
    ./aws/install
    rm -rf aws awscliv2.zip

    # Install git
    echo "[7/10] Installing git..."
    yum install -y git

    # Create app directory
    echo "[8/10] Creating application directory..."
    mkdir -p /home/ec2-user/theme-park/scripts
    chown -R ec2-user:ec2-user /home/ec2-user/theme-park

    # Configure CloudWatch agent
    echo "[9/10] Configuring CloudWatch agent..."
    cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CWCONFIG'
    {
      "logs": {
        "logs_collected": {
          "files": {
            "collect_list": [
              {
                "file_path": "/var/log/user-data.log",
                "log_group_name": "/aws/ec2/${var.project_name}",
                "log_stream_name": "{instance_id}/user-data"
              }
            ]
          }
        }
      },
      "metrics": {
        "namespace": "ThemePark",
        "metrics_collected": {
          "mem": {
            "measurement": [
              {
                "name": "mem_used_percent",
                "rename": "MemoryUsedPercent"
              }
            ],
            "metrics_collection_interval": 60
          },
          "disk": {
            "measurement": [
              {
                "name": "used_percent",
                "rename": "DiskUsedPercent"
              }
            ],
            "metrics_collection_interval": 60,
            "resources": ["*"]
          }
        }
      }
    }
    CWCONFIG

    # Start CloudWatch agent
    /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
        -a fetch-config \
        -m ec2 \
        -s \
        -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json

    # Start and enable X-Ray daemon
    echo "[10/10] Starting X-Ray daemon..."
    systemctl start xray
    systemctl enable xray

    # Configure Docker to use awslogs driver
    cat > /etc/docker/daemon.json <<'DOCKERCONFIG'
    {
      "log-driver": "json-file",
      "log-opts": {
        "max-size": "10m",
        "max-file": "3"
      }
    }
    DOCKERCONFIG

    systemctl restart docker

    echo "======================================"
    echo "Theme Park EC2 Setup Complete!"
    echo "Time: $(date)"
    echo "======================================"
    echo "Setup complete" > /var/log/user-data-complete.log
  EOF
}

# ==============================================================================
# EC2 Key Pair
# ==============================================================================

# Create a new SSH key pair
resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "ec2_key" {
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.ec2_key.public_key_openssh

  tags = {
    Name = "${var.project_name}-key"
  }
}

# Save private key locally
resource "local_file" "private_key" {
  content         = tls_private_key.ec2_key.private_key_pem
  filename        = "${path.module}/${var.project_name}-key.pem"
  file_permission = "0400"
}

# ==============================================================================
# EC2 Instance
# ==============================================================================

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public_1.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # Use the generated key pair
  key_name = aws_key_pair.ec2_key.key_name

  # Root volume configuration
  root_block_device {
    volume_size           = var.ec2_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project_name}-root-volume"
    }
  }

  # User data for initial setup
  user_data = local.user_data

  # Enable detailed monitoring
  monitoring = var.enable_detailed_monitoring

  # Enable termination protection in production
  disable_api_termination = false  # Set to true for production

  # Metadata options for IMDSv2
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # Require IMDSv2
    http_put_response_hop_limit = 2  # Allow Docker containers to access metadata
    instance_metadata_tags      = "enabled"
  }

  tags = {
    Name = "${var.project_name}-app"
  }

  lifecycle {
    ignore_changes = [
      # Ignore changes to user_data after initial creation
      user_data,
      # Ignore AMI changes to prevent accidental instance replacement
      ami
    ]
  }
}

# ==============================================================================
# Elastic IP for Stable Public IP Address
# ==============================================================================

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }

  depends_on = [aws_internet_gateway.main]
}