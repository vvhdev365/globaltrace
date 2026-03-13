"""
International Shipment Tracking Service
Integrates with free APIs for vessel and flight tracking
"""

import httpx
import asyncio
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import os


class VesselTracker:
    """
    Track vessels using free AIS data APIs
    
    Free Options:
    1. VesselFinder API (free tier available)
    2. MarineTraffic (limited free access)
    3. AIS Hub (community data)
    """
    
    def __init__(self):
        self.api_key = os.getenv("VESSELFINDER_API_KEY", "")  # Optional
        
    async def get_vessel_position(self, imo_number: str) -> Optional[Dict]:
        """
        Get current vessel position by IMO number
        
        Free alternative: Use public AIS data sources
        """
        try:
            # Example using public AIS data (no API key needed for basic data)
            url = f"https://www.vesselfinder.com/api/pub/vesseltrack?imo={imo_number}"
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "imo": imo_number,
                        "lat": data.get("LAT"),
                        "lng": data.get("LON"),
                        "speed": data.get("SPEED"),
                        "course": data.get("COURSE"),
                        "destination": data.get("DESTINATION"),
                        "eta": data.get("ETA"),
                        "status": data.get("NAVSTAT"),
                        "timestamp": datetime.utcnow()
                    }
        except Exception as e:
            print(f"Error tracking vessel {imo_number}: {e}")
            return None
    
    async def get_vessel_route(self, imo_number: str, hours: int = 24) -> List[Dict]:
        """
        Get vessel historical positions
        """
        # Placeholder - would fetch from AIS historical data
        return []
    
    async def estimate_arrival(self, imo_number: str, destination_port: str) -> Optional[datetime]:
        """
        Estimate vessel arrival time at destination
        """
        position = await self.get_vessel_position(imo_number)
        if not position:
            return None
        
        # Simple calculation - would use actual routing in production
        # For now, return current ETA if available
        if position.get("eta"):
            return position["eta"]
        
        return None


