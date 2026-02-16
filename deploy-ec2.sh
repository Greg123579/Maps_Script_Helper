#!/bin/bash
# =============================================================================
# Maps Script Helper - EC2 Deployment Script (Amazon Linux 2023)
# =============================================================================
#
# This script sets up everything needed to run Maps Script Helper on an
# Amazon Linux EC2 instance using Docker.
#
# Usage:
#   1. SSH into your EC2 instance
#   2. Clone or copy the project to /opt/maps-helper/
#   3. Run: sudo bash deploy-ec2.sh
#
# The app will be available at http://<ec2-public-ip>:8080
#
# Prerequisites:
#   - Amazon Linux 2023 (or Amazon Linux 2) EC2 instance
#   - At least 2GB RAM, 20GB disk recommended
#   - Security group allowing inbound TCP port 8080
#   - Internet access (to pull Docker images and install packages)
#
# =============================================================================

set -euo pipefail

# --- Configuration ---
DEPLOY_DIR="/opt/maps-helper"
APP_PORT=8080
DATA_DIR="${DEPLOY_DIR}/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "\n${BLUE}==>${NC} $*"; }

# --- Pre-flight checks ---
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_step "Starting Maps Script Helper deployment on EC2"
echo "  Deploy directory: ${DEPLOY_DIR}"
echo "  Application port: ${APP_PORT}"
echo ""

# --- Step 1: Install Docker ---
log_step "Step 1/6: Installing Docker"

if command -v docker &> /dev/null; then
    log_info "Docker is already installed: $(docker --version)"
else
    log_info "Installing Docker..."
    
    # Detect Amazon Linux version
    if grep -q "Amazon Linux 2023" /etc/os-release 2>/dev/null; then
        # Amazon Linux 2023
        dnf install -y docker
    elif grep -q "Amazon Linux 2" /etc/os-release 2>/dev/null; then
        # Amazon Linux 2
        amazon-linux-extras install docker -y
    else
        # Generic - try dnf first, then yum
        dnf install -y docker 2>/dev/null || yum install -y docker
    fi
    
    log_info "Docker installed: $(docker --version)"
fi

# Start and enable Docker
systemctl start docker
systemctl enable docker
log_info "Docker service started and enabled"

# Add ec2-user to docker group (so they can run docker without sudo)
usermod -aG docker ec2-user 2>/dev/null || true

# --- Step 2: Install Docker Compose ---
log_step "Step 2/6: Installing Docker Compose"

if docker compose version &> /dev/null; then
    log_info "Docker Compose (plugin) is already installed: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    log_info "Docker Compose (standalone) is already installed: $(docker-compose --version)"
else
    log_info "Installing Docker Compose plugin..."
    
    # Install the Docker Compose plugin
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    if [[ -z "$COMPOSE_VERSION" ]]; then
        COMPOSE_VERSION="v2.24.0"
        log_warn "Could not detect latest version, using ${COMPOSE_VERSION}"
    fi
    
    ARCH=$(uname -m)
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}" \
        -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    
    log_info "Docker Compose installed: $(docker compose version)"
fi

# --- Step 3: Install Git (if needed for cloning) ---
log_step "Step 3/6: Ensuring Git is available"

if command -v git &> /dev/null; then
    log_info "Git is already installed: $(git --version)"
else
    log_info "Installing Git..."
    dnf install -y git 2>/dev/null || yum install -y git
    log_info "Git installed: $(git --version)"
fi

# --- Step 4: Set up deployment directory ---
log_step "Step 4/6: Setting up deployment directory"

# Check if project files exist in current directory or DEPLOY_DIR
if [[ -f "${DEPLOY_DIR}/docker-compose.prod.yml" ]]; then
    log_info "Project already exists at ${DEPLOY_DIR}"
