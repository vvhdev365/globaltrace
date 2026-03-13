"""
GlobalTrace - HONEST Edition
Only real carrier websites - NO fake data
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
import os
from typing import Dict

app = FastAPI(
    title="GlobalTrace - Honest Edition",
    description="Direct links to real carrier tracking websites",
    version="9.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# ============= CARRIER DETECTION =============

def detect_carrier(tracking_number: str) -> Dict:
    """Detect carrier and return their official tracking URL"""
    
    clean = tracking_number.strip().upper().replace(" ", "").replace("-", "")
    
    # UPS: 1Z + 16 characters
    if re.match(r'^1Z[A-Z0-9]{16}$', clean):
        return {
            "carrier": "UPS",
            "tracking_number": clean,
            "url": "https://www.ups.com/track",
            "direct_url": f"https://www.ups.com/track?tracknum={clean}",
            "type": "express",
            "can_embed": True
        }
    
    # FedEx: 12 or 15 digits
    if re.match(r'^\d{12}$|^\d{15}$', clean):
        return {
            "carrier": "FedEx",
            "tracking_number": clean,
            "url": "https://www.fedex.com/fedextrack/",
            "direct_url": f"https://www.fedex.com/fedextrack/?tracknumbers={clean}",
            "type": "express",
            "can_embed": True
        }
    
    # DHL: 10 digits
    if re.match(r'^\d{10}$', clean):
        return {
            "carrier": "DHL Express",
            "tracking_number": clean,
            "url": "https://www.dhl.com/us-en/home/tracking.html",
            "direct_url": f"https://www.dhl.com/us-en/home/tracking/tracking-express.html?submit=1&tracking-id={clean}",
            "type": "express",
            "can_embed": False
        }
    
    # USPS: 9400... or 9200... (20-22 digits)
    if re.match(r'^9[2-4]\d{18,20}$', clean):
        return {
            "carrier": "USPS",
            "tracking_number": clean,
            "url": "https://tools.usps.com/go/TrackConfirmAction",
            "direct_url": f"https://tools.usps.com/go/TrackConfirmAction?tLabels={clean}",
            "type": "mail",
            "can_embed": True
        }
    
    # Container: 4 letters + 7 digits
    if re.match(r'^[A-Z]{4}\d{7}$', clean):
        prefix = clean[:4]
        
        carriers = {
            "MAEU": {"name": "Maersk", "url": "https://www.maersk.com/tracking", "can_embed": False},
            "MSCU": {"name": "MSC", "url": "https://www.msc.com/en/track-a-shipment", "can_embed": False},
            "CMAU": {"name": "CMA CGM", "url": "https://www.cma-cgm.com/ebusiness/tracking", "can_embed": False},
            "COSU": {"name": "COSCO", "url": "https://elines.coscoshipping.com/ebusiness/cargoTracking", "can_embed": False},
            "HLCU": {"name": "Hapag-Lloyd", "url": "https://www.hapag-lloyd.com/en/online-business/track/track-by-container.html", "can_embed": False},
            "ONEY": {"name": "ONE", "url": "https://ecomm.one-line.com/ecom/CUP_HOM_3301.do", "can_embed": False},
            "EISU": {"name": "Evergreen", "url": "https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do", "can_embed": False},
        }
        
        carrier_info = carriers.get(prefix, {"name": "Ocean Carrier", "url": "https://www.google.com/search?q=container+tracking", "can_embed": True})
        
        return {
            "carrier": carrier_info["name"],
            "tracking_number": clean,
            "url": carrier_info["url"],
            "direct_url": carrier_info["url"],
            "type": "ocean",
            "can_embed": carrier_info["can_embed"],
            "note": f"Enter container number: {clean}"
        }
    
    # Air Waybill: XXX-XXXXXXXX (3 digits/letters, dash, 8 digits)
    awb_match = re.match(r'^(\d{3})-?(\d{8})$', tracking_number.strip())
    if awb_match:
        prefix = awb_match.group(1)
        full_awb = f"{prefix}-{awb_match.group(2)}"
        
        airlines = {
            "098": {"name": "Air India Cargo", "url": "https://www.airindia.com/in/en/manage/track-cargo.html", "can_embed": False},
            "176": {"name": "Emirates SkyCargo", "url": "https://www.skycargo.com/track", "can_embed": False},
            "235": {"name": "Turkish Cargo", "url": "https://cargo.turkishairlines.com/en-INT/track-shipment", "can_embed": False},
            "020": {"name": "Lufthansa Cargo", "url": "https://www.lufthansa-cargo.com/tracking", "can_embed": False},
            "157": {"name": "Qatar Airways Cargo", "url": "https://www.qrcargo.com/track", "can_embed": False},
            "607": {"name": "Etihad Cargo", "url": "https://www.etihadcargo.com/en/track", "can_embed": False},
            "057": {"name": "Air France KLM Cargo", "url": "https://www.afklcargo.com/WW/en/common/tracking/track.jsp", "can_embed": False},
            "125": {"name": "British Airways World Cargo", "url": "https://www.iacargo.com/iCargo/tracking.do", "can_embed": False},
            "618": {"name": "Singapore Airlines Cargo", "url": "https://www.siacargo.com/track-trace", "can_embed": False},
            "160": {"name": "Cathay Pacific Cargo", "url": "https://www.cathaypacificcargo.com/track", "can_embed": False},
        }
        
        airline_info = airlines.get(prefix, {"name": "Air Cargo", "url": "https://www.google.com/search?q=air+cargo+tracking", "can_embed": True})
        
        return {
            "carrier": airline_info["name"],
            "tracking_number": full_awb,
            "url": airline_info["url"],
            "direct_url": airline_info["url"],
            "type": "air",
            "can_embed": airline_info["can_embed"],
            "note": f"Enter AWB: {full_awb}"
        }
    
    # Unknown format
    return None

# ============= MAIN ENDPOINT =============

@app.post("/api/track")
async def track_shipment(data: dict):
    """Detect carrier and return their tracking URL"""
    
    tracking_input = data.get("tracking_input", "").strip()
    
    if not tracking_input:
        raise HTTPException(status_code=400, detail="Please enter a tracking number")
    
    result = detect_carrier(tracking_input)
    
    if not result:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Cannot recognize tracking number format: '{tracking_input}'",
                "supported_formats": [
                    "UPS: 1Z999AA10123456784",
                    "FedEx: 123456789012 or 123456789012345",
                    "USPS: 9400111899562537289741",
                    "DHL: 1234567890",
                    "Maersk Container: MAEU1234567",
                    "Air Waybill: 176-12345678",
                ],
                "note": "For U.S. Customs entries, contact your customs broker directly"
            }
        )
    
    return {
        "success": True,
        "carrier": result["carrier"],
        "tracking_number": result["tracking_number"],
        "url": result.get("direct_url", result["url"]),
        "search_url": result["url"],
        "type": result["type"],
        "can_embed": result.get("can_embed", False),
        "note": result.get("note", ""),
        "message": f"Opening {result['carrier']} tracking page"
    }

@app.get("/")
async def root():
    return {
        "name": "GlobalTrace - Honest Edition",
        "version": "9.0.0",
        "description": "Direct links to real carrier tracking websites",
        "data_policy": "NO FAKE DATA - Only links to official carrier websites",
        "supported_carriers": {
            "express": ["UPS", "FedEx", "DHL", "USPS"],
            "ocean": ["Maersk", "MSC", "CMA CGM", "COSCO", "Hapag-Lloyd", "ONE", "Evergreen"],
            "air": ["Air India", "Emirates", "Turkish", "Lufthansa", "Qatar", "Etihad", "Air France KLM", "British Airways", "Singapore", "Cathay Pacific"]
        },
        "note": "For U.S. Customs status, contact your customs broker"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "9.0.0", "data": "real_only"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