class FlightTracker:
    """
    Track flights using free aviation APIs
    
    Free Options:
    1. AviationStack (free tier: 100 requests/month)
    2. FlightAware (limited free access)
    3. OpenSky Network (free, open data)
    """
    
    def __init__(self):
        self.api_key = os.getenv("AVIATIONSTACK_API_KEY", "")
        self.use_opensky = True  # Use free OpenSky Network by default
        
    async def get_flight_position(self, flight_number: str) -> Optional[Dict]:
        """
        Get current flight position
        
        Using OpenSky Network (100% free, no API key needed)
        """
        try:
            if self.use_opensky:
                return await self._get_position_opensky(flight_number)
            else:
                return await self._get_position_aviationstack(flight_number)
        except Exception as e:
            print(f"Error tracking flight {flight_number}: {e}")
            return None
    
    async def _get_position_opensky(self, flight_number: str) -> Optional[Dict]:
        """
        Use OpenSky Network (free, no API key)
        """
        url = "https://opensky-network.org/api/states/all"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Search for matching flight
                for state in data.get("states", []):
                    callsign = state[1].strip() if state[1] else ""
                    if callsign.upper() == flight_number.upper():
                        return {
                            "flight_number": flight_number,
                            "lat": state[6],
                            "lng": state[5],
                            "altitude_m": state[7],
                            "speed_m_s": state[9],
                            "heading": state[10],
                            "on_ground": state[8],
                            "timestamp": datetime.fromtimestamp(state[3])
                        }
        
        return None
    
    async def _get_position_aviationstack(self, flight_number: str) -> Optional[Dict]:
        """
        Use AviationStack (requires API key, free tier available)
        """
        if not self.api_key:
            return None
            
        url = f"http://api.aviationstack.com/v1/flights"
        params = {
            "access_key": self.api_key,
            "flight_iata": flight_number
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    flight = data["data"][0]
                    live = flight.get("live", {})
                    
                    return {
                        "flight_number": flight_number,
                        "lat": live.get("latitude"),
                        "lng": live.get("longitude"),
                        "altitude_m": live.get("altitude"),
                        "speed_km_h": live.get("speed_horizontal"),
                        "heading": live.get("direction"),
                        "status": flight.get("flight_status"),
                        "timestamp": datetime.utcnow()
                    }
        
        return None


class PortDatabase:
    """
    Database of major ports and airports
    Pre-loaded data for quick lookups
    """
    
    # Major Indian ports
    INDIAN_PORTS = {
        "INNSA": {"name": "Nhava Sheva (JNPT)", "city": "Mumbai", "lat": 18.9484, "lng": 72.9491, "type": "seaport"},
        "INMUN": {"name": "Mumbai Port", "city": "Mumbai", "lat": 18.9386, "lng": 72.8361, "type": "seaport"},
        "INCHE": {"name": "Chennai Port", "city": "Chennai", "lat": 13.0827, "lng": 80.2707, "type": "seaport"},
        "INCOK": {"name": "Kochi Port", "city": "Kochi", "lat": 9.9605, "lng": 76.2673, "type": "seaport"},
        "INVTZ": {"name": "Visakhapatnam Port", "city": "Visakhapatnam", "lat": 17.6868, "lng": 83.2185, "type": "seaport"},
        "INDEL": {"name": "Indira Gandhi Airport", "city": "Delhi", "lat": 28.5562, "lng": 77.1000, "type": "airport"},
        "INBLR": {"name": "Bangalore Airport", "city": "Bangalore", "lat": 13.1986, "lng": 77.7066, "type": "airport"},
        "INMAA": {"name": "Chennai Airport", "city": "Chennai", "lat": 12.9941, "lng": 80.1709, "type": "airport"},
    }
    
    # Major US ports
    US_PORTS = {
        "USLAX": {"name": "Los Angeles/Long Beach", "city": "Los Angeles", "lat": 33.7366, "lng": -118.2725, "type": "seaport"},
        "USNYC": {"name": "New York/New Jersey", "city": "New York", "lat": 40.6653, "lng": -74.0806, "type": "seaport"},
        "USSAV": {"name": "Savannah", "city": "Savannah", "lat": 32.0809, "lng": -81.0912, "type": "seaport"},
        "USHOU": {"name": "Houston", "city": "Houston", "lat": 29.7604, "lng": -95.3698, "type": "seaport"},
        "USSEA": {"name": "Seattle", "city": "Seattle", "lat": 47.6062, "lng": -122.3321, "type": "seaport"},
        "USJFK": {"name": "JFK Airport", "city": "New York", "lat": 40.6413, "lng": -73.7781, "type": "airport"},
        "USLAX_AIR": {"name": "LAX Airport", "city": "Los Angeles", "lat": 33.9416, "lng": -118.4085, "type": "airport"},
        "USORD": {"name": "O'Hare Airport", "city": "Chicago", "lat": 41.9742, "lng": -87.9073, "type": "airport"},
    }
    
    @classmethod
    def get_port(cls, code: str) -> Optional[Dict]:
        """Get port information by code"""
        all_ports = {**cls.INDIAN_PORTS, **cls.US_PORTS}
        port = all_ports.get(code)
        if port:
            return {**port, "code": code}
        return None
    
    @classmethod
    def get_all_ports(cls) -> Dict:
        """Get all ports"""
        return {**cls.INDIAN_PORTS, **cls.US_PORTS}


class ShipmentEstimator:
    """
    Estimate shipment transit times and costs
    """
    
    # Average transit times (in days) from India to US
    TRANSIT_TIMES = {
        ("INNSA", "USLAX"): {"sea": 25, "air": 2},  # Mumbai to LA
        ("INNSA", "USNYC"): {"sea": 30, "air": 2},  # Mumbai to NY
        ("INCHE", "USLAX"): {"sea": 28, "air": 2},  # Chennai to LA
        ("INCHE", "USNYC"): {"sea": 32, "air": 2},  # Chennai to NY
    }
    
    @classmethod
    def estimate_transit_time(cls, origin: str, destination: str, mode: str) -> int:
        """
        Estimate transit time in days
        """
        key = (origin, destination)
        if key in cls.TRANSIT_TIMES:
            return cls.TRANSIT_TIMES[key].get(mode, 30)
        
        # Default estimates
        if mode == "air":
            return 2
        elif mode == "sea":
            return 28
        else:
            return 7
    
    @classmethod
    def calculate_eta(cls, departure_date: datetime, origin: str, destination: str, mode: str) -> datetime:
        """
        Calculate estimated arrival date
        """
        days = cls.estimate_transit_time(origin, destination, mode)
        return departure_date + timedelta(days=days)


class TrackingService:
    """
    Main tracking service that coordinates all trackers
    """
    
    def __init__(self):
        self.vessel_tracker = VesselTracker()
        self.flight_tracker = FlightTracker()
    
    async def track_shipment(self, shipment_data: Dict) -> Dict:
        """
        Track shipment and return current status
        """
        mode = shipment_data.get("transport_mode")
        
        if mode == "sea":
            imo = shipment_data.get("vessel_imo")
            if imo:
                position = await self.vessel_tracker.get_vessel_position(imo)
                return position or {}
        
        elif mode == "air":
            flight = shipment_data.get("flight_number")
            if flight:
                position = await self.flight_tracker.get_flight_position(flight)
                return position or {}
        
        return {}
    
    async def batch_track_shipments(self, shipments: List[Dict]) -> List[Dict]:
        """
        Track multiple shipments in parallel
        """
        tasks = [self.track_shipment(s) for s in shipments]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r if not isinstance(r, Exception) else {} for r in results]


