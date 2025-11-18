#!/bin/bash
# User Data Script for Theme Park ASG Instances
# This script runs on first boot to set up the instance

set -e  # Exit on any error

# Log all output
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "======================================"
echo "Theme Park ASG Instance Setup Starting"
echo "Time: $(date)"
echo "Instance ID: $(ec2-metadata --instance-id | cut -d ' ' -f 2)"
echo "======================================"

# ==============================================================================
# System Updates and Dependencies
# ==============================================================================

echo "[1/10] Updating system packages..."
yum update -y

echo "[2/10] Installing Docker..."
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# ==============================================================================
# Install AWS CLI v2
# ==============================================================================

echo "[3/10] Installing AWS CLI v2..."
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
yum install -y unzip
unzip -q awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# ==============================================================================
# Install CloudWatch Agent
# ==============================================================================

echo "[4/10] Installing CloudWatch agent..."
curl -sL -o amazon-cloudwatch-agent.rpm https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm
rm -f ./amazon-cloudwatch-agent.rpm

# ==============================================================================
# Configure CloudWatch Agent
# ==============================================================================

echo "[5/10] Configuring CloudWatch agent..."
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<'CWCONFIG'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/ec2/theme-park",
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

# ==============================================================================
# Get AWS Account and Region Information
# ==============================================================================

echo "[6/10] Getting AWS configuration..."
AWS_REGION=$(ec2-metadata --availability-zone | cut -d ' ' -f 2 | sed 's/[a-z]$//')
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ALB_DNS="theme-park-alb-591885444.us-east-2.elb.amazonaws.com"
DOMAIN="maps.skyfall.ai"

echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"

# ==============================================================================
# ECR Login and Pull Images
# ==============================================================================

echo "[7/10] Logging into Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "[8/10] Pulling Docker images..."
echo "Pulling backend image..."
docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/theme-park-backend:latest

echo "Pulling website image..."
docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/theme-park-website:latest

# ==============================================================================
# Start Application Containers
# ==============================================================================

echo "[9/10] Starting application containers..."

# Create Docker network for container communication
echo "Creating Docker network..."
docker network create theme-park-network

# Start backend container
echo "Starting backend container..."
docker run -d \
    --name theme-park-backend \
    --network theme-park-network \
    --network-alias backend \
    --restart unless-stopped \
    -p 3000:3000 \
    -e NODE_ENV=production \
    -e THEME_PARK_PORT=3000 \
    -e CORS_ORIGIN=https://${ALB_DNS},https://${DOMAIN} \
    -e AWS_REGION=${AWS_REGION} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/theme-park-backend:latest

# Wait a few seconds for backend to start
sleep 5

# Start website container
echo "Starting website container..."
docker run -d \
    --name theme-park-website \
    --network theme-park-network \
    --restart unless-stopped \
    -p 3001:3001 \
    -e NODE_ENV=production \
    -e PORT=3001 \
    -e ORIGIN=https://${DOMAIN} \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/theme-park-website:latest

# ==============================================================================
# Verify Containers Are Running
# ==============================================================================

echo "[10/10] Verifying containers..."
sleep 5

BACKEND_STATUS=$(docker inspect theme-park-backend --format='{{.State.Status}}')
WEBSITE_STATUS=$(docker inspect theme-park-website --format='{{.State.Status}}')

echo "Backend container status: $BACKEND_STATUS"
echo "Website container status: $WEBSITE_STATUS"

if [ "$BACKEND_STATUS" != "running" ]; then
    echo "ERROR: Backend container failed to start!"
    docker logs theme-park-backend
    exit 1
fi

if [ "$WEBSITE_STATUS" != "running" ]; then
    echo "ERROR: Website container failed to start!"
    docker logs theme-park-website
    exit 1
fi

# ==============================================================================
# Health Check
# ==============================================================================

echo "Waiting for applications to be ready..."
sleep 10

# Check backend health
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health || echo "000")
echo "Backend health check status: $BACKEND_HEALTH"

if [ "$BACKEND_HEALTH" != "200" ] && [ "$BACKEND_HEALTH" != "404" ]; then
    echo "WARNING: Backend health check returned $BACKEND_HEALTH"
fi

# Check website
WEBSITE_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/ || echo "000")
echo "Website health check status: $WEBSITE_HEALTH"

if [ "$WEBSITE_HEALTH" != "200" ]; then
    echo "WARNING: Website health check returned $WEBSITE_HEALTH"
fi

# ==============================================================================
# Cleanup and Final Steps
# ==============================================================================

echo "Configuring Docker logging..."
cat > /etc/docker/daemon.json <<'DOCKERCONFIG'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
DOCKERCONFIG

# Don't restart Docker as it would kill our containers
# This config will apply to future containers

echo "======================================"
echo "Theme Park ASG Instance Setup Complete!"
echo "Time: $(date)"
echo "======================================"
echo ""
echo "Container Status:"
docker ps

echo ""
echo "Setup complete" > /var/log/user-data-complete.log
