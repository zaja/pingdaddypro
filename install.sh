# PingDaddyPro Installation Script
# GitHub: https://github.com/zaja/pingdaddypro
# Docker Hub: svejedobro/pingdaddypro
# Version: 1.0.3

#!/bin/bash

# PingDaddyPro Docker Installation Script
# This script installs Docker and runs PingDaddyPro application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PINGDADDY_IMAGE="svejedobro/pingdaddypro:latest"
CONTAINER_NAME="pingdaddypro"
POSTGRES_CONTAINER="pingdaddypro-postgres"
PORT="5000"
DATA_DIR="./pingdaddypro-data"
POSTGRES_PASSWORD="pingdaddypro"

echo -e "${GREEN}PingDaddy Docker Installation Script${NC}"
echo "======================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${YELLOW}Warning: Running as root. This is not recommended for security reasons.${NC}"
   echo -e "${YELLOW}Consider running as a regular user and using sudo when needed.${NC}"
   echo -e "${YELLOW}Continuing anyway...${NC}"
   echo ""
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    
    # Update package index
    if [[ $EUID -eq 0 ]]; then
        apt-get update
    else
        sudo apt-get update
    fi
    
    # Install required packages
    if [[ $EUID -eq 0 ]]; then
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    else
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    fi
    
    # Add Docker's official GPG key
    if [[ $EUID -eq 0 ]]; then
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    else
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    fi
    
    # Set up the stable repository
    if [[ $EUID -eq 0 ]]; then
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    else
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    fi
    
    # Update package index again
    if [[ $EUID -eq 0 ]]; then
        apt-get update
    else
        sudo apt-get update
    fi
    
    # Install Docker Engine
    if [[ $EUID -eq 0 ]]; then
        apt-get install -y docker-ce docker-ce-cli containerd.io
    else
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    fi
    
    # Add user to docker group (only if not root)
    if [[ $EUID -ne 0 ]]; then
        sudo usermod -aG docker $USER
    fi
    
    echo -e "${GREEN}Docker installed successfully!${NC}"
    if [[ $EUID -ne 0 ]]; then
        echo -e "${YELLOW}Please logout and login again to use Docker without sudo${NC}"
        echo -e "${YELLOW}Or run: newgrp docker${NC}"
    else
        echo -e "${YELLOW}Running as root - Docker is ready to use${NC}"
    fi
    
    # Set Docker command based on user
    if [[ $EUID -eq 0 ]]; then
        DOCKER_CMD="docker"
    else
        # Try to use Docker without sudo
        if ! docker ps &> /dev/null; then
            echo -e "${YELLOW}Running with sudo for now...${NC}"
            DOCKER_CMD="sudo docker"
        else
            DOCKER_CMD="docker"
        fi
    fi
else
    echo -e "${GREEN}Docker is already installed${NC}"
    # Set Docker command based on user
    if [[ $EUID -eq 0 ]]; then
        DOCKER_CMD="docker"
    else
        # Check if we can use Docker without sudo
        if ! docker ps &> /dev/null; then
            echo -e "${YELLOW}Using sudo for Docker commands...${NC}"
            DOCKER_CMD="sudo docker"
        else
            DOCKER_CMD="docker"
        fi
    fi
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    if [[ $EUID -eq 0 ]]; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
fi

# Create data directory
mkdir -p $DATA_DIR

# Stop existing containers if running
if $DOCKER_CMD ps -q -f name=$CONTAINER_NAME | grep -q .; then
    echo -e "${YELLOW}Stopping existing PingDaddyPro container...${NC}"
    $DOCKER_CMD stop $CONTAINER_NAME
    $DOCKER_CMD rm $CONTAINER_NAME
fi

if $DOCKER_CMD ps -q -f name=$POSTGRES_CONTAINER | grep -q .; then
    echo -e "${YELLOW}Stopping existing PostgreSQL container...${NC}"
    $DOCKER_CMD stop $POSTGRES_CONTAINER
    $DOCKER_CMD rm $POSTGRES_CONTAINER
fi

