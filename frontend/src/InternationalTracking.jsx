import React, { useState, useEffect } from 'react';
import Map, { Marker, Source, Layer, Popup } from 'react-map-gl';
import { Ship, Plane, Package, MapPin, Clock, TrendingUp, AlertCircle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Port locations
const PORTS = {
  INNSA: { name: "Mumbai (JNPT)", lat: 18.9484, lng: 72.9491, country: "India" },
  INCHE: { name: "Chennai Port", lat: 13.0827, lng: 80.2707, country: "India" },
  INDEL: { name: "Delhi Airport", lat: 28.5562, lng: 77.1000, country: "India" },
  USLAX: { name: "Los Angeles", lat: 33.7366, lng: -118.2725, country: "USA" },
  USNYC: { name: "New York", lat: 40.6653, lng: -74.0806, country: "USA" },
  USJFK: { name: "JFK Airport", lat: 40.6413, lng: -73.7781, country: "USA" },
};

function InternationalTracking() {
  const [shipments, setShipments] = useState([]);
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [showPopup, setShowPopup] = useState(null);
  const [viewport, setViewport] = useState({
    longitude: 30,  // Center between India and US
    latitude: 30,
    zoom: 2
  });

  useEffect(() => {
    loadTestShipments();
    // Refresh tracking data every 30 seconds
    const interval = setInterval(loadTestShipments, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadTestShipments = async () => {
    try {
      // Generate test shipments
      const response = await fetch(`${API_BASE_URL}/api/international/test/generate-shipments`, {
        method: 'POST'
      });
      const data = await response.json();
      setShipments(data.shipments || []);
    } catch (error) {
      console.error('Error loading shipments:', error);
    }
  };

  const getShipmentDetails = async (trackingNumber) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/international/shipments/${trackingNumber}`);
      const data = await response.json();
      setSelectedShipment(data);
    } catch (error) {
      console.error('Error fetching shipment:', error);
    }
  };

  // Generate route line between two ports
  const generateRouteLine = (origin, destination) => {
    const originPort = PORTS[origin];
    const destPort = PORTS[destination];
    
    if (!originPort || !destPort) return null;

    // Create a curved line (great circle route approximation)
    const points = [];
    const steps = 50;
    
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      // Simple linear interpolation (for demo - use great circle in production)
      const lat = originPort.lat + (destPort.lat - originPort.lat) * t;
      const lng = originPort.lng + (destPort.lng - originPort.lng) * t;
      
      // Add some curve for visual effect
      const curve = Math.sin(t * Math.PI) * 10;
      points.push([lng, lat + curve]);
    }

    return {
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: points
      }
    };
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_transit':
      case 'in_flight':
        return 'text-blue-600 bg-blue-50';
      case 'at_port':
        return 'text-orange-600 bg-orange-50';
      case 'customs_clearance':
        return 'text-purple-600 bg-purple-50';
      case 'delivered':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getModeIcon = (mode) => {
    switch (mode) {
      case 'sea':
        return <Ship className="w-5 h-5" />;
      case 'air':
        return <Plane className="w-5 h-5" />;
      default:
        return <Package className="w-5 h-5" />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-96 bg-white shadow-lg overflow-y-auto">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-indigo-600 to-blue-600">
          <h1 className="text-2xl font-bold text-white">International Tracking</h1>
          <p className="text-blue-100 text-sm mt-1">India → United States</p>
        </div>

        {/* Stats */}
        <div className="p-4 grid grid-cols-2 gap-3 border-b">
          <StatCard 
            icon={<Ship className="w-5 h-5" />}
            label="Sea Freight"
            value={shipments.filter(s => s.mode === 'sea').length}
            color="blue"
          />
          <StatCard 
            icon={<Plane className="w-5 h-5" />}
            label="Air Freight"
            value={shipments.filter(s => s.mode === 'air').length}
            color="purple"
          />
        </div>

        {/* Shipments List */}
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-3 flex items-center">
            <Package className="w-5 h-5 mr-2" />
            Active Shipments
          </h2>

          {shipments.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Loading shipments...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {shipments.map((shipment) => (
                <ShipmentCard
                  key={shipment.tracking_number}
                  shipment={shipment}
                  isSelected={selectedShipment?.tracking_number === shipment.tracking_number}
                  onClick={() => {
                    getShipmentDetails(shipment.tracking_number);
                    // Parse origin and destination codes
                    const originMatch = shipment.origin.match(/\(([^)]+)\)/);
                    const destMatch = shipment.destination.match(/\(([^)]+)\)/);
                    if (originMatch && destMatch) {
                      const origin = PORTS[originMatch[1]];
                      const dest = PORTS[destMatch[1]];
                      if (origin && dest) {
                        setViewport({
                          longitude: (origin.lng + dest.lng) / 2,
                          latitude: (origin.lat + dest.lat) / 2,
                          zoom: 3
                        });
                      }
                    }
                  }}
                  getStatusColor={getStatusColor}
                  getModeIcon={getModeIcon}
                />
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="p-4 border-t mt-4">
          <button 
            onClick={loadTestShipments}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Refresh Tracking
          </button>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <Map
          {...viewport}
          onMove={evt => setViewport(evt.viewState)}
          style={{width: '100%', height: '100%'}}
          mapStyle="https://demotiles.maplibre.org/style.json"
        >
          {/* Draw routes */}
          {shipments.map((shipment) => {
            const originMatch = shipment.origin.match(/\(([^)]+)\)/);
            const destMatch = shipment.destination.match(/\(([^)]+)\)/);
            
            if (originMatch && destMatch) {
              const routeLine = generateRouteLine(originMatch[1], destMatch[1]);
              
              if (routeLine) {
                return (
                  <Source
                    key={`route-${shipment.tracking_number}`}
                    type="geojson"
                    data={routeLine}
                  >
                    <Layer
                      type="line"
                      paint={{
                        'line-color': shipment.mode === 'sea' ? '#3B82F6' : '#8B5CF6',
                        'line-width': 2,
                        'line-dasharray': [2, 2]
                      }}
                    />
                  </Source>
                );
              }
            }
            return null;
          })}

          {/* Port markers */}
          {Object.entries(PORTS).map(([code, port]) => (
            <Marker
              key={code}
              longitude={port.lng}
              latitude={port.lat}
              anchor="center"
              onClick={e => {
                e.originalEvent.stopPropagation();
                setShowPopup(code);
              }}
            >
              <div className="relative group cursor-pointer">
                <div className="w-3 h-3 bg-red-500 rounded-full border-2 border-white shadow-lg" />
                <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                  <div className="bg-gray-900 text-white text-xs px-2 py-1 rounded">
                    {port.name}
                  </div>
                </div>
              </div>
            </Marker>
          ))}

          {/* Popup */}
          {showPopup && PORTS[showPopup] && (
            <Popup
              longitude={PORTS[showPopup].lng}
              latitude={PORTS[showPopup].lat}
              anchor="bottom"
              onClose={() => setShowPopup(null)}
            >
              <div className="p-2">
                <div className="font-semibold">{PORTS[showPopup].name}</div>
                <div className="text-xs text-gray-500">{PORTS[showPopup].country}</div>
                <div className="text-xs text-gray-400 mt-1">Code: {showPopup}</div>
              </div>
            </Popup>
          )}
        </Map>

        {/* Selected Shipment Details */}
        {selectedShipment && (
          <div className="absolute top-4 right-4 bg-white rounded-lg shadow-xl p-4 max-w-sm">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center">
                {getModeIcon(selectedShipment.transport_mode)}
                <span className="ml-2 font-semibold">{selectedShipment.tracking_number}</span>
              </div>
              <button 
                onClick={() => setSelectedShipment(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500">Route:</span>
                <div className="font-medium">{selectedShipment.origin_city} → {selectedShipment.destination_city}</div>
              </div>
              
              <div>
                <span className="text-gray-500">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs ${getStatusColor(selectedShipment.status)}`}>
                  {selectedShipment.status?.replace('_', ' ').toUpperCase()}
                </span>
              </div>

              {selectedShipment.vessel_name && (
                <div>
                  <span className="text-gray-500">Vessel:</span>
                  <div className="font-medium">{selectedShipment.vessel_name}</div>
                </div>
              )}

              {selectedShipment.flight_number && (
                <div>
                  <span className="text-gray-500">Flight:</span>
                  <div className="font-medium">{selectedShipment.flight_number}</div>
                </div>
              )}

              <div>
                <span className="text-gray-500">Cargo:</span>
                <div className="font-medium">{selectedShipment.cargo_description}</div>
                <div className="text-xs text-gray-400">{selectedShipment.weight_kg?.toLocaleString()} kg</div>
              </div>

              {selectedShipment.estimated_arrival && (
                <div>
                  <span className="text-gray-500">ETA:</span>
                  <div className="font-medium">{new Date(selectedShipment.estimated_arrival).toLocaleDateString()}</div>
                </div>
              )}
            </div>

            <button 
              className="mt-4 w-full px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 transition"
              onClick={() => window.open(`${API_BASE_URL}/api/international/shipments/${selectedShipment.tracking_number}/events`, '_blank')}
            >
              View Full Timeline
            </button>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 text-xs">
          <div className="font-semibold mb-2">Legend</div>
          <div className="space-y-1">
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-red-500 mr-2" />
              <span>Ports/Airports</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-0.5 bg-blue-500 border-dashed mr-2" />
              <span>Sea Route</span>
            </div>
            <div className="flex items-center">
              <div className="w-6 h-0.5 bg-purple-500 border-dashed mr-2" />
              <span>Air Route</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon, label, value, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className={`w-8 h-8 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-2`}>
        {icon}
      </div>
      <div className="text-xl font-bold">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

// Shipment Card Component
function ShipmentCard({ shipment, isSelected, onClick, getStatusColor, getModeIcon }) {
  return (
    <div 
      onClick={onClick}
      className={`p-3 rounded-lg border-2 cursor-pointer transition ${
        isSelected 
          ? 'border-indigo-500 bg-indigo-50' 
          : 'border-gray-200 hover:border-gray-300 bg-white'
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <div className="mr-2">
            {getModeIcon(shipment.mode)}
          </div>
          <div>
            <div className="font-medium text-sm">{shipment.tracking_number}</div>
            <div className="text-xs text-gray-500">{shipment.mode.toUpperCase()}</div>
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${getStatusColor(shipment.status)}`}>
          {shipment.status?.replace('_', ' ')}
        </span>
      </div>

      <div className="text-xs text-gray-600 space-y-1">
        <div className="flex items-center">
          <MapPin className="w-3 h-3 mr-1" />
          {shipment.origin} → {shipment.destination}
        </div>
        <div className="flex items-center">
          <Package className="w-3 h-3 mr-1" />
          {shipment.cargo}
        </div>
      </div>
    </div>
  );
}

export default InternationalTracking;
