"""
Database Models for Logistics Platform
Using SQLAlchemy with PostGIS for geospatial data
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from geoalchemy2 import Geometry

Base = declarative_base()


class Route(Base):
    """Route model - represents a delivery route"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="draft")  # draft, active, completed, cancelled
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Route statistics
    total_distance_meters = Column(Float, default=0)
    estimated_duration_minutes = Column(Integer, default=0)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Optimization metadata
    optimization_data = Column(JSON, nullable=True)
    
    # Relationships
    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan")
    vehicle = relationship("Vehicle", back_populates="routes")
    driver = relationship("Driver", back_populates="routes")


class Stop(Base):
    """Stop model - represents a delivery stop on a route"""
    __tablename__ = "stops"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    
    # Location data
    address = Column(String(500), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=True)  # PostGIS point
    
    # Stop details
    sequence = Column(Integer, nullable=False)  # Order in route
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Package details
    package_count = Column(Integer, default=1)
    weight_kg = Column(Float, nullable=True)
    
    # Time windows
    time_window_start = Column(DateTime, nullable=True)
    time_window_end = Column(DateTime, nullable=True)
    
    # Estimated vs actual
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    estimated_service_time_minutes = Column(Integer, default=5)
    actual_service_time_minutes = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, arrived, completed, failed
    completion_notes = Column(Text, nullable=True)
    proof_of_delivery = Column(String(500), nullable=True)  # URL to image/signature
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    route = relationship("Route", back_populates="stops")


class Driver(Base):
    """Driver model"""
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal info
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Driver details
    license_number = Column(String(100), nullable=True)
    license_expiry = Column(DateTime, nullable=True)
    
    # Current location (updated in real-time)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    current_location = Column(Geometry('POINT'), nullable=True)
    last_location_update = Column(DateTime, nullable=True)
    
    # Performance metrics
    total_deliveries = Column(Integer, default=0)
    success_rate = Column(Float, default=0)
    avg_rating = Column(Float, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    routes = relationship("Route", back_populates="driver")
    vehicle = relationship("Vehicle", back_populates="driver", uselist=False)


class Vehicle(Base):
    """Vehicle model"""
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    # Vehicle details
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=True)
    license_plate = Column(String(50), unique=True, nullable=False)
    vin = Column(String(100), nullable=True)
    
    # Capacity
    max_weight_kg = Column(Float, nullable=True)
    max_volume_m3 = Column(Float, nullable=True)
    max_packages = Column(Integer, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    current_odometer_km = Column(Float, default=0)
    
    # Maintenance
    last_maintenance_date = Column(DateTime, nullable=True)
    next_maintenance_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver = relationship("Driver", back_populates="vehicle")
    routes = relationship("Route", back_populates="vehicle")


class LocationHistory(Base):
    """Track historical locations for analytics"""
    __tablename__ = "location_history"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    
    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=True)
    
    # Additional data
    speed_kmh = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)  # Compass direction
    accuracy_meters = Column(Float, nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class DeliveryEvent(Base):
    """Track events during delivery"""
    __tablename__ = "delivery_events"
    
    id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # arrived, departed, delivered, failed, etc.
    event_data = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Location at event time
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Timestamp
    occurred_at = Column(DateTime, default=datetime.utcnow, index=True)


class Organization(Base):
    """Multi-tenant support - different companies can use the platform"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    # Contact
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Settings
    settings = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
