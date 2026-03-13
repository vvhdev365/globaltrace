"""
ULTIMATE GlobalTrace Backend - Combined Version
- Real Maersk & UPS API integration
- Smart routing (realistic routes)
- US Customs Entry Number tracking with ISF
- Simulation fallback
- CFR Part 11 ready architecture
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import httpx
import re
import os
from typing import Optional, List, Dict
import json
import base64
import random

app = FastAPI(
    title="GlobalTrace - Ultimate Edition",
    description="Real APIs + Smart Routing + Customs Tracking",
    version="6.0.0"
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

# API Keys
MAERSK_API_KEY = os.getenv("MAERSK_API_KEY", "")
MAERSK_CONSUMER_KEY = os.getenv("MAERSK_CONSUMER_KEY", "")
UPS_CLIENT_ID = os.getenv("UPS_CLIENT_ID", "")
UPS_CLIENT_SECRET = os.getenv("UPS_CLIENT_SECRET", "")

# Storage
TRACKED_SHIPMENTS = {}
CUSTOMS_ENTRIES = {}

# ============= CARRIER DETECTION =============

def detect_carrier(tracking_number: str) -> Dict:
    """Auto-detect carrier from tracking number format"""
    tracking_number = tracking_number.strip().replace(" ", "").upper()
    
    if re.match(r'^1Z[A-Z0-9]{16}$', tracking_number):
        return {"carrier": "UPS", "type": "domestic", "mode": "ground", "pattern": "UPS Ground", "has_api": True}
    elif re.match(r'^[A-Z]{4}\d{7}$', tracking_number):
        if tracking_number[:4] in ["MAEU", "MSCU", "CMAU", "HLCU"]:
            return {"carrier": "Maersk", "type": "international", "mode": "sea", "pattern": "Ocean Container", "has_api": True}
        return {"carrier": "Ocean Freight", "type": "international", "mode": "sea", "pattern": "Container", "has_api": False}
    elif re.match(r'^\d{12}$|^\d{15}$', tracking_number):
        return {"carrier": "FedEx", "type": "domestic", "mode": "express", "pattern": "FedEx Express", "has_api": False}
    elif re.match(r'^9\d{19,21}$', tracking_number):
        return {"carrier": "USPS", "type": "domestic", "mode": "mail", "pattern": "USPS", "has_api": False}
    elif re.match(r'^\d{3}-?\d{8}$', tracking_number):
        return {"carrier": "Air Cargo", "type": "international", "mode": "air", "pattern": "Air Waybill", "has_api": False}
    else:
        return {"carrier": "Unknown", "type": "unknown", "mode": "unknown", "pattern": "Custom", "has_api": False}

# ============= MAERSK API =============

async def track_maersk_container(container_number: str) -> Optional[Dict]:
    """Fetch REAL tracking data from Maersk API"""
    
    if not MAERSK_API_KEY:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://api.maersk.com/track-and-trace-private/v1/shipments/{container_number}"
            
            headers = {
                "Consumer-Key": MAERSK_CONSUMER_KEY,
                "API-Key": MAERSK_API_KEY,
                "Accept": "application/json"
            }
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return parse_maersk_response(data, container_number)
            
            return None
            
    except Exception as e:
        print(f"Maersk API error: {e}")
        return None

def parse_maersk_response(data: Dict, container_number: str) -> Dict:
    """Parse Maersk API response"""
    
    hops = []
    sequence = 1
    
    events = data.get("events", [])
    
    for event in events:
        hop = {
            "sequence": sequence,
            "timestamp": event.get("eventDateTime", datetime.utcnow().isoformat()),
            "location": event.get("location", {}).get("name", "Unknown"),
            "facility": event.get("facility", "Port Terminal"),
            "status": event.get("eventType", "in_transit").lower(),
            "description": event.get("description", "Shipment event"),
            "scan_type": event.get("eventType", "Status Update"),
            "data_source": "REAL - Maersk API"
        }
        
        if "vessel" in event:
            hop["vessel"] = event["vessel"].get("name")
            hop["vessel_imo"] = event["vessel"].get("imoNumber")
        
        hops.append(hop)
        sequence += 1
    
    current_hop = hops[-1] if hops else None
    completed = len(hops)
    
    return {
        "tracking_number": container_number,
        "carrier": "Maersk Line",
        "type": "international",
        "mode": "sea",
        "pattern": "Ocean Container",
        "current_status": current_hop["status"] if current_hop else "unknown",
        "current_location": current_hop["location"] if current_hop else "Unknown",
        "current_facility": current_hop.get("facility") if current_hop else None,
        "progress": 100 if data.get("status") == "DELIVERED" else 50,
        "total_hops": len(hops),
        "completed_hops": completed,
        "hops": hops,
        "last_update": current_hop["timestamp"] if current_hop else datetime.utcnow().isoformat(),
        "data_source": "REAL - Maersk API",
        "origin": data.get("origin", {}).get("name"),
        "destination": data.get("destination", {}).get("name")
    }

# ============= UPS API =============

async def get_ups_token() -> Optional[str]:
    """Get OAuth token from UPS"""
    
    if not UPS_CLIENT_ID or not UPS_CLIENT_SECRET:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            auth_string = f"{UPS_CLIENT_ID}:{UPS_CLIENT_SECRET}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = await client.post(
                "https://onlinetools.ups.com/security/v1/oauth/token",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                return response.json().get("access_token")
            
            return None
    except Exception as e:
        print(f"UPS OAuth error: {e}")
        return None

async def track_ups_package(tracking_number: str) -> Optional[Dict]:
    """Fetch REAL tracking data from UPS API"""
    
    token = await get_ups_token()
    if not token:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"https://onlinetools.ups.com/api/track/v1/details/{tracking_number}"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return parse_ups_response(data, tracking_number)
            
            return None
            
    except Exception as e:
        print(f"UPS API error: {e}")
        return None

def parse_ups_response(data: Dict, tracking_number: str) -> Dict:
    """Parse UPS API response"""
    
    hops = []
    sequence = 1
    
    shipment = data.get("trackResponse", {}).get("shipment", [{}])[0]
    package = shipment.get("package", [{}])[0]
    activities = package.get("activity", [])
    
    for activity in activities:
        location_data = activity.get("location", {}).get("address", {})
        location = f"{location_data.get('city', '')}, {location_data.get('stateProvinceCode', '')}"
        
        hop = {
            "sequence": sequence,
            "timestamp": activity.get("date", "") + "T" + activity.get("time", ""),
            "location": location,
            "facility": activity.get("location", {}).get("description", "UPS Facility"),
            "status": activity.get("status", {}).get("type", "in_transit").lower(),
            "description": activity.get("status", {}).get("description", "Package activity"),
            "scan_type": activity.get("status", {}).get("code", ""),
            "data_source": "REAL - UPS API"
        }
        
        hops.append(hop)
        sequence += 1
    
    hops.reverse()
    
    current_hop = hops[-1] if hops else None
    delivery_date = package.get("deliveryDate", [{}])[0]
    
    return {
        "tracking_number": tracking_number,
        "carrier": "UPS",
        "type": "domestic",
        "mode": "ground",
        "pattern": "UPS Ground",
        "current_status": current_hop["status"] if current_hop else "unknown",
        "current_location": current_hop["location"] if current_hop else "Unknown",
        "current_facility": current_hop.get("facility") if current_hop else None,
        "progress": 100 if delivery_date.get("type") == "DEL" else 70,
        "total_hops": len(hops),
        "completed_hops": len(hops),
        "hops": hops,
        "last_update": current_hop["timestamp"] if current_hop else datetime.utcnow().isoformat(),
        "data_source": "REAL - UPS API",
        "origin": None,
        "destination": None
    }

# ============= SMART ROUTING =============

def get_realistic_air_route(origin: str, destination: str) -> List[str]:
    """Generate realistic air routes"""
    
    if "india" in origin.lower() and "usa" in destination.lower():
        if "delhi" in origin.lower():
            if "new york" in destination.lower():
                return ["Delhi (DEL)", "New York (JFK)"]
            elif "chicago" in destination.lower():
                return ["Delhi (DEL)", "Chicago (ORD)"]
            elif "san francisco" in destination.lower():
                return ["Delhi (DEL)", "San Francisco (SFO)"]
        elif "mumbai" in origin.lower():
            if "newark" in destination.lower() or "new york" in destination.lower():
                return ["Mumbai (BOM)", "Newark (EWR)"]
        elif "bangalore" in origin.lower():
            return ["Bangalore (BLR)", "San Francisco (SFO)"]
        
        return ["Delhi (DEL)", "New York (JFK)"]
    
    origin_city = origin.split(",")[0].strip()
    dest_city = destination.split(",")[0].strip()
    return [origin_city, dest_city]

def get_realistic_sea_route(origin: str, destination: str) -> List[Dict]:
    """Generate realistic ocean routes"""
    
    if "india" in origin.lower() and ("los angeles" in destination.lower() or "oakland" in destination.lower()):
        return [
            {"port": "Colombo, Sri Lanka", "days": 5},
            {"port": "Singapore", "days": 10},
            {"port": "Hong Kong", "days": 15},
            {"port": "At Sea - Pacific Ocean", "days": 28},
        ]
    
    elif "india" in origin.lower() and ("new york" in destination.lower() or "savannah" in destination.lower()):
        return [
            {"port": "Colombo, Sri Lanka", "days": 5},
            {"port": "Suez Canal, Egypt", "days": 15},
            {"port": "Algeciras, Spain", "days": 20},
            {"port": "At Sea - Atlantic Ocean", "days": 30},
        ]
    
    return [{"port": "At Sea", "days": 14}]

# ============= US CUSTOMS TRACKING =============

def validate_customs_entry(entry_number: str) -> bool:
    """Validate US Customs Entry Number format"""
    pattern = r'^\d{3}-\d{7}-\d$'
    return bool(re.match(pattern, entry_number.replace(" ", "")))

def generate_customs_hops(entry_number: str, arrival_date: datetime) -> List[Dict]:
    """Generate US Customs clearance hops with ISF"""
    
    now = datetime.utcnow()
    hops = []
    
    isf_date = arrival_date - timedelta(days=3)
    
    hops.append({
        "sequence": 1,
        "timestamp": isf_date.isoformat(),
        "status": "isf_filed",
        "description": "ISF (Importer Security Filing) filed with CBP",
        "location": "Electronic Filing",
        "facility": "CBP AMS System",
        "entry_number": entry_number,
        "scan_type": "ISF-10+2 Filed",
        "detail": "Importer Security Filing submitted 72 hours before arrival",
        "data_source": "SIMULATED"
    })
    
    hops.append({
        "sequence": 2,
        "timestamp": (arrival_date - timedelta(days=1)).isoformat(),
        "status": "isf_accepted",
        "description": "ISF accepted by CBP",
        "location": "CBP AMS System",
        "facility": "Automated Manifest System",
        "entry_number": entry_number,
        "scan_type": "ISF Accepted",
        "detail": "No discrepancies - cleared for arrival",
        "data_source": "SIMULATED"
    })
    
    hops.append({
        "sequence": 3,
        "timestamp": arrival_date.isoformat(),
        "status": "arrival_notice",
        "description": "Cargo arrived at US port",
        "location": "US Port of Entry",
        "facility": "Port Terminal",
        "entry_number": entry_number,
        "scan_type": "Arrival Notice",
        "detail": "Vessel/aircraft arrival notification sent to CBP",
        "data_source": "SIMULATED"
    })
    
    hops.append({
        "sequence": 4,
        "timestamp": (arrival_date + timedelta(hours=6)).isoformat(),
        "status": "entry_filed",
        "description": "Customs entry filed",
        "location": "CBP ACE System",
        "facility": "Automated Commercial Environment",
        "entry_number": entry_number,
        "scan_type": "Entry Summary Filed",
        "detail": f"Entry #{entry_number} - duties estimated at $1,247.50",
        "data_source": "SIMULATED"
    })
    
    hops.append({
        "sequence": 5,
        "timestamp": (arrival_date + timedelta(hours=12)).isoformat(),
        "status": "under_review",
        "description": "Under CBP review",
        "location": "US Customs - Import Specialist",
        "facility": "CBP Import Review",
        "entry_number": entry_number,
        "scan_type": "Document Review",
        "detail": "Reviewing tariff classification and valuation",
        "data_source": "SIMULATED"
    })
    
    needs_exam = random.choice([False, False, True])
    
    if needs_exam:
        hops.append({
            "sequence": 6,
            "timestamp": (arrival_date + timedelta(hours=18)).isoformat(),
            "status": "exam_ordered",
            "description": "CBP exam ordered",
            "location": "Centralized Examination Station (CES)",
            "facility": "CBP Inspection Facility",
            "entry_number": entry_number,
            "scan_type": "Exam Ordered - VACIS",
            "detail": "Non-intrusive inspection (NII) + physical exam required",
            "exam_type": "VACIS Scan + Tailgate Inspection",
            "data_source": "SIMULATED"
        })
        
        hops.append({
            "sequence": 7,
            "timestamp": (arrival_date + timedelta(days=1, hours=8)).isoformat(),
            "status": "exam_completed",
            "description": "CBP exam completed - No issues",
            "location": "Centralized Examination Station",
            "facility": "CBP Inspection",
            "entry_number": entry_number,
            "scan_type": "Exam Completed",
            "detail": "Inspection results: No discrepancies found",
            "data_source": "SIMULATED"
        })
        
        release_time = arrival_date + timedelta(days=1, hours=12)
    else:
        hops.append({
            "sequence": 6,
            "timestamp": (arrival_date + timedelta(hours=20)).isoformat(),
            "status": "no_exam_required",
            "description": "No CBP exam required",
            "location": "CBP Automated Processing",
            "facility": "Risk-based Screening",
            "entry_number": entry_number,
            "scan_type": "Cleared Without Exam",
            "detail": "Low-risk shipment - automated release authorized",
            "data_source": "SIMULATED"
        })
        
        release_time = arrival_date + timedelta(hours=24)
    
    hops.append({
        "sequence": len(hops) + 1,
        "timestamp": release_time.isoformat(),
        "status": "duties_paid",
        "description": "Duties and fees paid",
        "location": "CBP Payment Processing",
        "facility": "ACE Payment System",
        "entry_number": entry_number,
        "scan_type": "Payment Received",
        "detail": "Total duties: $1,247.50 - Payment confirmed",
        "duties_amount": "$1,247.50",
        "data_source": "SIMULATED"
    })
    
    hops.append({
        "sequence": len(hops) + 1,
        "timestamp": (release_time + timedelta(hours=2)).isoformat(),
        "status": "released",
        "description": "Released by US Customs",
        "location": "US Customs - Port of Entry",
        "facility": "CBP Release Authorization",
        "entry_number": entry_number,
        "scan_type": "Customs Released",
        "detail": "Cargo released for domestic delivery",
        "release_code": "01 - Released",
        "data_source": "SIMULATED"
    })
    
    return hops

# ============= SMART SIMULATION =============

def generate_smart_hops(tracking_number: str, carrier_info: Dict, 
                       origin: str = None, destination: str = None,
                       customs_entry: str = None) -> List[Dict]:
    """Generate realistic hops with smart routing"""
    
    mode = carrier_info["mode"]
    carrier = carrier_info["carrier"]
    now = datetime.utcnow()
    hops = []
    
    if not origin:
        origin = "Los Angeles, CA, USA"
    if not destination:
        destination = "New York, NY, USA"
    
    if mode == "air":
        route = get_realistic_air_route(origin, destination)
        current_time = now - timedelta(days=3)
        
        hops.append({
            "sequence": 1,
            "timestamp": current_time.isoformat(),
            "location": route[0],
            "facility": f"{route[0].split('(')[0].strip()} Airport Cargo Terminal",
            "status": "manifested",
            "description": "Air waybill created",
            "scan_type": "AWB Manifested",
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(hours=12)
        hops.append({
            "sequence": 2,
            "timestamp": current_time.isoformat(),
            "location": route[0],
            "facility": "Airline Cargo Warehouse",
            "status": "received",
            "description": "Cargo received by airline",
            "scan_type": "Cargo Accepted",
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(hours=12)
        hops.append({
            "sequence": 3,
            "timestamp": current_time.isoformat(),
            "location": route[0],
            "facility": f"{route[0].split('(')[0].strip()} Airport",
            "status": "departed",
            "description": f"Departed on direct flight to {route[-1]}",
            "scan_type": "Flight Departed",
            "flight_info": "Direct flight - no transit stops",
            "data_source": "SIMULATED"
        })
        
        flight_time = 16 if "india" in origin.lower() else 8
        current_time += timedelta(hours=flight_time)
        hops.append({
            "sequence": 4,
            "timestamp": current_time.isoformat(),
            "location": route[-1],
            "facility": f"{route[-1].split('(')[0].strip()} International Airport",
            "status": "arrived",
            "description": "Arrived at destination",
            "scan_type": "Flight Arrived",
            "data_source": "SIMULATED"
        })
        
        if "usa" in destination.lower() and "usa" not in origin.lower():
            if customs_entry:
                customs_hops = generate_customs_hops(customs_entry, current_time)
                for ch in customs_hops:
                    ch["sequence"] = len(hops) + ch["sequence"]
                hops.extend(customs_hops)
                current_time = datetime.fromisoformat(customs_hops[-1]["timestamp"])
            else:
                current_time += timedelta(hours=24)
                hops.append({
                    "sequence": len(hops) + 1,
                    "timestamp": current_time.isoformat(),
                    "location": route[-1],
                    "facility": "US Customs",
                    "status": "customs_pending",
                    "description": "Awaiting customs clearance",
                    "scan_type": "Customs Processing",
                    "note": "Add Customs Entry Number (XXX-XXXXXXX-X) for detailed ISF/CBP tracking",
                    "data_source": "SIMULATED"
                })
        
        current_time += timedelta(hours=4)
        hops.append({
            "sequence": len(hops) + 1,
            "timestamp": current_time.isoformat(),
            "location": destination,
            "facility": "Delivery Service",
            "status": "out_for_delivery",
            "description": "Out for delivery",
            "scan_type": "Out For Delivery",
            "data_source": "SIMULATED"
        })
    
    elif mode == "sea":
        current_time = now - timedelta(days=35)
        route_ports = get_realistic_sea_route(origin, destination)
        
        hops.append({
            "sequence": 1,
            "timestamp": current_time.isoformat(),
            "location": origin,
            "facility": "Port Terminal",
            "status": "gate_in",
            "description": "Container received at port",
            "scan_type": "Gate In",
            "container": tracking_number,
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(days=1)
        hops.append({
            "sequence": 2,
            "timestamp": current_time.isoformat(),
            "location": origin,
            "facility": "Container Terminal",
            "status": "loaded",
            "description": "Loaded onto vessel",
            "scan_type": "Loaded",
            "vessel": "MSC ALTAIR",
            "vessel_imo": "9321483",
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(days=1)
        hops.append({
            "sequence": 3,
            "timestamp": current_time.isoformat(),
            "location": origin,
            "facility": f"Port of {origin.split(',')[0]}",
            "status": "departed",
            "description": "Vessel departed",
            "scan_type": "Vessel Departure",
            "data_source": "SIMULATED"
        })
        
        for port_info in route_ports:
            days = port_info["days"]
            port = port_info["port"]
            
            current_time = now - timedelta(days=35) + timedelta(days=days)
            
            if "At Sea" not in port:
                hops.append({
                    "sequence": len(hops) + 1,
                    "timestamp": current_time.isoformat(),
                    "location": port,
                    "facility": f"Port of {port.split(',')[0]}",
                    "status": "port_call",
                    "description": "Port call",
                    "scan_type": "Port Call",
                    "data_source": "SIMULATED"
                })
                
                current_time += timedelta(hours=18)
                hops.append({
                    "sequence": len(hops) + 1,
                    "timestamp": current_time.isoformat(),
                    "location": port,
                    "facility": f"Port of {port.split(',')[0]}",
                    "status": "departed",
                    "description": "Departed port",
                    "scan_type": "Vessel Departure",
                    "data_source": "SIMULATED"
                })
        
        arrival = now - timedelta(days=2)
        hops.append({
            "sequence": len(hops) + 1,
            "timestamp": arrival.isoformat(),
            "location": destination,
            "facility": f"Port of {destination.split(',')[0]}",
            "status": "arrived",
            "description": "Vessel arrived",
            "scan_type": "Vessel Arrival",
            "data_source": "SIMULATED"
        })
        
        if customs_entry and "usa" in destination.lower():
            customs_hops = generate_customs_hops(customs_entry, arrival)
            for ch in customs_hops:
                ch["sequence"] = len(hops) + ch["sequence"]
            hops.extend(customs_hops)
        else:
            hops.append({
                "sequence": len(hops) + 1,
                "timestamp": (arrival + timedelta(hours=12)).isoformat(),
                "location": destination,
                "facility": "US Customs",
                "status": "customs_pending",
                "description": "Awaiting customs clearance",
                "scan_type": "Customs Processing",
                "note": "Add Customs Entry Number (XXX-XXXXXXX-X) for ISF/CBP details",
                "data_source": "SIMULATED"
            })
    
    else:  # Domestic
        current_time = now - timedelta(days=2)
        
        hops.append({
            "sequence": 1,
            "timestamp": current_time.isoformat(),
            "location": origin,
            "facility": f"{carrier} Service Center",
            "status": "picked_up",
            "description": "Package picked up",
            "scan_type": "Pickup",
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(hours=24)
        hops.append({
            "sequence": 2,
            "timestamp": current_time.isoformat(),
            "location": "Regional Hub",
            "facility": f"{carrier} Hub",
            "status": "in_transit",
            "description": "In transit",
            "scan_type": "In Transit",
            "data_source": "SIMULATED"
        })
        
        current_time += timedelta(hours=24)
        hops.append({
            "sequence": 3,
            "timestamp": current_time.isoformat(),
            "location": destination,
            "facility": f"{carrier} Facility",
            "status": "out_for_delivery",
            "description": "Out for delivery",
            "scan_type": "Out For Delivery",
            "data_source": "SIMULATED"
        })
    
    return hops

# ============= MAIN TRACKING ENDPOINT =============

@app.post("/api/track/manual")
async def track_manually(data: dict):
    """Track shipment - tries REAL APIs first, falls back to smart simulation"""
    
    tracking_number = data.get("tracking_number", "").strip()
    origin = data.get("origin")
    destination = data.get("destination")
    customs_entry = data.get("customs_entry", "").strip()
    
    if not tracking_number:
        raise HTTPException(status_code=400, detail="Tracking number required")
    
    if customs_entry and not validate_customs_entry(customs_entry):
        raise HTTPException(status_code=400, detail="Invalid customs entry. Use format: XXX-XXXXXXX-X")
    
    carrier_info = detect_carrier(tracking_number)
    
    # Try REAL APIs first
    shipment = None
    
    if carrier_info["carrier"] == "Maersk" or (carrier_info["mode"] == "sea" and carrier_info.get("has_api")):
        print(f"Attempting Maersk API for {tracking_number}...")
        shipment = await track_maersk_container(tracking_number)
        if shipment:
            print("✅ Got REAL data from Maersk API")
    
    elif carrier_info["carrier"] == "UPS":
        print(f"Attempting UPS API for {tracking_number}...")
        shipment = await track_ups_package(tracking_number)
        if shipment:
            print("✅ Got REAL data from UPS API")
    
    # Fall back to smart simulation
    if not shipment:
        print(f"⚠️ API not available, using smart simulation for {tracking_number}")
        hops = generate_smart_hops(tracking_number, carrier_info, origin, destination, customs_entry)
        
        completed = sum(1 for h in hops if datetime.fromisoformat(h["timestamp"]) < datetime.utcnow())
        progress = int((completed / len(hops)) * 100) if hops else 0
        current = next((h for h in reversed(hops) if datetime.fromisoformat(h["timestamp"]) < datetime.utcnow()), hops[0] if hops else None)
        
        shipment = {
            "tracking_number": tracking_number,
            "carrier": carrier_info["carrier"],
            "type": carrier_info["type"],
            "mode": carrier_info["mode"],
            "pattern": carrier_info["pattern"],
            "origin": origin,
            "destination": destination,
            "customs_entry": customs_entry if customs_entry else None,
            "current_status": current["status"] if current else "unknown",
            "current_location": current["location"] if current else "Unknown",
            "current_facility": current.get("facility") if current else None,
            "progress": progress,
            "total_hops": len(hops),
            "completed_hops": completed,
            "hops": hops,
            "last_update": current["timestamp"] if current else datetime.utcnow().isoformat(),
            "data_source": "SIMULATED - No API available"
        }
    
    TRACKED_SHIPMENTS[tracking_number] = shipment
    
    if customs_entry:
        CUSTOMS_ENTRIES[customs_entry] = tracking_number
    
    return shipment

@app.get("/api/track/{tracking_number}")
async def get_tracking(tracking_number: str):
    tracking_number = tracking_number.strip().upper()
    if tracking_number in TRACKED_SHIPMENTS:
        return TRACKED_SHIPMENTS[tracking_number]
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/api/customs/{entry_number}")
async def get_customs(entry_number: str):
    if not validate_customs_entry(entry_number):
        raise HTTPException(status_code=400, detail="Invalid format")
    
    if entry_number in CUSTOMS_ENTRIES:
        tracking = CUSTOMS_ENTRIES[entry_number]
        shipment = TRACKED_SHIPMENTS.get(tracking)
        if shipment:
            customs_hops = [h for h in shipment["hops"] if "customs" in h["status"] or "isf" in h["status"]]
            return {
                "entry_number": entry_number,
                "tracking_number": tracking,
                "customs_hops": customs_hops
            }
    
    raise HTTPException(status_code=404, detail="Entry not found")

@app.get("/api/track/list")
async def list_tracked():
    return {
        "shipments": list(TRACKED_SHIPMENTS.values()),
        "count": len(TRACKED_SHIPMENTS)
    }

@app.delete("/api/track/{tracking_number}")
async def remove_tracking(tracking_number: str):
    tracking_number = tracking_number.strip().upper()
    if tracking_number in TRACKED_SHIPMENTS:
        del TRACKED_SHIPMENTS[tracking_number]
        return {"message": "Removed"}
    raise HTTPException(status_code=404, detail="Not found")

@app.get("/")
async def root():
    return {
        "message": "GlobalTrace - Ultimate Edition",
        "version": "6.0.0",
        "features": {
            "maersk_api": "enabled" if MAERSK_API_KEY else "disabled - set MAERSK_API_KEY",
            "ups_api": "enabled" if UPS_CLIENT_ID else "disabled - set UPS_CLIENT_ID",
            "smart_routing": "enabled",
            "us_customs_tracking": "enabled",
            "simulation_fallback": "enabled"
        },
        "supported_carriers": {
            "real_data": ["Maersk (ocean)", "UPS (domestic)"],
            "simulated": ["FedEx", "USPS", "Air Cargo", "Other carriers"]
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "apis": {
            "maersk": "configured" if MAERSK_API_KEY else "not configured",
            "ups": "configured" if UPS_CLIENT_ID else "not configured"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