# Test data generator
def generate_test_shipment_india_to_us(mode: str = "sea") -> Dict:
    """
    Generate test shipment data from India to US
    """
    if mode == "sea":
        return {
            "tracking_number": "TEST-SEA-001",
            "bill_of_lading": "MAEU123456789",
            "transport_mode": "sea",
            "carrier_name": "Maersk Line",
            "vessel_name": "MSC GULSUN",
            "vessel_imo": "9811000",  # Real vessel IMO
            "origin_country": "India",
            "origin_port": "INNSA",
            "origin_city": "Mumbai",
            "destination_country": "United States",
            "destination_port": "USLAX",
            "destination_city": "Los Angeles",
            "container_number": "MSCU1234567",
            "container_type": "40ft HC",
            "cargo_description": "Electronics and Textiles",
            "weight_kg": 18000,
            "volume_m3": 67.7,
            "commodity_type": "General Cargo",
            "status": "in_transit",
            "booking_date": datetime.utcnow() - timedelta(days=5),
            "departure_date": datetime.utcnow() - timedelta(days=3),
            "estimated_arrival": datetime.utcnow() + timedelta(days=22),
        }
    else:  # air
        return {
            "tracking_number": "TEST-AIR-001",
            "airway_bill": "176-12345678",
            "transport_mode": "air",
            "carrier_name": "Air India Cargo",
            "flight_number": "AI173",
            "origin_country": "India",
            "origin_port": "INDEL",
            "origin_city": "Delhi",
            "destination_country": "United States",
            "destination_port": "USJFK",
            "destination_city": "New York",
            "cargo_description": "Pharmaceuticals",
            "weight_kg": 500,
            "volume_m3": 2.5,
            "commodity_type": "High Value",
            "status": "in_transit",
            "is_temperature_controlled": True,
            "target_temperature_c": 5,
            "booking_date": datetime.utcnow() - timedelta(hours=12),
            "departure_date": datetime.utcnow() - timedelta(hours=6),
            "estimated_arrival": datetime.utcnow() + timedelta(hours=18),
        }
