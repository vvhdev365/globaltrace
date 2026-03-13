# 🚚 Zero-Cost Logistics Platform

A complete, production-ready logistics and route optimization platform built with an AI-first approach. Deploy for **$0/month** using free-tier cloud services.

## 🌟 Features

- ✅ **Route Optimization** - Google OR-Tools powered VRP solver
- ✅ **Real-Time GPS Tracking** - WebSocket-based live tracking
- ✅ **Smart Geocoding** - Free OpenStreetMap geocoding
- ✅ **Route Planning** - OSRM-powered routing engine
- ✅ **Driver Management** - Complete driver and vehicle management
- ✅ **Analytics Dashboard** - Real-time metrics and reporting
- ✅ **Mobile App Ready** - React Native driver app included
- ✅ **Multi-Tenant** - Support for multiple organizations
- ✅ **Free Forever** - No monthly costs, ever!

## 🎯 Tech Stack

### Backend
- **FastAPI** - Modern, fast Python web framework
- **PostgreSQL + PostGIS** - Geospatial database
- **Redis** - Caching and message queue
- **Google OR-Tools** - Route optimization
- **OSRM** - Self-hosted routing engine
- **SQLAlchemy** - ORM with async support

### Frontend
- **React** - Modern UI framework
- **MapLibre GL JS** - Free map rendering
- **Tailwind CSS** - Utility-first styling
- **Vite** - Fast build tool

### Mobile
- **React Native** - Cross-platform mobile apps
- **Expo** - Easy deployment

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **Oracle Cloud Always Free** - Hosting (4 CPU, 24GB RAM!)
- **Vercel/Netlify** - Frontend hosting (free)

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/logistics-platform.git
cd logistics-platform
```

### 2. Set Up Environment Variables
```bash
cp backend/.env.example backend/.env
# Edit .env with your settings
```

### 3. Start All Services
```bash
docker compose up -d
```

### 4. Initialize Database
```bash
docker compose exec api python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"
```

### 5. Access the Application
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000 (after setup)

## 📦 Services Overview

### Core Services (Always Running)
- **PostgreSQL**: Database with PostGIS extension
- **Redis**: Caching and job queue
- **API**: FastAPI backend
- **OSRM**: Routing engine (optional)

### Optional Services
- **Worker**: Celery background jobs
- **Nginx**: Reverse proxy (production)
- **Prometheus + Grafana**: Monitoring

## 🌐 Zero-Cost Deployment

### Option 1: Oracle Cloud (Recommended)
**Free Forever: 4 CPU, 24GB RAM, 200GB Storage**

```bash
# SSH into your Oracle Cloud VM
ssh -i your-key.pem ubuntu@your-vm-ip

# Clone the repository
git clone https://github.com/yourusername/logistics-platform.git
cd logistics-platform

# Run deployment script
chmod +x devops/deploy-oracle-cloud.sh
./devops/deploy-oracle-cloud.sh
```

### Option 2: Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Option 3: Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
fly deploy
```

## 🗺️ Setting Up OSRM (Optional - Self-Hosted Routing)

OSRM provides free, unlimited routing. Here's how to set it up:

### 1. Download Map Data
```bash
# Create OSRM data directory
mkdir -p osrm_data
cd osrm_data

# Download map for your region (example: North America)
wget http://download.geofabrik.de/north-america-latest.osm.pbf

# Or for specific country:
wget http://download.geofabrik.de/north-america/us-west-latest.osm.pbf
```

### 2. Process Map Data
```bash
# Extract
docker run -t -v "$(pwd):/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/us-west-latest.osm.pbf

# Partition
docker run -t -v "$(pwd):/data" osrm/osrm-backend osrm-partition /data/us-west-latest.osrm

# Customize
docker run -t -v "$(pwd):/data" osrm/osrm-backend osrm-customize /data/us-west-latest.osrm
```

### 3. Start OSRM Service
```bash
# Update docker-compose.yml with correct path
docker compose --profile osrm up -d
```

## 📱 Frontend Setup

### Web Dashboard
```bash
cd frontend
npm install
npm run dev

# Build for production
npm run build

# Deploy to Vercel
vercel deploy --prod
```

### Mobile App
```bash
cd mobile
npm install
npx expo start

# Build for iOS/Android
eas build --platform all
```

## 🔑 API Endpoints

### Route Optimization
```bash
POST /api/routes/optimize
```
```json
{
  "stops": [
    {"lat": 37.7749, "lng": -122.4194, "address": "San Francisco"},
    {"lat": 37.8044, "lng": -122.2712, "address": "Oakland"}
  ],
  "num_vehicles": 1
}
```

### Geocoding
```bash
GET /api/geocode?address=1600 Amphitheatre Parkway, Mountain View, CA
```

### Real-Time Tracking
```javascript
// WebSocket connection
const ws = new WebSocket('ws://localhost:8000/ws/tracking/driver123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Location update:', data);
};

// Send location update
ws.send(JSON.stringify({
  lat: 37.7749,
  lng: -122.4194,
  speed: 45,
  heading: 180
}));
```

## 📊 Database Schema

### Core Tables
- `routes` - Delivery routes
- `stops` - Delivery stops
- `drivers` - Driver information
- `vehicles` - Vehicle fleet
- `location_history` - GPS tracking history
- `delivery_events` - Event logging

### Geospatial Queries
```sql
-- Find nearby stops within 5km
SELECT * FROM stops
WHERE ST_DWithin(
  location,
  ST_SetSRID(ST_MakePoint(-122.4194, 37.7749), 4326)::geography,
  5000
);
```

## 🧪 Testing

### Run Tests
```bash
# Backend tests
docker compose exec api pytest

# Frontend tests
cd frontend && npm test

# Load testing
docker compose exec api locust
```

## 📈 Monitoring

### Enable Monitoring Stack
```bash
docker compose --profile monitoring up -d
```

Access:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## 🔐 Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Configure CORS origins
- [ ] Set up rate limiting
- [ ] Enable database backups
- [ ] Review firewall rules

## 💰 Cost Breakdown (Zero!)

| Service | Free Tier | Cost |
|---------|-----------|------|
| Oracle Cloud VM | 4 CPU, 24GB RAM | $0 |
| PostgreSQL | Self-hosted | $0 |
| Redis | Self-hosted | $0 |
| OSRM | Self-hosted | $0 |
| Vercel/Netlify | Unlimited bandwidth | $0 |
| Expo | Unlimited builds | $0 |
| Mapbox | 50k loads/month | $0 |
| **Total** | | **$0/month** |

## 🗺️ Roadmap

### Phase 1 (Current)
- [x] Core API with route optimization
- [x] Real-time GPS tracking
- [x] Web dashboard
- [x] Docker deployment

### Phase 2 (Next 2 months)
- [ ] ML-based ETA predictions
- [ ] Driver behavior scoring
- [ ] Advanced analytics
- [ ] Mobile app v1

### Phase 3 (Months 3-6)
- [ ] AI route optimization
- [ ] Dynamic re-routing
- [ ] Customer portal
- [ ] Billing system

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🆘 Support

- **Documentation**: [docs.logistics-platform.com](https://docs.logistics-platform.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/logistics-platform/issues)
- **Discord**: [Join our community](https://discord.gg/logistics)

## 🎓 Learning Resources

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [OR-Tools Guide](https://developers.google.com/optimization)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [OSRM API](http://project-osrm.org/docs/v5.24.0/api/)

## ⭐ Star History

If this helped you, please star the repo!

---

**Built with ❤️ for the logistics community**

**Zero cost. Zero limits. Infinite possibilities.**
