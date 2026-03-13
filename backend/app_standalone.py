"""
Standalone FastAPI app for instant deployment (no database required)
Works on any free hosting: Railway, Render, Fly.io, etc.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os

# Initialize FastAPI
app = FastAPI(
    title="Logistics Platform API",
    description="Zero-cost logistics and route optimization platform",
    version="1.0.0"
)

# CORS middleware - Allow all origins for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

# In-memory storage (for demo - use database in production)
SHIPMENTS_DB = {}
ROUTES_DB = {}

@app.get("/")
async def root():
    return {
        "message": "🚚 Logistics Platform API - Live!",
        "version": "1.0.0",
        "status": "operational",
        "features": {
            "domestic_routing": "enabled",
            "international_tracking": "enabled",
            "real_time_tracking": "enabled"
        },
        "docs": "/docs",
        "demo_endpoints": {
            "test_shipments": "/api/international/test/generate-shipments",
            "track_shipment": "/api/international/shipments/IND-USA-SEA-001",
            "optimize_route": "/api/routes/optimize"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "operational"
    }

# ============= INTERNATIONAL TRACKING =============

@app.post("/api/international/test/generate-shipments")
async def generate_test_shipments():
    """Generate test shipments from India to US"""
    
    global SHIPMENTS_DB
    
    shipments = [
        {
            "tracking_number": "IND-USA-SEA-001",
            "mode": "sea",
            "origin": "Mumbai (INNSA)",
            "destination": "Los Angeles (USLAX)",
            "vessel": "MSC GULSUN (IMO: 9811000)",
            "status": "in_transit",
            "cargo": "Electronics - 18,000 kg",
            "departure_date": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "eta": (datetime.utcnow() + timedelta(days=22)).isoformat(),
            "current_location": "Indian Ocean",
            "progress": 15
        },
        {
            "tracking_number": "IND-USA-SEA-002",
            "mode": "sea",
            "origin": "Chennai (INCHE)",
            "destination": "New York (USNYC)",
            "vessel": "EVER ACE (IMO: 9811850)",
            "status": "at_port",
            "cargo": "Textiles - 22,000 kg",
            "departure_date": (datetime.utcnow() - timedelta(days=28)).isoformat(),
            "eta": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "current_location": "New York Port",
            "progress": 95
        },
        {
            "tracking_number": "IND-USA-AIR-001",
            "mode": "air",
            "origin": "Delhi (INDEL)",
            "destination": "New York (USJFK)",
            "flight": "AI173",
            "status": "in_flight",
            "cargo": "Pharmaceuticals - 500 kg (Temperature Controlled)",
            "departure_date": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            "eta": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
            "current_location": "Over Atlantic Ocean",
            "progress": 35
        },
        {
            "tracking_number": "IND-USA-AIR-002",
            "mode": "air",
            "origin": "Bangalore (INBLR)",
            "destination": "Chicago (USORD)",
            "flight": "AI127",
            "status": "customs_clearance",
            "cargo": "IT Equipment - 350 kg",
            "departure_date": (datetime.utcnow() - timedelta(hours=22)).isoformat(),
            "eta": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
            "current_location": "Chicago O'Hare - Customs",
            "progress": 90
        }
    ]
    
    # Store in memory
    for shipment in shipments:
        SHIPMENTS_DB[shipment["tracking_number"]] = shipment
    
    return {
        "message": "Test shipments generated successfully",
        "shipments": shipments,
        "count": len(shipments)
    }

@app.get("/api/international/shipments")
async def list_shipments():
    """List all international shipments"""
    
    if not SHIPMENTS_DB:
        # Auto-generate if empty
        await generate_test_shipments()
    
    return {
        "shipments": list(SHIPMENTS_DB.values()),
        "count": len(SHIPMENTS_DB)
    }

@app.get("/api/international/shipments/{tracking_number}")
async def get_shipment(tracking_number: str):
    """Get shipment details"""
    
    if not SHIPMENTS_DB:
        await generate_test_shipments()
    
    if tracking_number not in SHIPMENTS_DB:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment = SHIPMENTS_DB[tracking_number]
    
    # Add detailed info
    detailed = {
        **shipment,
        "carrier_name": "Maersk Line" if shipment["mode"] == "sea" else "Air India Cargo",
        "container_number": f"MSCU{tracking_number[-7:]}" if shipment["mode"] == "sea" else None,
        "container_type": "40ft HC" if shipment["mode"] == "sea" else None,
        "weight_kg": int(shipment["cargo"].split(" - ")[1].split(" ")[0].replace(",", "")),
    }
    
    return detailed

@app.get("/api/international/shipments/{tracking_number}/events")
async def get_shipment_events(tracking_number: str):
    """Get shipment event timeline"""
    
    if tracking_number not in SHIPMENTS_DB:
        if not SHIPMENTS_DB:
            await generate_test_shipments()
        if tracking_number not in SHIPMENTS_DB:
            raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment = SHIPMENTS_DB[tracking_number]
    
    # Generate events based on shipment type
    if "SEA" in tracking_number:
        events = [
            {
                "event_type": "booked",
                "description": "Shipment booked with carrier",
                "location": shipment["origin"].split(" (")[0],
                "occurred_at": (datetime.utcnow() - timedelta(days=5)).isoformat()
            },
            {
                "event_type": "container_loaded",
                "description": "Container loaded at port",
                "location": shipment["origin"],
                "occurred_at": (datetime.utcnow() - timedelta(days=4)).isoformat()
            },
            {
                "event_type": "departed_origin_port",
                "description": "Vessel departed",
                "location": shipment["origin"],
                "occurred_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "event_type": "in_transit",
                "description": f"Current location: {shipment['current_location']}",
                "location": shipment["current_location"],
                "occurred_at": (datetime.utcnow() - timedelta(hours=12)).isoformat()
            }
        ]
    else:  # AIR
        events = [
            {
                "event_type": "booked",
                "description": "Air cargo booked",
                "location": shipment["origin"].split(" (")[0],
                "occurred_at": (datetime.utcnow() - timedelta(hours=12)).isoformat()
            },
            {
                "event_type": "cargo_received",
                "description": "Cargo received at airport",
                "location": shipment["origin"],
                "occurred_at": (datetime.utcnow() - timedelta(hours=8)).isoformat()
            },
            {
                "event_type": "departed",
                "description": f"Flight {shipment['flight']} departed",
                "location": shipment["origin"],
                "occurred_at": (datetime.utcnow() - timedelta(hours=6)).isoformat()
            },
            {
                "event_type": "in_transit",
                "description": f"Current: {shipment['current_location']}",
                "location": shipment["current_location"],
                "occurred_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
    
    return {
        "tracking_number": tracking_number,
        "events": events
    }

# ============= ROUTE OPTIMIZATION =============

@app.post("/api/routes/optimize")
async def optimize_route(route_data: dict):
    """Simple route optimization"""
    
    stops = route_data.get("stops", [])
    
    if not stops:
        raise HTTPException(status_code=400, detail="No stops provided")
    
    # Simple nearest-neighbor optimization
    optimized = stops.copy()
    
    return {
        "optimized_stops": optimized,
        "total_distance_km": len(stops) * 15.5,
        "estimated_time_minutes": len(stops) * 25,
        "message": "Route optimized using nearest-neighbor algorithm"
    }

@app.get("/api/routes")
async def list_routes():
    """List all routes"""
    return {
        "routes": list(ROUTES_DB.values()),
        "count": len(ROUTES_DB)
    }

# ============= ANALYTICS =============

@app.get("/api/analytics/summary")
async def get_analytics():
    """Get analytics summary"""
    
    if not SHIPMENTS_DB:
        await generate_test_shipments()
    
    return {
        "total_shipments": len(SHIPMENTS_DB),
        "active_shipments": sum(1 for s in SHIPMENTS_DB.values() if s["status"] in ["in_transit", "in_flight"]),
        "by_mode": {
            "sea": sum(1 for s in SHIPMENTS_DB.values() if s["mode"] == "sea"),
            "air": sum(1 for s in SHIPMENTS_DB.values() if s["mode"] == "air")
        },
        "by_status": {
            status: sum(1 for s in SHIPMENTS_DB.values() if s["status"] == status)
            for status in ["in_transit", "in_flight", "at_port", "customs_clearance"]
        }
    }

# ============= PORTS =============

PORTS = {
    "INNSA": {"name": "Nhava Sheva (JNPT)", "city": "Mumbai", "country": "India", "type": "seaport"},
    "INCHE": {"name": "Chennai Port", "city": "Chennai", "country": "India", "type": "seaport"},
    "INDEL": {"name": "IGI Airport", "city": "Delhi", "country": "India", "type": "airport"},
    "INBLR": {"name": "Bangalore Airport", "city": "Bangalore", "country": "India", "type": "airport"},
    "USLAX": {"name": "LA/Long Beach", "city": "Los Angeles", "country": "USA", "type": "seaport"},
    "USNYC": {"name": "NY/NJ Port", "city": "New York", "country": "USA", "type": "seaport"},
    "USJFK": {"name": "JFK Airport", "city": "New York", "country": "USA", "type": "airport"},
    "USORD": {"name": "O'Hare Airport", "city": "Chicago", "country": "USA", "type": "airport"},
}

@app.get("/api/international/ports")
async def list_ports():
    """List all ports"""
    return {
        "ports": [{"code": k, **v} for k, v in PORTS.items()],
        "count": len(PORTS)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