elif [[ -f "./docker-compose.prod.yml" ]]; then
    if [[ "$(pwd)" != "${DEPLOY_DIR}" ]]; then
        log_info "Copying project files to ${DEPLOY_DIR}..."
        mkdir -p "${DEPLOY_DIR}"
        cp -r ./* "${DEPLOY_DIR}/"
        cp -r ./.git "${DEPLOY_DIR}/" 2>/dev/null || true
        cp ./.gitignore "${DEPLOY_DIR}/" 2>/dev/null || true
    fi
else
    log_error "Project files not found!"
    log_error "Please clone the repository first, then run this script from the project directory."
    log_error "  Example: git clone <repo-url> ${DEPLOY_DIR} && cd ${DEPLOY_DIR} && sudo bash deploy-ec2.sh"
    exit 1
fi

cd "${DEPLOY_DIR}"

# Create persistent data directories
log_info "Creating data directories..."
mkdir -p "${DATA_DIR}/outputs"
mkdir -p "${DATA_DIR}/library/images"
mkdir -p "${DATA_DIR}/assets/uploads"
mkdir -p "${DATA_DIR}/logs"
mkdir -p "${DATA_DIR}/scripts"
mkdir -p "${DATA_DIR}/db"

# Copy library files into data directory if they exist and data is empty
if [[ -d "${DEPLOY_DIR}/library/images" ]] && [[ ! "$(ls -A ${DATA_DIR}/library/images 2>/dev/null)" ]]; then
    log_info "Copying library images to data directory..."
    cp -r "${DEPLOY_DIR}/library/images/"* "${DATA_DIR}/library/images/" 2>/dev/null || true
fi

if [[ -f "${DEPLOY_DIR}/library/metadata.json" ]] && [[ ! -f "${DATA_DIR}/library/metadata.json" ]]; then
    cp "${DEPLOY_DIR}/library/metadata.json" "${DATA_DIR}/library/" 2>/dev/null || true
fi

if [[ -f "${DEPLOY_DIR}/scripts/metadata.json" ]] && [[ ! -f "${DATA_DIR}/scripts/metadata.json" ]]; then
    cp "${DEPLOY_DIR}/scripts/metadata.json" "${DATA_DIR}/scripts/" 2>/dev/null || true
fi

# Set permissions so Docker containers can write to data dirs
chmod -R 777 "${DATA_DIR}"
log_info "Data directories created at ${DATA_DIR}"

# --- Step 5: Create .env file ---
log_step "Step 5/6: Configuring environment"

ENV_FILE="${DEPLOY_DIR}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
    log_info "Creating .env file (edit later to add API keys)..."
    cat > "${ENV_FILE}" << 'ENVEOF'
# Maps Script Helper - Environment Configuration
# Edit this file to add your API keys, then restart:
#   cd /opt/maps-helper && docker compose -f docker-compose.prod.yml restart

# Google Gemini AI API key (optional - enables AI assistant)
GOOGLE_API_KEY=

# OpenAI API key (optional - enables AI assistant)
OPENAI_API_KEY=

# Host project directory (used for Docker-in-Docker volume mounts)
# This should match the deploy directory + /data
HOST_PROJECT_DIR=/opt/maps-helper/data
ENVEOF
    chmod 600 "${ENV_FILE}"
    log_warn "Created ${ENV_FILE} - edit it to add your API keys"
else
    log_info ".env file already exists at ${ENV_FILE}"
fi

# --- Step 6: Build and start ---
log_step "Step 6/6: Building and starting the application"

# Build the script execution sandbox image first
log_info "Building py-exec sandbox image..."
docker build -t py-exec:latest "${DEPLOY_DIR}/backend/runner_image/"

# Build backend image with classic docker build (avoids buildx version requirement on older EC2)
log_info "Building Maps Script Helper backend image..."
docker build -t maps-helper-backend .

# Start the application (use pre-built image; no compose --build)
log_info "Starting Maps Script Helper..."
docker compose -f docker-compose.prod.yml up -d

# --- Post-deployment ---
echo ""
echo "============================================================"
echo ""
log_info "Deployment complete!"
echo ""

# Get the public IP
PUBLIC_IP=$(curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "")
PRIVATE_IP=$(curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/local-ipv4 2>/dev/null || hostname -I | awk '{print $1}')

echo "  Application URL:"
if [[ -n "$PUBLIC_IP" ]]; then
    echo "    Public:  http://${PUBLIC_IP}:${APP_PORT}"
fi
echo "    Private: http://${PRIVATE_IP}:${APP_PORT}"
echo ""
echo "  Useful commands:"
echo "    View logs:     cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml logs -f"
echo "    Restart:       cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml restart"
echo "    Stop:          cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml down"
echo "    Rebuild:       cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml up -d --build"
echo "    Update:        cd ${DEPLOY_DIR} && git pull && docker compose -f docker-compose.prod.yml up -d --build"
echo ""
echo "  Configuration:"
echo "    Edit API keys: sudo nano ${DEPLOY_DIR}/.env"
echo "    Data stored:   ${DATA_DIR}/"
echo ""

# Security reminder
log_warn "IMPORTANT: Make sure your EC2 security group allows inbound TCP port ${APP_PORT}"
echo "    You can restrict access to specific IP ranges for security."
echo ""
echo "============================================================"
