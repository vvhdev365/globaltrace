#!/bin/bash

# ============================================
# Zero-Cost Deployment Script for Oracle Cloud
# Deploy complete logistics platform to Oracle Cloud Always Free Tier
# ============================================

set -e  # Exit on error

echo "🚀 Starting deployment to Oracle Cloud..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="logistics-platform"
APP_DIR="/home/ubuntu/$APP_NAME"
DOMAIN="${DOMAIN:-your-domain.com}"  # Optional

# ============================================
# 1. System Update and Dependencies
# ============================================

echo -e "${BLUE}📦 Installing system dependencies...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    software-properties-common \
    ca-certificates \
    gnupg \
    lsb-release

# ============================================
# 2. Install Docker
# ============================================

echo -e "${BLUE}🐳 Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✅ Docker installed successfully${NC}"
else
    echo -e "${GREEN}✅ Docker already installed${NC}"
fi

# Install Docker Compose
echo -e "${BLUE}📦 Installing Docker Compose...${NC}"
sudo apt-get install -y docker-compose-plugin

# ============================================
# 3. Clone/Update Repository
# ============================================

echo -e "${BLUE}📥 Setting up application...${NC}"
if [ -d "$APP_DIR" ]; then
    echo "Updating existing repository..."
    cd $APP_DIR
    git pull
else
    echo "Cloning repository..."
    cd /home/ubuntu
    # Replace with your actual repository
    # git clone https://github.com/yourusername/logistics-platform.git
    mkdir -p $APP_NAME
    # For now, we'll assume files are already copied
fi

cd $APP_DIR

# ============================================
# 4. Environment Configuration
# ============================================

echo -e "${BLUE}⚙️  Configuring environment...${NC}"
if [ ! -f ".env" ]; then
    cp backend/.env.example .env
    
    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Update .env file
    sed -i "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
    sed -i "s/your-jwt-secret-key-change-this/$JWT_SECRET/" .env
    sed -i "s/logistics_pass/$DB_PASSWORD/" .env
    
    echo -e "${GREEN}✅ Environment file created${NC}"
else
    echo -e "${GREEN}✅ Environment file already exists${NC}"
fi

# ============================================
# 5. Firewall Configuration
# ============================================

echo -e "${BLUE}🔥 Configuring firewall...${NC}"
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # API (development)
sudo ufw allow 22/tcp    # SSH
sudo ufw --force enable

echo -e "${GREEN}✅ Firewall configured${NC}"

# ============================================
# 6. Start Services
# ============================================

echo -e "${BLUE}🚀 Starting services with Docker Compose...${NC}"
docker compose down
docker compose up -d --build

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check if services are running
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    docker compose logs
    exit 1
fi

# ============================================
# 7. Database Initialization
# ============================================

echo -e "${BLUE}🗄️  Initializing database...${NC}"
docker compose exec -T api python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
print('Database initialized successfully!')
"

# ============================================
# 8. SSL Certificate (Optional - Let's Encrypt)
# ============================================

if [ "$DOMAIN" != "your-domain.com" ]; then
    echo -e "${BLUE}🔒 Setting up SSL certificate...${NC}"
    sudo apt-get install -y certbot
    sudo certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    echo -e "${GREEN}✅ SSL certificate installed${NC}"
fi

# ============================================
# 9. Setup Monitoring (Optional)
# ============================================

echo -e "${BLUE}📊 Setting up monitoring...${NC}"
docker compose --profile monitoring up -d

# ============================================
# 10. Display Status
# ============================================

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📍 Services running at:"
echo -e "   API:        http://$(curl -s ifconfig.me):8000"
echo -e "   API Docs:   http://$(curl -s ifconfig.me):8000/docs"
echo -e "   Health:     http://$(curl -s ifconfig.me):8000/health"
echo ""
echo -e "🔍 Check status:    docker compose ps"
echo -e "📋 View logs:       docker compose logs -f"
echo -e "🔄 Restart:         docker compose restart"
echo -e "⛔ Stop:            docker compose down"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "1. Deploy frontend to Vercel/Netlify"
echo "2. Update CORS_ORIGINS in .env"
echo "3. Create first admin user"
echo "4. Test API endpoints"
echo ""
echo -e "${GREEN}Happy deploying! 🎉${NC}"
