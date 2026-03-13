# 🚀 QUICK START - Get Running in 5 Minutes

## Prerequisites
- Docker and Docker Compose installed
- That's it! (seriously)

## Step 1: Start the Backend (2 minutes)

```bash
# Navigate to project directory
cd logistics-platform

# Copy environment file
cp backend/.env.example backend/.env

# Start all services
docker compose up -d

# Wait ~30 seconds for services to start
# Check status
docker compose ps
```

## Step 2: Initialize Database (30 seconds)

```bash
# Run database initialization
docker compose exec -T api python << EOF
import asyncio
from database import init_db
asyncio.run(init_db())
print("✅ Database initialized!")
EOF
```

## Step 3: Test the API (30 seconds)

```bash
# Check API health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs
```

## Step 4: Start Frontend (Optional - 2 minutes)

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

## 🎉 You're Done!

### What's Running:
- ✅ FastAPI Backend: http://localhost:8000
- ✅ API Documentation: http://localhost:8000/docs
- ✅ PostgreSQL + PostGIS: localhost:5432
- ✅ Redis: localhost:6379
- ✅ Frontend (if started): http://localhost:3000

### Try It Out:

1. **Geocode an address:**
```bash
curl "http://localhost:8000/api/geocode?address=1600+Amphitheatre+Parkway"
```

2. **Optimize a route:**
```bash
curl -X POST "http://localhost:8000/api/routes/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "stops": [
      {"lat": 37.7749, "lng": -122.4194, "address": "San Francisco"},
      {"lat": 37.8044, "lng": -122.2712, "address": "Oakland"},
      {"lat": 37.6879, "lng": -122.4702, "address": "Daly City"}
    ],
    "num_vehicles": 1
  }'
```

3. **View real-time docs:**
   Open http://localhost:8000/docs and click "Try it out" on any endpoint!

## 🚨 Troubleshooting

### Services won't start?
```bash
# Check logs
docker compose logs -f

# Restart
docker compose down && docker compose up -d
```

### Port already in use?
```bash
# Edit docker-compose.yml ports
# Change 8000:8000 to 8080:8000 (or any other port)
```

### Database connection error?
```bash
# Wait for database to be ready
docker compose logs db

# Restart API service
docker compose restart api
```

## 📚 Next Steps

1. Read the full [README.md](README.md)
2. Deploy to Oracle Cloud (see devops/deploy-oracle-cloud.sh)
3. Customize for your needs
4. Add your own features!

## 🎯 Common Tasks

### Stop all services:
```bash
docker compose down
```

### View logs:
```bash
docker compose logs -f api
```

### Access database:
```bash
docker compose exec db psql -U logistics_user -d logistics_db
```

### Rebuild after code changes:
```bash
docker compose up -d --build
```

---

**Need help?** Check the full README or open an issue!
