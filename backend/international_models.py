"""
International Shipment Tracking Models
Support for Sea (Ocean) and Air cargo tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from geoalchemy2 import Geometry
import enum

from models import Base


class TransportMode(str, enum.Enum):
    """Transport mode enumeration"""
    ROAD = "road"
    SEA = "sea"
    AIR = "air"
    RAIL = "rail"


class ShipmentStatus(str, enum.Enum):
    """Shipment status enumeration"""
    BOOKED = "booked"
    IN_TRANSIT = "in_transit"
    AT_PORT = "at_port"
    CUSTOMS_CLEARANCE = "customs_clearance"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class InternationalShipment(Base):
    """International shipment tracking (sea and air)"""
    __tablename__ = "international_shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Shipment identification
    tracking_number = Column(String(100), unique=True, nullable=False, index=True)
    bill_of_lading = Column(String(100), nullable=True)  # For sea freight
    airway_bill = Column(String(100), nullable=True)  # For air freight
    
    # Transport details
    transport_mode = Column(Enum(TransportMode), nullable=False)
    carrier_name = Column(String(255), nullable=True)
    vessel_name = Column(String(255), nullable=True)  # For sea
    vessel_imo = Column(String(20), nullable=True)  # IMO number for vessel tracking
    flight_number = Column(String(50), nullable=True)  # For air
    
    # Origin and destination
    origin_country = Column(String(100), nullable=False)
    origin_port = Column(String(255), nullable=True)
    origin_city = Column(String(255), nullable=True)
    
    destination_country = Column(String(100), nullable=False)
    destination_port = Column(String(255), nullable=True)
    destination_city = Column(String(255), nullable=True)
    
    # Cargo details
    container_number = Column(String(50), nullable=True)
    container_type = Column(String(50), nullable=True)  # 20ft, 40ft, etc.
    cargo_description = Column(Text, nullable=True)
    weight_kg = Column(Float, nullable=True)
    volume_m3 = Column(Float, nullable=True)
    commodity_type = Column(String(100), nullable=True)
    
    # Status
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.BOOKED)
    current_location = Column(String(500), nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    current_location_point = Column(Geometry('POINT'), nullable=True)
    
    # Timeline
    booking_date = Column(DateTime, nullable=True)
    departure_date = Column(DateTime, nullable=True)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    
    # Customs
    customs_status = Column(String(100), nullable=True)
    customs_clearance_date = Column(DateTime, nullable=True)
    
    # Temperature control (for reefer containers)
    is_temperature_controlled = Column(Boolean, default=False)
    target_temperature_c = Column(Float, nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")
    legs = relationship("ShipmentLeg", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentEvent(Base):
    """Track events in shipment journey"""
    __tablename__ = "shipment_events"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("international_shipments.id"), nullable=False)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # departed, arrived, customs, etc.
    event_description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    
    # Vessel/flight position at event time
    vessel_position = Column(JSON, nullable=True)
    
    # Timestamp
    occurred_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    shipment = relationship("InternationalShipment", back_populates="events")


class ShipmentLeg(Base):
    """Multi-modal shipment legs (e.g., truck -> sea -> truck)"""
    __tablename__ = "shipment_legs"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("international_shipments.id"), nullable=False)
    
    # Leg details
    leg_number = Column(Integer, nullable=False)  # Sequence
    transport_mode = Column(Enum(TransportMode), nullable=False)
    
    # Origin and destination for this leg
    origin_location = Column(String(500), nullable=True)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    
    destination_location = Column(String(500), nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    
    # Carrier for this leg
    carrier_name = Column(String(255), nullable=True)
    vessel_name = Column(String(255), nullable=True)
    flight_number = Column(String(50), nullable=True)
    
    # Timeline
    departure_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    
    # Distance
    distance_km = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    shipment = relationship("InternationalShipment", back_populates="legs")


class Port(Base):
    """Ports and airports database"""
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Port identification
    code = Column(String(10), unique=True, nullable=False, index=True)  # UN/LOCODE
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # seaport, airport, inland_port
    
    # Location
    country = Column(String(100), nullable=False)
    city = Column(String(255), nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=True)
    
    # Additional info
    timezone = Column(String(50), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class VesselPosition(Base):
    """Real-time vessel positions (AIS data)"""
    __tablename__ = "vessel_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Vessel identification
    imo_number = Column(String(20), nullable=True, index=True)
    mmsi = Column(String(20), nullable=True, index=True)  # Maritime Mobile Service Identity
    vessel_name = Column(String(255), nullable=True)
    
    # Position
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    location = Column(Geometry('POINT'), nullable=True)
    
    # Movement
    speed_knots = Column(Float, nullable=True)
    course = Column(Float, nullable=True)  # Heading in degrees
    
    # Status
    status = Column(String(100), nullable=True)  # underway, at anchor, moored, etc.
    destination = Column(String(255), nullable=True)
    eta = Column(DateTime, nullable=True)
    
    # Position timestamp
    position_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Data source
    source = Column(String(50), nullable=True)  # ais, api, manual
    
    # Created timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class FlightPosition(Base):
    """Real-time flight positions"""
    __tablename__ = "flight_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Flight identification
    flight_number = Column(String(50), nullable=False, index=True)
    airline = Column(String(100), nullable=True)
    aircraft_type = Column(String(50), nullable=True)
    
    # Position
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    altitude_ft = Column(Float, nullable=True)
    location = Column(Geometry('POINT'), nullable=True)
    
    # Movement
    speed_knots = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    
    # Origin and destination
    origin_airport = Column(String(10), nullable=True)
    destination_airport = Column(String(10), nullable=True)
    
    # Status
    status = Column(String(50), nullable=True)  # scheduled, active, landed
    
    # Position timestamp
    position_timestamp = Column(DateTime, nullable=False, index=True)
    
    # Data source
    source = Column(String(50), nullable=True)
    
    # Created timestamp
    created_at = Column(DateTime, default=datetime.utcnow)


class CustomsClearance(Base):
    """Customs clearance tracking"""
    __tablename__ = "customs_clearance"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("international_shipments.id"), nullable=False)
    
    # Customs details
    entry_number = Column(String(100), nullable=True)
    customs_office = Column(String(255), nullable=True)
    clearance_type = Column(String(50), nullable=True)  # import, export, transit
    
    # Status
    status = Column(String(100), nullable=False)  # submitted, under_review, cleared, held
    
    # Documents
    documents_submitted = Column(JSON, nullable=True)
    
    # Duties and taxes
    duties_amount = Column(Float, nullable=True)
    taxes_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    
    # Timeline
    submitted_date = Column(DateTime, nullable=True)
    cleared_date = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
