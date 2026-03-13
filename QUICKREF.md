# 📖 Quick Reference Guide

Essential commands and workflows for daily operations.

## 🚀 Getting Started

```bash
# First time setup
./setup.sh

# Start services
docker compose up -d

# Stop services
docker compose down

# Restart all
docker compose restart
```

## 🔍 Monitoring & Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f db
docker compose logs -f worker

# Check service status
docker compose ps

# View resource usage
docker stats
```

## 🗄️ Database Operations

```bash
# Connect to database
docker compose exec db psql -U logistics

# Backup database
docker compose exec db pg_dump -U logistics logistics > backup.sql

# Restore database
docker compose exec -T db psql -U logistics logistics < backup.sql

# View database size
docker compose exec db psql -U logistics -c "\l+"

# Run migrations (when added)
docker compose exec backend alembic upgrade head
```

## 🧪 Testing API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Geocode address
curl -X POST http://localhost:8000/api/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "1600 Amphitheatre Parkway, Mountain View, CA"}'

# Create route
curl -X POST http://localhost:8000/api/routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Route",
    "stops": [
      {"address": "Location A", "latitude": 37.7749, "longitude": -122.4194},
      {"address": "Location B", "latitude": 37.8044, "longitude": -122.2712}
    ]
  }'

# Optimize route
curl -X POST http://localhost:8000/api/routes/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"latitude": 37.7749, "longitude": -122.4194},
      {"latitude": 37.8044, "longitude": -122.2712},
      {"latitude": 37.7849, "longitude": -122.4094}
    ]
  }'

# Get all routes
curl http://localhost:8000/api/routes
```

## 🔧 Maintenance

```bash
# Update code and rebuild
git pull
docker compose build
docker compose up -d

# Clean up unused Docker resources
docker system prune -a

# View Docker disk usage
docker system df

# Remove all volumes (CAUTION: deletes data!)
docker compose down -v
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check logs for errors
docker compose logs

# Remove containers and restart
docker compose down
docker compose up -d

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Database connection errors
```bash
# Check if database is running
docker compose ps db

# Restart database
docker compose restart db

# Check database logs
docker compose logs db

# Test connection manually
docker compose exec db psql -U logistics -c "SELECT 1"
```

### OSRM routing not working
```bash
# Check OSRM logs
docker compose logs osrm

# Test OSRM directly
curl "http://localhost:5000/route/v1/driving/-122.4194,37.7749;-122.2712,37.8044"

# Download and process new map data
# See DEPLOYMENT.md for detailed instructions
```

### High memory usage
```bash
# Check resource usage
docker stats

# Restart services
docker compose restart

# Adjust Docker memory limits in docker-compose.yml
```

## 📊 Performance Optimization

```bash
# Optimize database
docker compose exec db psql -U logistics -c "VACUUM ANALYZE"

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL

# Restart workers to clear memory
docker compose restart worker
```

## 🔐 Security

```bash
# Change database password
# 1. Update .env file
# 2. Update docker-compose.yml
# 3. Restart services
docker compose down
docker compose up -d

# Generate new secret key
openssl rand -hex 32

# View environment variables
docker compose config
```

## 📈 Scaling

```bash
# Scale workers horizontally
docker compose up -d --scale worker=3

# View scaled services
docker compose ps

# Scale back down
docker compose up -d --scale worker=1
```

## 🔄 CI/CD

```bash
# Manual deployment
git pull
docker compose pull
docker compose up -d

# Check deployment status
docker compose ps
docker compose logs -f backend
```

## 💾 Backup Strategy

```bash
# Daily backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker compose exec -T db pg_dump -U logistics logistics > "backup_${DATE}.sql"
echo "Backup created: backup_${DATE}.sql"
EOF

chmod +x backup.sh

# Add to crontab for daily backups
echo "0 2 * * * cd /path/to/logistics-platform && ./backup.sh" | crontab -
```

## 🌍 Environment-Specific Commands

### Development
```bash
# Hot reload enabled by default
# Edit code and see changes instantly
docker compose logs -f backend
```

### Production
```bash
# Set production environment
export ENVIRONMENT=production

# Use production compose file
docker compose -f docker-compose.prod.yml up -d

# Enable SSL
# See DEPLOYMENT.md for Certbot setup
```

## 📱 Mobile App (Coming Soon)

```bash
# Start React Native dev server
cd mobile
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## 🤝 Common Workflows

### Adding a new feature
```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# Edit files...

# 3. Test locally
docker compose restart backend
docker compose logs -f backend

# 4. Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
```

### Updating dependencies
```bash
# Update Python packages
# Edit backend/requirements.txt

# Rebuild
docker compose build backend
docker compose up -d backend
```

## 📞 Getting Help

- API Documentation: http://localhost:8000/docs
- Interactive API: http://localhost:8000/redoc
- GitHub Issues: Report bugs
- Discussions: Ask questions

---

**💡 Pro Tip**: Bookmark this file for quick reference!
