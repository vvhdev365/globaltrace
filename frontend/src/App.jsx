import React, { useState, useEffect } from 'react';
import Map, { Marker, Source, Layer, NavigationControl } from 'react-map-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapPin, Navigation, Package, Users, TrendingUp } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [routes, setRoutes] = useState([]);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [optimizing, setOptimizing] = useState(false);
  const [viewport, setViewport] = useState({
    longitude: -122.4194,
    latitude: 37.7749,
    zoom: 12
  });

  // Stats
  const [stats, setStats] = useState({
    totalRoutes: 0,
    activeDrivers: 0,
    completedDeliveries: 0,
    avgDeliveryTime: 0
  });

  // Fetch routes
  useEffect(() => {
    fetchRoutes();
    fetchStats();
  }, []);

  const fetchRoutes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/routes`);
      const data = await response.json();
      setRoutes(data.routes || []);
    } catch (error) {
      console.error('Error fetching routes:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/analytics/summary`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const optimizeRoute = async (stops) => {
    setOptimizing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/routes/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          stops: stops,
          num_vehicles: 1
        })
      });
      const data = await response.json();
      console.log('Optimized route:', data);
      return data;
    } catch (error) {
      console.error('Error optimizing route:', error);
    } finally {
      setOptimizing(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white shadow-lg overflow-y-auto">
        {/* Header */}
        <div className="p-6 bg-gradient-to-r from-blue-600 to-blue-700">
          <h1 className="text-2xl font-bold text-white">Logistics Platform</h1>
          <p className="text-blue-100 text-sm mt-1">Zero-Cost Route Optimization</p>
        </div>

        {/* Stats Grid */}
        <div className="p-4 grid grid-cols-2 gap-3">
          <StatCard 
            icon={<Package className="w-5 h-5" />}
            label="Routes"
            value={stats.totalRoutes}
            color="blue"
          />
          <StatCard 
            icon={<Users className="w-5 h-5" />}
            label="Drivers"
            value={stats.activeDrivers}
            color="green"
          />
          <StatCard 
            icon={<TrendingUp className="w-5 h-5" />}
            label="Deliveries"
            value={stats.completedDeliveries}
            color="purple"
          />
          <StatCard 
            icon={<Navigation className="w-5 h-5" />}
            label="Avg Time"
            value={`${stats.avgDeliveryTime}m`}
            color="orange"
          />
        </div>

        {/* Routes List */}
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-3 flex items-center">
            <Navigation className="w-5 h-5 mr-2" />
            Active Routes
          </h2>
          
          {routes.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No routes yet</p>
              <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                Create First Route
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {routes.map((route) => (
                <RouteCard 
                  key={route.id}
                  route={route}
                  onClick={() => setSelectedRoute(route)}
                  isSelected={selectedRoute?.id === route.id}
                />
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="p-4 border-t">
          <h3 className="font-semibold mb-3">Quick Actions</h3>
          <div className="space-y-2">
            <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
              + New Route
            </button>
            <button className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
              Import Stops
            </button>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 relative">
        <Map
          {...viewport}
          onMove={evt => setViewport(evt.viewState)}
          style={{width: '100%', height: '100%'}}
          mapStyle="https://demotiles.maplibre.org/style.json"  // Free basemap!
        >
          <NavigationControl position="top-right" />
          
          {/* Sample markers */}
          <Marker longitude={-122.4194} latitude={37.7749}>
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shadow-lg">
              <MapPin className="w-5 h-5 text-white" />
            </div>
          </Marker>
        </Map>

        {/* Floating Controls */}
        {selectedRoute && (
          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-md">
            <h3 className="font-semibold mb-2">{selectedRoute.name}</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p>Status: <span className="font-medium text-green-600">{selectedRoute.status}</span></p>
              <p>Stops: {selectedRoute.stops?.length || 0}</p>
              <p>Distance: {(selectedRoute.total_distance_meters / 1000).toFixed(1)} km</p>
            </div>
            <button 
              onClick={() => optimizeRoute(selectedRoute.stops)}
              disabled={optimizing}
              className="mt-3 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
            >
              {optimizing ? 'Optimizing...' : 'Re-optimize Route'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ icon, label, value, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600'
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className={`w-8 h-8 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-2`}>
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

// Route Card Component
function RouteCard({ route, onClick, isSelected }) {
  return (
    <div 
      onClick={onClick}
      className={`p-3 rounded-lg border-2 cursor-pointer transition ${
        isSelected 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-200 hover:border-gray-300 bg-white'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-sm">{route.name}</h4>
          <div className="text-xs text-gray-500 mt-1">
            {route.stops?.length || 0} stops • {(route.total_distance_meters / 1000).toFixed(1)} km
          </div>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${
          route.status === 'active' ? 'bg-green-100 text-green-700' :
          route.status === 'completed' ? 'bg-gray-100 text-gray-700' :
          'bg-blue-100 text-blue-700'
        }`}>
          {route.status}
        </span>
      </div>
    </div>
  );
}

export default App;
