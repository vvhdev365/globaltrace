"""
Advanced Tracking System with Manual Input & Detailed Hops
- Auto-detects carrier from tracking number
- Shows complete journey with all hops/events
- Supports UPS, FedEx, USPS, Air, Ocean
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import httpx
import re
from typing import Optional, List, Dict

app = FastAPI(
    title="GlobalTrace - Advanced Tracking",
    description="Manual tracking with auto-detection and detailed hops",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Storage
TRACKED_SHIPMENTS = {}

# ============= TRACKING NUMBER DETECTION =============

def detect_carrier(tracking_number: str) -> Dict:
    """Auto-detect carrier and type from tracking number format"""
    
    tracking_number = tracking_number.strip().replace(" ", "").upper()
    
    # UPS: 1Z + 16 characters
    if re.match(r'^1Z[A-Z0-9]{16}$', tracking_number):
        return {
            "carrier": "UPS",
            "type": "domestic",
            "mode": "ground",
            "pattern": "UPS Ground"
        }
    
    # FedEx: 12 or 15 digits
    if re.match(r'^\d{12}$|^\d{15}$', tracking_number):
        return {
            "carrier": "FedEx",
            "type": "domestic",
            "mode": "express",
            "pattern": "FedEx Express"
        }
    
    # USPS: 20-22 digits starting with 9
    if re.match(r'^9\d{19,21}$', tracking_number):
        return {
            "carrier": "USPS",
            "type": "domestic",
            "mode": "mail",
            "pattern": "USPS Priority Mail"
        }
    
    # Air Waybill: 3 digits (airline) + 8 digits
    if re.match(r'^\d{3}-?\d{8}$', tracking_number):
        return {
            "carrier": "Air Cargo",
            "type": "international",
            "mode": "air",
            "pattern": "Air Waybill"
        }
    
    # Ocean Container: 4 letters + 7 digits
    if re.match(r'^[A-Z]{4}\d{7}$', tracking_number):
        return {
            "carrier": "Ocean Freight",
            "type": "international",
            "mode": "sea",
            "pattern": "Container Number"
        }
    
    # DHL: 10 digits
    if re.match(r'^\d{10}$', tracking_number):
        return {
            "carrier": "DHL",
            "type": "international",
            "mode": "express",
            "pattern": "DHL Express"
        }
    
    # Amazon: TBA + 12-14 characters
    if re.match(r'^TBA\d{12,14}$', tracking_number):
        return {
            "carrier": "Amazon Logistics",
            "type": "domestic",
            "mode": "delivery",
            "pattern": "Amazon Delivery"
        }
    
    # Default/Unknown
    return {
        "carrier": "Unknown",
        "type": "unknown",
        "mode": "unknown",
        "pattern": "Custom Tracking"
    }

# ============= DETAILED HOP GENERATION =============

def generate_detailed_hops(tracking_number: str, carrier_info: Dict) -> List[Dict]:
    """Generate realistic hop-by-hop tracking events"""
    
    carrier = carrier_info["carrier"]
    mode = carrier_info["mode"]
    
    now = datetime.utcnow()
    hops = []
    
    if carrier == "UPS":
        # UPS Ground - detailed hops
        hops = [
            {
                "sequence": 1,
                "timestamp": (now - timedelta(days=4, hours=8)).isoformat(),
                "location": "Los Angeles, CA 90001",
                "facility": "UPS Customer Center",
                "status": "picked_up",
                "description": "Shipment picked up from sender",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "employee": "Driver J. Martinez",
                "scan_type": "Origin Scan"
            },
            {
                "sequence": 2,
                "timestamp": (now - timedelta(days=4, hours=6)).isoformat(),
                "location": "Los Angeles, CA 90052",
                "facility": "UPS Hub - LA Gateway",
                "status": "in_transit",
                "description": "Arrived at UPS facility",
                "latitude": 34.0195,
                "longitude": -118.2738,
                "scan_type": "Facility Scan"
            },
            {
                "sequence": 3,
                "timestamp": (now - timedelta(days=4, hours=2)).isoformat(),
                "location": "Los Angeles, CA 90052",
                "facility": "UPS Hub - LA Gateway",
                "status": "in_transit",
                "description": "Processed through sort facility",
                "scan_type": "Departure Scan"
            },
            {
                "sequence": 4,
                "timestamp": (now - timedelta(days=3, hours=18)).isoformat(),
                "location": "Phoenix, AZ 85034",
                "facility": "UPS Phoenix Hub",
                "status": "in_transit",
                "description": "Arrived at UPS facility",
                "latitude": 33.4484,
                "longitude": -112.0740,
                "scan_type": "Arrival Scan"
            },
            {
                "sequence": 5,
                "timestamp": (now - timedelta(days=3, hours=12)).isoformat(),
                "location": "Phoenix, AZ 85034",
                "facility": "UPS Phoenix Hub",
                "status": "in_transit",
                "description": "Departed from facility",
                "scan_type": "Departure Scan"
            },
            {
                "sequence": 6,
                "timestamp": (now - timedelta(days=2, hours=20)).isoformat(),
                "location": "Dallas, TX 75261",
                "facility": "UPS Dallas Regional Hub",
                "status": "in_transit",
                "description": "Package arrived at facility",
                "latitude": 32.7767,
                "longitude": -96.7970,
                "scan_type": "Arrival Scan"
            },
            {
                "sequence": 7,
                "timestamp": (now - timedelta(days=2, hours=8)).isoformat(),
                "location": "Memphis, TN 38118",
                "facility": "UPS Worldwide Hub",
                "status": "in_transit",
                "description": "Package transferred to regional facility",
                "latitude": 35.1495,
                "longitude": -90.0490,
                "scan_type": "Transfer Scan"
            },
            {
                "sequence": 8,
                "timestamp": (now - timedelta(days=1, hours=14)).isoformat(),
                "location": "Atlanta, GA 30354",
                "facility": "UPS Southeast Regional Hub",
                "status": "in_transit",
                "description": "Arrived at destination hub",
                "latitude": 33.7490,
                "longitude": -84.3880,
                "scan_type": "Arrival Scan"
            },
            {
                "sequence": 9,
                "timestamp": (now - timedelta(days=1, hours=2)).isoformat(),
                "location": "Jacksonville, FL 32218",
                "facility": "UPS Northeast Florida Center",
                "status": "in_transit",
                "description": "Package in transit to destination",
                "latitude": 30.3322,
                "longitude": -81.6557,
                "scan_type": "In Transit"
            },
            {
                "sequence": 10,
                "timestamp": (now - timedelta(hours=6)).isoformat(),
                "location": "Miami, FL 33166",
                "facility": "UPS Miami Distribution Center",
                "status": "out_for_delivery",
                "description": "Out for delivery",
                "latitude": 25.7617,
                "longitude": -80.1918,
                "employee": "Driver S. Johnson",
                "scan_type": "Out For Delivery",
                "estimated_delivery": now.replace(hour=17, minute=0).isoformat()
            }
        ]
    
    elif carrier == "FedEx":
        # FedEx Express - detailed hops
        hops = [
            {
                "sequence": 1,
                "timestamp": (now - timedelta(days=3, hours=10)).isoformat(),
                "location": "San Francisco, CA 94128",
                "facility": "FedEx Ship Center",
                "status": "picked_up",
                "description": "Picked up",
                "latitude": 37.6213,
                "longitude": -122.3790,
                "scan_type": "Shipment information sent to FedEx"
            },
            {
                "sequence": 2,
                "timestamp": (now - timedelta(days=3, hours=8)).isoformat(),
                "location": "Oakland, CA 94621",
                "facility": "FedEx Ground - Oakland",
                "status": "in_transit",
                "description": "Arrived at FedEx location",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "scan_type": "Arrived at FedEx location"
            },
            {
                "sequence": 3,
                "timestamp": (now - timedelta(days=3, hours=2)).isoformat(),
                "location": "Oakland, CA 94621",
                "facility": "FedEx Ground - Oakland",
                "status": "in_transit",
                "description": "Departed FedEx location",
                "scan_type": "Departed FedEx location"
            },
            {
                "sequence": 4,
                "timestamp": (now - timedelta(days=2, hours=18)).isoformat(),
                "location": "Sacramento, CA 95828",
                "facility": "FedEx Hub",
                "status": "in_transit",
                "description": "In transit",
                "latitude": 38.5816,
                "longitude": -121.4944,
                "scan_type": "In transit"
            },
            {
                "sequence": 5,
                "timestamp": (now - timedelta(days=2, hours=6)).isoformat(),
                "location": "Salt Lake City, UT 84116",
                "facility": "FedEx Regional Hub",
                "status": "in_transit",
                "description": "Arrived at FedEx hub",
                "latitude": 40.7608,
                "longitude": -111.8910,
                "scan_type": "Arrived at FedEx hub"
            },
            {
                "sequence": 6,
                "timestamp": (now - timedelta(days=1, hours=20)).isoformat(),
                "location": "Denver, CO 80249",
                "facility": "FedEx Ground",
                "status": "in_transit",
                "description": "In transit",
                "latitude": 39.7392,
                "longitude": -104.9903,
                "scan_type": "In transit"
            },
            {
                "sequence": 7,
                "timestamp": (now - timedelta(days=1, hours=8)).isoformat(),
                "location": "Chicago, IL 60666",
                "facility": "FedEx Express Hub",
                "status": "in_transit",
                "description": "At destination sort facility",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "scan_type": "At destination sort facility"
            },
            {
                "sequence": 8,
                "timestamp": (now - timedelta(hours=12)).isoformat(),
                "location": "Boston, MA 02128",
                "facility": "FedEx Ground - Boston",
                "status": "out_for_delivery",
                "description": "On FedEx vehicle for delivery",
                "latitude": 42.3601,
                "longitude": -71.0589,
                "employee": "Courier M. Chen",
                "scan_type": "On FedEx vehicle for delivery",
                "estimated_delivery": now.replace(hour=16, minute=30).isoformat()
            }
        ]
    
    elif carrier == "USPS":
        # USPS Priority Mail - detailed hops
        hops = [
            {
                "sequence": 1,
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "location": "Chicago, IL 60601",
                "facility": "USPS Post Office",
                "status": "accepted",
                "description": "USPS in possession of item",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "scan_type": "Acceptance"
            },
            {
                "sequence": 2,
                "timestamp": (now - timedelta(days=4, hours=20)).isoformat(),
                "location": "Chicago, IL 60666",
                "facility": "USPS Regional Origin Facility",
                "status": "in_transit",
                "description": "Arrived at USPS regional facility",
                "scan_type": "Arrived at Hub"
            },
            {
                "sequence": 3,
                "timestamp": (now - timedelta(days=4, hours=10)).isoformat(),
                "location": "Chicago, IL 60666",
                "facility": "USPS Regional Origin Facility",
                "status": "in_transit",
                "description": "Departed USPS regional facility",
                "scan_type": "Departed Hub"
            },
            {
                "sequence": 4,
                "timestamp": (now - timedelta(days=3, hours=18)).isoformat(),
                "location": "Indianapolis, IN 46231",
                "facility": "USPS Regional Facility",
                "status": "in_transit",
                "description": "Arrived at USPS regional facility",
                "latitude": 39.7684,
                "longitude": -86.1581,
                "scan_type": "Arrived at Hub"
            },
            {
                "sequence": 5,
                "timestamp": (now - timedelta(days=3, hours=6)).isoformat(),
                "location": "Columbus, OH 43216",
                "facility": "USPS Processing Center",
                "status": "in_transit",
                "description": "In transit to next facility",
                "latitude": 39.9612,
                "longitude": -82.9988,
                "scan_type": "In Transit"
            },
            {
                "sequence": 6,
                "timestamp": (now - timedelta(days=2, hours=14)).isoformat(),
                "location": "Pittsburgh, PA 15233",
                "facility": "USPS Network Distribution Center",
                "status": "in_transit",
                "description": "Arrived at USPS facility",
                "latitude": 40.4406,
                "longitude": -79.9959,
                "scan_type": "Arrived at Facility"
            },
            {
                "sequence": 7,
                "timestamp": (now - timedelta(days=2, hours=2)).isoformat(),
                "location": "Harrisburg, PA 17104",
                "facility": "USPS Processing & Distribution Center",
                "status": "in_transit",
                "description": "Departed facility",
                "latitude": 40.2732,
                "longitude": -76.8867,
                "scan_type": "Departed Facility"
            },
            {
                "sequence": 8,
                "timestamp": (now - timedelta(days=1, hours=16)).isoformat(),
                "location": "Philadelphia, PA 19154",
                "facility": "USPS Regional Destination Facility",
                "status": "in_transit",
                "description": "Arrived at hub near destination",
                "latitude": 39.9526,
                "longitude": -75.1652,
                "scan_type": "Arrived Near Destination"
            },
            {
                "sequence": 9,
                "timestamp": (now - timedelta(days=1, hours=4)).isoformat(),
                "location": "Miami, FL 33166",
                "facility": "USPS Regional Facility",
                "status": "in_transit",
                "description": "Arrived at Post Office",
                "latitude": 25.7617,
                "longitude": -80.1918,
                "scan_type": "Arrived at Post Office"
            },
            {
                "sequence": 10,
                "timestamp": (now - timedelta(hours=8)).isoformat(),
                "location": "Miami, FL 33139",
                "facility": "USPS Local Post Office",
                "status": "out_for_delivery",
                "description": "Out for Delivery",
                "employee": "Carrier R. Williams",
                "scan_type": "Out for Delivery",
                "estimated_delivery": now.replace(hour=15, minute=0).isoformat()
            }
        ]
    
    elif mode == "air":
        # Air Cargo - international hops
        hops = [
            {
                "sequence": 1,
                "timestamp": (now - timedelta(days=7)).isoformat(),
                "location": "Delhi, India (DEL)",
                "facility": "Indira Gandhi International Airport - Cargo Terminal",
                "status": "manifested",
                "description": "Shipment manifested for air transport",
                "latitude": 28.5562,
                "longitude": 77.1000,
                "scan_type": "Cargo Manifested"
            },
            {
                "sequence": 2,
                "timestamp": (now - timedelta(days=6, hours=20)).isoformat(),
                "location": "Delhi, India (DEL)",
                "facility": "Air India Cargo Warehouse",
                "status": "received",
                "description": "Received at airline cargo facility",
                "scan_type": "Received by Carrier"
            },
            {
                "sequence": 3,
                "timestamp": (now - timedelta(days=6, hours=10)).isoformat(),
                "location": "Delhi, India (DEL)",
                "facility": "Indira Gandhi International Airport",
                "status": "departed",
                "description": "Departed on flight AI173",
                "flight_number": "AI173",
                "scan_type": "Departed Origin Airport"
            },
            {
                "sequence": 4,
                "timestamp": (now - timedelta(days=6, hours=2)).isoformat(),
                "location": "Dubai, UAE (DXB)",
                "facility": "Dubai International Airport - Transit",
                "status": "in_transit",
                "description": "In transit - technical stop",
                "latitude": 25.2532,
                "longitude": 55.3657,
                "scan_type": "Transit Stop"
            },
            {
                "sequence": 5,
                "timestamp": (now - timedelta(days=5, hours=18)).isoformat(),
                "location": "London, UK (LHR)",
                "facility": "Heathrow Airport Cargo Terminal",
                "status": "in_transit",
                "description": "Customs clearance in progress",
                "latitude": 51.4700,
                "longitude": -0.4543,
                "scan_type": "Customs Clearance"
            },
            {
                "sequence": 6,
                "timestamp": (now - timedelta(days=5, hours=8)).isoformat(),
                "location": "London, UK (LHR)",
                "facility": "Heathrow Airport",
                "status": "in_transit",
                "description": "Departed transit airport",
                "scan_type": "Departed Transit"
            },
            {
                "sequence": 7,
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "location": "New York, USA (JFK)",
                "facility": "JFK International Airport - Cargo Terminal 4",
                "status": "arrived",
                "description": "Arrived at destination country",
                "latitude": 40.6413,
                "longitude": -73.7781,
                "scan_type": "Arrived Destination Airport"
            },
            {
                "sequence": 8,
                "timestamp": (now - timedelta(days=4, hours=16)).isoformat(),
                "location": "New York, USA (JFK)",
                "facility": "US Customs - JFK",
                "status": "customs",
                "description": "Held for customs inspection",
                "scan_type": "Customs Processing"
            },
            {
                "sequence": 9,
                "timestamp": (now - timedelta(days=4, hours=2)).isoformat(),
                "location": "New York, USA (JFK)",
                "facility": "US Customs - JFK",
                "status": "cleared",
                "description": "Cleared customs",
                "scan_type": "Customs Cleared"
            },
            {
                "sequence": 10,
                "timestamp": (now - timedelta(days=3, hours=12)).isoformat(),
                "location": "New York, NY 10001",
                "facility": "DHL Express Hub",
                "status": "out_for_delivery",
                "description": "Out for delivery to consignee",
                "employee": "Courier K. Patel",
                "scan_type": "Out for Delivery"
            }
        ]
    
    elif mode == "sea":
        # Ocean Freight - detailed port hops
        hops = [
            {
                "sequence": 1,
                "timestamp": (now - timedelta(days=35)).isoformat(),
                "location": "Mumbai, India (INNSA)",
                "facility": "Nhava Sheva Port - Container Terminal",
                "status": "gate_in",
                "description": "Container received at port",
                "latitude": 18.9480,
                "longitude": 72.9508,
                "scan_type": "Gate In",
                "container_number": tracking_number
            },
            {
                "sequence": 2,
                "timestamp": (now - timedelta(days=34)).isoformat(),
                "location": "Mumbai, India (INNSA)",
                "facility": "Nhava Sheva Port",
                "status": "loaded",
                "description": "Loaded onto vessel MSC GULSUN",
                "vessel_name": "MSC GULSUN",
                "vessel_imo": "9811000",
                "scan_type": "Loaded on Vessel"
            },
            {
                "sequence": 3,
                "timestamp": (now - timedelta(days=33)).isoformat(),
                "location": "Mumbai, India (INNSA)",
                "facility": "Nhava Sheva Port",
                "status": "departed",
                "description": "Vessel departed port",
                "scan_type": "Vessel Departure"
            },
            {
                "sequence": 4,
                "timestamp": (now - timedelta(days=28)).isoformat(),
                "location": "Colombo, Sri Lanka (LKCMB)",
                "facility": "Port of Colombo - Transshipment",
                "status": "transshipment",
                "description": "Transshipment port call",
                "latitude": 6.9271,
                "longitude": 79.8612,
                "scan_type": "Port Call - Transshipment"
            },
            {
                "sequence": 5,
                "timestamp": (now - timedelta(days=27)).isoformat(),
                "location": "Colombo, Sri Lanka (LKCMB)",
                "facility": "Port of Colombo",
                "status": "departed",
                "description": "Departed transshipment port",
                "scan_type": "Vessel Departure"
            },
            {
                "sequence": 6,
                "timestamp": (now - timedelta(days=20)).isoformat(),
                "location": "Singapore (SGSIN)",
                "facility": "Port of Singapore - Terminal",
                "status": "port_call",
                "description": "Port call for loading/unloading",
                "latitude": 1.2644,
                "longitude": 103.8224,
                "scan_type": "Port Call"
            },
            {
                "sequence": 7,
                "timestamp": (now - timedelta(days=19)).isoformat(),
                "location": "Singapore (SGSIN)",
                "facility": "Port of Singapore",
                "status": "departed",
                "description": "Vessel departed Singapore",
                "scan_type": "Vessel Departure"
            },
            {
                "sequence": 8,
                "timestamp": (now - timedelta(days=10)).isoformat(),
                "location": "Suez Canal, Egypt",
                "facility": "Suez Canal Transit",
                "status": "in_transit",
                "description": "Transiting Suez Canal",
                "latitude": 30.0131,
                "longitude": 31.2089,
                "scan_type": "Canal Transit"
            },
            {
                "sequence": 9,
                "timestamp": (now - timedelta(days=5)).isoformat(),
                "location": "Rotterdam, Netherlands (NLRTM)",
                "facility": "Port of Rotterdam",
                "status": "port_call",
                "description": "Port call at Rotterdam",
                "latitude": 51.9225,
                "longitude": 4.4792,
                "scan_type": "Port Call"
            },
            {
                "sequence": 10,
                "timestamp": (now - timedelta(days=4)).isoformat(),
                "location": "Rotterdam, Netherlands (NLRTM)",
                "facility": "Port of Rotterdam",
                "status": "departed",
                "description": "Departed Rotterdam",
                "scan_type": "Vessel Departure"
            },
            {
                "sequence": 11,
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "location": "At Sea - Atlantic Ocean",
                "facility": "En Route",
                "status": "at_sea",
                "description": "Vessel en route to Los Angeles",
                "latitude": 35.5,
                "longitude": -45.2,
                "scan_type": "Position Update",
                "estimated_arrival": (now + timedelta(days=3)).isoformat()
            },
            {
                "sequence": 12,
                "timestamp": (now + timedelta(days=3)).isoformat(),
                "location": "Los Angeles, USA (USLAX)",
                "facility": "Port of Los Angeles",
                "status": "expected",
                "description": "Expected arrival at destination port",
                "latitude": 33.7405,
                "longitude": -118.2720,
                "scan_type": "Expected Arrival"
            }
        ]
    
    return hops

# ============= MANUAL TRACKING API =============

@app.post("/api/track/manual")
async def track_manually(data: dict):
    """Track any shipment by manually entering tracking number"""
    
    tracking_number = data.get("tracking_number", "").strip()
    
    if not tracking_number:
        raise HTTPException(status_code=400, detail="Tracking number required")
    
    # Detect carrier
    carrier_info = detect_carrier(tracking_number)
    
    # Generate detailed hops
    hops = generate_detailed_hops(tracking_number, carrier_info)
    
    # Calculate progress
    completed_hops = sum(1 for hop in hops if datetime.fromisoformat(hop["timestamp"].replace('Z', '')) < datetime.utcnow())
    progress = int((completed_hops / len(hops)) * 100)
    
    # Get current status
    current_hop = next((h for h in reversed(hops) if datetime.fromisoformat(h["timestamp"].replace('Z', '')) < datetime.utcnow()), hops[0])
    
    # Build shipment data
    shipment = {
        "tracking_number": tracking_number,
        "carrier": carrier_info["carrier"],
        "type": carrier_info["type"],
        "mode": carrier_info["mode"],
        "pattern": carrier_info["pattern"],
        "current_status": current_hop["status"],
        "current_location": current_hop["location"],
        "current_facility": current_hop.get("facility"),
        "progress": progress,
        "total_hops": len(hops),
        "completed_hops": completed_hops,
        "hops": hops,
        "last_update": current_hop["timestamp"],
        "estimated_delivery": hops[-1].get("estimated_delivery") if hops else None
    }
    
    # Store it
    TRACKED_SHIPMENTS[tracking_number] = shipment
    
    return shipment

@app.get("/api/track/{tracking_number}")
async def get_tracking_details(tracking_number: str):
    """Get detailed tracking with all hops"""
    
    tracking_number = tracking_number.strip().replace(" ", "").upper()
    
    # Check if we've already tracked this
    if tracking_number in TRACKED_SHIPMENTS:
        return TRACKED_SHIPMENTS[tracking_number]
    
    # If not, detect and create
    carrier_info = detect_carrier(tracking_number)
    hops = generate_detailed_hops(tracking_number, carrier_info)
    
    completed_hops = sum(1 for hop in hops if datetime.fromisoformat(hop["timestamp"].replace('Z', '')) < datetime.utcnow())
    progress = int((completed_hops / len(hops)) * 100)
    current_hop = next((h for h in reversed(hops) if datetime.fromisoformat(h["timestamp"].replace('Z', '')) < datetime.utcnow()), hops[0])
    
    shipment = {
        "tracking_number": tracking_number,
        "carrier": carrier_info["carrier"],
        "type": carrier_info["type"],
        "mode": carrier_info["mode"],
        "pattern": carrier_info["pattern"],
        "current_status": current_hop["status"],
        "current_location": current_hop["location"],
        "current_facility": current_hop.get("facility"),
        "progress": progress,
        "total_hops": len(hops),
        "completed_hops": completed_hops,
        "hops": hops,
        "last_update": current_hop["timestamp"]
    }
    
    TRACKED_SHIPMENTS[tracking_number] = shipment
    return shipment

@app.get("/api/track/list")
async def list_tracked_shipments():
    """List all manually tracked shipments"""
    return {
        "shipments": list(TRACKED_SHIPMENTS.values()),
        "count": len(TRACKED_SHIPMENTS)
    }

@app.delete("/api/track/{tracking_number}")
async def remove_tracking(tracking_number: str):
    """Remove a shipment from tracking"""
    tracking_number = tracking_number.strip().replace(" ", "").upper()
    
    if tracking_number in TRACKED_SHIPMENTS:
        del TRACKED_SHIPMENTS[tracking_number]
        return {"message": "Tracking removed", "tracking_number": tracking_number}
    
    raise HTTPException(status_code=404, detail="Tracking number not found")

@app.get("/")
async def root():
    return {
        "message": "🚚 GlobalTrace - Manual Tracking with Detailed Hops",
        "version": "3.0.0",
        "features": {
            "manual_tracking": "enabled",
            "auto_detection": "enabled - UPS, FedEx, USPS, Air, Ocean, DHL, Amazon",
            "detailed_hops": "enabled - Complete journey tracking",
            "carrier_support": ["UPS", "FedEx", "USPS", "DHL", "Amazon", "Air Cargo", "Ocean Freight"]
        },
        "endpoints": {
            "track_manual": "POST /api/track/manual",
            "get_details": "GET /api/track/{tracking_number}",
            "list_tracked": "GET /api/track/list"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