# Create Docker network for containers (only if it doesn't exist)
echo -e "${YELLOW}Creating Docker network...${NC}"
$DOCKER_CMD network create pingdaddypro-network 2>/dev/null || echo "Network already exists"

# Pull latest images
echo -e "${YELLOW}Pulling latest PingDaddyPro image...${NC}"
$DOCKER_CMD pull $PINGDADDY_IMAGE

echo -e "${YELLOW}Pulling PostgreSQL image...${NC}"
$DOCKER_CMD pull postgres:15-alpine

# Start PostgreSQL container
echo -e "${YELLOW}Starting PostgreSQL container...${NC}"

# Ensure network exists before starting containers
if ! $DOCKER_CMD network ls -q -f name=pingdaddypro-network | grep -q .; then
    echo -e "${YELLOW}Creating network (retry)...${NC}"
    $DOCKER_CMD network create pingdaddypro-network
fi

$DOCKER_CMD run -d \
    --name $POSTGRES_CONTAINER \
    --network pingdaddypro-network \
    -v pingdaddypro-data:/var/lib/postgresql/data \
    -e POSTGRES_DB=pingdaddypro \
    -e POSTGRES_USER=pingdaddypro \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -p 5432:5432 \
    --restart unless-stopped \
    postgres:15-alpine

# Wait for PostgreSQL to start
echo -e "${YELLOW}Waiting for PostgreSQL to start...${NC}"
sleep 30

# Start PingDaddyPro container
echo -e "${YELLOW}Starting PingDaddyPro container...${NC}"

# Ensure network exists before starting containers
if ! $DOCKER_CMD network ls -q -f name=pingdaddypro-network | grep -q .; then
    echo -e "${YELLOW}Creating network (retry)...${NC}"
    $DOCKER_CMD network create pingdaddypro-network
fi

$DOCKER_CMD run -d \
    --name $CONTAINER_NAME \
    --network pingdaddypro-network \
    -e DATABASE_URL=postgresql://pingdaddypro:$POSTGRES_PASSWORD@$POSTGRES_CONTAINER:5432/pingdaddypro \
    -p $PORT:5000 \
    -v $(pwd)/$DATA_DIR:/app/data \
    --restart unless-stopped \
    $PINGDADDY_IMAGE

# Wait for container to start
echo -e "${YELLOW}Waiting for PingDaddyPro to start...${NC}"
sleep 10

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')

# Check if container is running
if $DOCKER_CMD ps -q -f name=$CONTAINER_NAME | grep -q .; then
    echo -e "${GREEN}PingDaddyPro started successfully!${NC}"
    echo ""
    echo -e "${GREEN}Installation is finished, open http://$SERVER_IP:$PORT${NC}"
    echo -e "${GREEN}Or locally: http://localhost:$PORT${NC}"
    echo -e "${GREEN}Default login: admin / admin123${NC}"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "  View logs: $DOCKER_CMD logs $CONTAINER_NAME -f"
    echo "  View PostgreSQL logs: $DOCKER_CMD logs $POSTGRES_CONTAINER -f"
    echo "  Stop: $DOCKER_CMD stop $CONTAINER_NAME $POSTGRES_CONTAINER"
    echo "  Start: $DOCKER_CMD start $POSTGRES_CONTAINER $CONTAINER_NAME"
    echo "  Restart: $DOCKER_CMD restart $CONTAINER_NAME $POSTGRES_CONTAINER"
    echo "  Remove: $DOCKER_CMD rm $CONTAINER_NAME $POSTGRES_CONTAINER"
    echo "  Remove network: $DOCKER_CMD network rm pingdaddypro-network"
    echo ""
    echo -e "${GREEN}Data is stored in: $(pwd)/$DATA_DIR${NC}"
    echo -e "${GREEN}PostgreSQL is running on port 5432${NC}"
else
    echo -e "${RED}Failed to start PingDaddyPro container${NC}"
    echo -e "${YELLOW}Check logs: $DOCKER_CMD logs $CONTAINER_NAME${NC}"
    echo -e "${YELLOW}Check PostgreSQL logs: $DOCKER_CMD logs $POSTGRES_CONTAINER${NC}"
    exit 1
fi
