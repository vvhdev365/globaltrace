"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


# ============= STOP SCHEMAS =============

class StopBase(BaseModel):
    address: str
    lat: float
    lng: float
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None
    package_count: int = 1
    weight_kg: Optional[float] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None


class StopCreate(StopBase):
    sequence: int


class StopUpdate(BaseModel):
    status: Optional[str] = None
    actual_arrival: Optional[datetime] = None
    actual_service_time_minutes: Optional[int] = None
    completion_notes: Optional[str] = None
    proof_of_delivery: Optional[str] = None


class StopResponse(StopBase):
    id: int
    route_id: int
    sequence: int
    status: str
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= ROUTE SCHEMAS =============

class RouteBase(BaseModel):
    name: str
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None


class RouteCreate(RouteBase):
    stops: List[StopCreate] = []


class RouteUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None


class RouteResponse(RouteBase):
    id: int
    status: str
    total_distance_meters: float
    estimated_duration_minutes: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stops: List[StopResponse] = []
    
    class Config:
        from_attributes = True


# ============= OPTIMIZATION SCHEMAS =============

class StopOptimize(BaseModel):
    """Stop data for optimization"""
    lat: float
    lng: float
    address: Optional[str] = ""
    time_window_start: Optional[int] = None  # Minutes from start
    time_window_end: Optional[int] = None
    service_time: int = 5  # Minutes
    demand: Optional[int] = 1  # For capacity constraints


class RouteOptimize(BaseModel):
    """Request for route optimization"""
    stops: List[StopOptimize]
    num_vehicles: Optional[int] = 1
    depot_index: Optional[int] = 0
    vehicle_capacity: Optional[int] = None


class RouteOptimizeResponse(BaseModel):
    """Optimized route response"""
    optimized_stops: List[StopOptimize]
    sequence: List[int]
    total_distance_meters: float
    estimated_time_minutes: float


# ============= DRIVER SCHEMAS =============

class DriverBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str


class DriverCreate(DriverBase):
    password: str
    license_number: Optional[str] = None


class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class DriverResponse(DriverBase):
    id: int
    is_active: bool
    total_deliveries: int
    success_rate: float
    avg_rating: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class DriverLocationUpdate(BaseModel):
    """Real-time location update from driver app"""
    lat: float
    lng: float
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy_meters: Optional[float] = None


# ============= VEHICLE SCHEMAS =============

class VehicleBase(BaseModel):
    make: str
    model: str
    year: Optional[int] = None
    license_plate: str
    max_weight_kg: Optional[float] = None
    max_packages: Optional[int] = None


class VehicleCreate(VehicleBase):
    driver_id: Optional[int] = None


class VehicleUpdate(BaseModel):
    is_active: Optional[bool] = None
    current_odometer_km: Optional[float] = None
    driver_id: Optional[int] = None


class VehicleResponse(VehicleBase):
    id: int
    is_active: bool
    current_odometer_km: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= GEOCODING SCHEMAS =============

class GeocodeRequest(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    address: str
    lat: float
    lng: float
    place_id: Optional[str] = None


# ============= ANALYTICS SCHEMAS =============

class AnalyticsSummary(BaseModel):
    total_routes: int
    active_routes: int
    completed_routes: int
    total_drivers: int
    active_drivers: int
    total_deliveries: int
    completed_deliveries: int
    success_rate: float
    avg_delivery_time_minutes: float


class RouteMetrics(BaseModel):
    route_id: int
    route_name: str
    planned_distance_km: float
    actual_distance_km: Optional[float] = None
    planned_duration_minutes: int
    actual_duration_minutes: Optional[int] = None
    stops_count: int
    completed_stops: int
    success_rate: float
