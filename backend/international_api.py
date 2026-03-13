"""
International Shipment API Endpoints
Add these to your main.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from database import get_db
from international_models import (
    InternationalShipment, ShipmentEvent, ShipmentLeg, 
    Port, VesselPosition, FlightPosition, CustomsClearance,
    TransportMode, ShipmentStatus
)
from tracking_service import (
    TrackingService, PortDatabase, ShipmentEstimator,
    generate_test_shipment_india_to_us
)

# Create router
router = APIRouter(prefix="/api/international", tags=["International Shipments"])

# Initialize tracking service
tracking_service = TrackingService()


# ============= SHIPMENT ENDPOINTS =============

@router.get("/shipments")
async def list_shipments(
    status: Optional[str] = None,
    mode: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all international shipments with optional filters
    """
    # For MVP, return mock data
    # In production, query database
    
    shipments = [
        generate_test_shipment_india_to_us("sea"),
        generate_test_shipment_india_to_us("air")
    ]
    
    return {"shipments": shipments, "count": len(shipments)}


@router.get("/shipments/{tracking_number}")
async def get_shipment(
    tracking_number: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed shipment information with real-time tracking
    """
    # Generate test data
    if "SEA" in tracking_number:
        shipment_data = generate_test_shipment_india_to_us("sea")
    else:
        shipment_data = generate_test_shipment_india_to_us("air")
    
    # Get real-time position
    position = await tracking_service.track_shipment(shipment_data)
    
    if position:
        shipment_data["current_lat"] = position.get("lat")
        shipment_data["current_lng"] = position.get("lng")
        shipment_data["current_speed"] = position.get("speed")
    
    return shipment_data


@router.post("/shipments")
async def create_shipment(shipment_data: dict, db: AsyncSession = Depends(get_db)):
    """
    Create new international shipment
    """
    # In production, create database record
    return {
        "message": "Shipment created successfully",
        "tracking_number": shipment_data.get("tracking_number"),
        "status": "booked"
    }


@router.get("/shipments/{tracking_number}/track")
async def track_shipment_realtime(tracking_number: str):
    """
    Get real-time position of vessel or flight
    """
    # Get shipment details
    if "SEA" in tracking_number:
        shipment_data = generate_test_shipment_india_to_us("sea")
    else:
        shipment_data = generate_test_shipment_india_to_us("air")
    
    # Track in real-time
    position = await tracking_service.track_shipment(shipment_data)
    
    if not position:
        return {
            "tracking_number": tracking_number,
            "status": "position_unavailable",
            "message": "Real-time position not available. Using last known position."
        }
    
    return {
        "tracking_number": tracking_number,
        "position": position,
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/shipments/{tracking_number}/events")
async def get_shipment_events(tracking_number: str):
    """
    Get shipment event history (milestones)
    """
    # Generate sample events
    if "SEA" in tracking_number:
        events = [
            {
                "event_type": "booked",
                "description": "Shipment booked with carrier",
                "location": "Mumbai, India",
                "occurred_at": (datetime.utcnow() - timedelta(days=5)).isoformat()
            },
            {
                "event_type": "container_loaded",
                "description": "Container loaded at JNPT Port",
                "location": "Nhava Sheva Port, Mumbai",
                "occurred_at": (datetime.utcnow() - timedelta(days=4)).isoformat()
            },
            {
                "event_type": "departed_origin_port",
                "description": "Vessel departed from Mumbai",
                "location": "Mumbai Port, India",
                "occurred_at": (datetime.utcnow() - timedelta(days=3)).isoformat()
            },
            {
                "event_type": "in_transit",
                "description": "Vessel in transit - Indian Ocean",
                "location": "Indian Ocean",
                "occurred_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
            }
        ]
    else:  # air
        events = [
            {
                "event_type": "booked",
                "description": "Air cargo booked",
                "location": "Delhi, India",
                "occurred_at": (datetime.utcnow() - timedelta(hours=12)).isoformat()
            },
            {
                "event_type": "cargo_received",
                "description": "Cargo received at IGI Airport",
                "location": "Indira Gandhi Airport, Delhi",
                "occurred_at": (datetime.utcnow() - timedelta(hours=8)).isoformat()
            },
            {
                "event_type": "departed",
                "description": "Flight AI173 departed",
                "location": "Delhi, India",
                "occurred_at": (datetime.utcnow() - timedelta(hours=6)).isoformat()
            },
            {
                "event_type": "in_flight",
                "description": "In transit to New York",
                "location": "Over Atlantic Ocean",
                "occurred_at": (datetime.utcnow() - timedelta(hours=2)).isoformat()
            }
        ]
    
    return {"tracking_number": tracking_number, "events": events}


# ============= PORT ENDPOINTS =============

@router.get("/ports")
async def list_ports(type: Optional[str] = None):
    """
    List all ports and airports
    """
    ports = PortDatabase.get_all_ports()
    
    if type:
        ports = {k: v for k, v in ports.items() if v.get("type") == type}
    
    return {"ports": [{"code": k, **v} for k, v in ports.items()]}


@router.get("/ports/{code}")
async def get_port(code: str):
    """
    Get port details by code
    """
    port = PortDatabase.get_port(code)
    if not port:
        raise HTTPException(status_code=404, detail="Port not found")
    
    return port


# ============= VESSEL TRACKING =============

@router.get("/vessels/{imo}/position")
async def get_vessel_position(imo: str):
    """
    Get current vessel position by IMO number
    """
    position = await tracking_service.vessel_tracker.get_vessel_position(imo)
    
    if not position:
        raise HTTPException(status_code=404, detail="Vessel position not available")
    
    return position


@router.get("/vessels/{imo}/route")
async def get_vessel_route(imo: str, hours: int = 24):
    """
    Get vessel historical route
    """
    route = await tracking_service.vessel_tracker.get_vessel_route(imo, hours)
    return {"imo": imo, "route": route, "hours": hours}


# ============= FLIGHT TRACKING =============

@router.get("/flights/{flight_number}/position")
async def get_flight_position(flight_number: str):
    """
    Get current flight position
    """
    position = await tracking_service.flight_tracker.get_flight_position(flight_number)
    
    if not position:
        raise HTTPException(status_code=404, detail="Flight position not available")
    
    return position


# ============= CUSTOMS =============

@router.get("/shipments/{tracking_number}/customs")
async def get_customs_status(tracking_number: str):
    """
    Get customs clearance status
    """
    return {
        "tracking_number": tracking_number,
        "customs_status": "cleared",
        "clearance_date": datetime.utcnow().isoformat(),
        "entry_number": "ENT-2024-123456",
        "customs_office": "US Customs - Los Angeles",
        "duties_amount": 1250.00,
        "taxes_amount": 450.00,
        "currency": "USD"
    }


# ============= ANALYTICS =============

@router.get("/analytics/transit-times")
async def get_transit_time_analytics(
    origin: Optional[str] = None,
    destination: Optional[str] = None
):
    """
    Get average transit times between ports
    """
    return {
        "routes": [
            {
                "origin": "INNSA",
                "destination": "USLAX",
                "mode": "sea",
                "avg_days": 25,
                "min_days": 22,
                "max_days": 30
            },
            {
                "origin": "INDEL",
                "destination": "USJFK",
                "mode": "air",
                "avg_days": 2,
                "min_days": 1.5,
                "max_days": 3
            }
        ]
    }


@router.get("/analytics/shipment-volume")
async def get_shipment_volume():
    """
    Get shipment volume statistics
    """
    return {
        "total_shipments": 150,
        "by_mode": {
            "sea": 120,
            "air": 30
        },
        "by_status": {
            "in_transit": 45,
            "at_port": 15,
            "customs_clearance": 10,
            "delivered": 80
        },
        "by_origin_country": {
            "India": 75,
            "China": 50,
            "Vietnam": 25
        }
    }


# ============= TEST DATA GENERATION =============

@router.post("/test/generate-shipments")
async def generate_test_shipments():
    """
    Generate test shipments from India to US for demonstration
    """
    shipments = [
        {
            "tracking_number": "IND-USA-SEA-001",
            "mode": "sea",
            "origin": "Mumbai (INNSA)",
            "destination": "Los Angeles (USLAX)",
            "vessel": "MSC GULSUN (IMO: 9811000)",
            "status": "in_transit",
            "cargo": "Electronics - 18,000 kg"
        },
        {
            "tracking_number": "IND-USA-SEA-002",
            "mode": "sea",
            "origin": "Chennai (INCHE)",
            "destination": "New York (USNYC)",
            "vessel": "EVER ACE (IMO: 9811850)",
            "status": "at_port",
            "cargo": "Textiles - 22,000 kg"
        },
        {
            "tracking_number": "IND-USA-AIR-001",
            "mode": "air",
            "origin": "Delhi (INDEL)",
            "destination": "New York (USJFK)",
            "flight": "AI173",
            "status": "in_flight",
            "cargo": "Pharmaceuticals - 500 kg (Temperature Controlled)"
        },
        {
            "tracking_number": "IND-USA-AIR-002",
            "mode": "air",
            "origin": "Bangalore (INBLR)",
            "destination": "Chicago (USORD)",
            "flight": "AI127",
            "status": "customs_clearance",
            "cargo": "IT Equipment - 350 kg"
        }
    ]
    
    return {
        "message": "Test shipments generated",
        "shipments": shipments,
        "count": len(shipments)
    }


# To add to main.py:
# from international_api import router as international_router
# app.include_router(international_router)
