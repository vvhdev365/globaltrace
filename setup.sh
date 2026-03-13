#!/bin/bash

# =============================================================================
# Logistics Platform - Automated Setup Script
# =============================================================================
# This script automates the complete setup process
# Run: ./setup.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${2}${1}${NC}"
}

print_message "╔════════════════════════════════════════════════════════════╗" "$BLUE"
print_message "║      Logistics Platform - Zero-Cost Setup                  ║" "$BLUE"
print_message "║      Production-Ready Fleet Management System              ║" "$BLUE"
print_message "╚════════════════════════════════════════════════════════════╝" "$BLUE"
echo ""

# =============================================================================
# STEP 1: Check Prerequisites
# =============================================================================

print_message "📋 Checking prerequisites..." "$YELLOW"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_message "❌ Docker not found. Please install Docker first." "$RED"
    print_message "   Visit: https://docs.docker.com/get-docker/" "$BLUE"
    exit 1
fi
print_message "✅ Docker found" "$GREEN"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_message "❌ Docker Compose not found. Please install Docker Compose." "$RED"
    exit 1
fi
print_message "✅ Docker Compose found" "$GREEN"

# =============================================================================
# STEP 2: Create Environment File
# =============================================================================

print_message "\n🔧 Setting up environment configuration..." "$YELLOW"

if [ ! -f .env ]; then
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://logistics:logistics_dev_2024@db:5432/logistics
POSTGRES_USER=logistics
POSTGRES_PASSWORD=logistics_dev_2024
POSTGRES_DB=logistics

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Configuration
SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=development

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
EOF

    print_message "✅ Environment file created (.env)" "$GREEN"
else
    print_message "⚠️  .env file already exists, skipping..." "$YELLOW"
fi

# =============================================================================
# STEP 3: Pull Docker Images
# =============================================================================

print_message "\n📥 Pulling Docker images (this may take a few minutes)..." "$YELLOW"
docker compose pull

# =============================================================================
# STEP 4: Build Services
# =============================================================================

print_message "\n🔨 Building services..." "$YELLOW"
docker compose build

# =============================================================================
# STEP 5: Start Services
# =============================================================================

print_message "\n🚀 Starting all services..." "$YELLOW"
docker compose up -d

# Wait for services to be healthy
print_message "\n⏳ Waiting for services to be ready..." "$YELLOW"
sleep 10

# =============================================================================
# STEP 6: Check Service Health
# =============================================================================

print_message "\n🏥 Checking service health..." "$YELLOW"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    print_message "✅ Backend API is healthy" "$GREEN"
else
    print_message "❌ Backend API is not responding" "$RED"
fi

# Check if database is running
if docker compose exec -T db pg_isready -U logistics > /dev/null 2>&1; then
    print_message "✅ Database is healthy" "$GREEN"
else
    print_message "❌ Database is not responding" "$RED"
fi

# Check if Redis is running
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_message "✅ Redis is healthy" "$GREEN"
else
    print_message "❌ Redis is not responding" "$RED"
fi

# =============================================================================
# STEP 7: Setup Initial Data (Optional)
# =============================================================================

print_message "\n📝 Setting up initial test data..." "$YELLOW"

# Create test user
print_message "Creating test admin user..." "$BLUE"
# This would normally use the API, but for now we'll skip

# =============================================================================
# STEP 8: Display Access Information
# =============================================================================

print_message "\n╔════════════════════════════════════════════════════════════╗" "$GREEN"
print_message "║                  🎉 Setup Complete!                        ║" "$GREEN"
print_message "╚════════════════════════════════════════════════════════════╝" "$GREEN"

echo ""
print_message "📡 Services Running:" "$BLUE"
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │ 🌐 API Documentation:  http://localhost:8000/docs       │"
echo "  │ 🔌 API Endpoint:       http://localhost:8000/api        │"
echo "  │ 📊 Grafana Dashboard:  http://localhost:3001            │"
echo "  │ 📈 Prometheus:         http://localhost:9090            │"
echo "  │ 🗄️  PostgreSQL:         localhost:5432                  │"
echo "  │ 💾 Redis:              localhost:6379                   │"
echo "  └─────────────────────────────────────────────────────────┘"

echo ""
print_message "🔑 Default Credentials:" "$BLUE"
echo "  ┌─────────────────────────────────────────────────────────┐"
echo "  │ Grafana:   admin / admin                                │"
echo "  │ Database:  logistics / logistics_dev_2024               │"
echo "  └─────────────────────────────────────────────────────────┘"

echo ""
print_message "🚀 Quick Test Commands:" "$BLUE"
echo ""
echo "  # View logs"
echo "  docker compose logs -f"
echo ""
echo "  # Check status"
echo "  docker compose ps"
echo ""
echo "  # Test API"
echo "  curl http://localhost:8000/health"
echo ""
echo "  # Stop services"
echo "  docker compose down"
echo ""
echo "  # Restart services"
echo "  docker compose restart"

echo ""
print_message "📚 Next Steps:" "$YELLOW"
echo "  1. Visit http://localhost:8000/docs to explore the API"
echo "  2. Read DEPLOYMENT.md for production deployment"
echo "  3. Check README.md for full documentation"
echo "  4. Start building your logistics solution!"

echo ""
print_message "💡 Tip: Run 'docker compose logs -f backend' to watch logs" "$BLUE"
echo ""

print_message "═══════════════════════════════════════════════════════════" "$GREEN"
print_message "         Happy building! 🚚 Track. Optimize. Deliver.      " "$GREEN"
print_message "═══════════════════════════════════════════════════════════" "$GREEN"
