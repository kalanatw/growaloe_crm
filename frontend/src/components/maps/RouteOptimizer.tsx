import React, { useState } from 'react';
import { GoogleMap, DirectionsRenderer, Marker, useJsApiLoader } from '@react-google-maps/api';
import { Shop } from '../../types';
import { Route, MapPin, Clock, Navigation, AlertCircle } from 'lucide-react';
import { GOOGLE_MAPS_CONFIG } from '../../utils/googleMapsLoader';

interface RouteOptimizerProps {
  shops: Shop[];
  startLocation?: { lat: number; lng: number; name?: string };
  onRouteCalculated?: (route: google.maps.DirectionsResult) => void;
}

const mapContainerStyle = {
  width: '100%',
  height: '500px'
};

const defaultCenter = {
  lat: 7.8731, // Sri Lanka center
  lng: 80.7718
};

export const RouteOptimizer: React.FC<RouteOptimizerProps> = ({ 
  shops, 
  startLocation,
  onRouteCalculated 
}) => {
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null);
  const [selectedShops, setSelectedShops] = useState<number[]>([]);
  const [isCalculating, setIsCalculating] = useState(false);
  const [routeInfo, setRouteInfo] = useState<{
    distance: string;
    duration: string;
    optimizedOrder: number[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { isLoaded, loadError } = useJsApiLoader(GOOGLE_MAPS_CONFIG);

  const validShops = shops.filter(shop => 
    shop.latitude && shop.longitude && 
    !isNaN(shop.latitude) && !isNaN(shop.longitude)
  );

  const calculateRoute = async () => {
    if (selectedShops.length === 0) {
      setError('Please select at least one shop');
      return;
    }

    if (!startLocation) {
      setError('Start location is required');
      return;
    }

    setIsCalculating(true);
    setError(null);

    const directionsService = new google.maps.DirectionsService();
    const selectedShopData = validShops.filter(shop => selectedShops.includes(shop.id));
    
    const waypoints = selectedShopData.map(shop => ({
      location: { lat: shop.latitude!, lng: shop.longitude! },
      stopover: true
    }));

    try {
      const result = await directionsService.route({
        origin: startLocation,
        destination: startLocation, // Return to start
        waypoints,
        optimizeWaypoints: true,
        travelMode: google.maps.TravelMode.DRIVING,
        unitSystem: google.maps.UnitSystem.METRIC,
        avoidHighways: false,
        avoidTolls: false
      });
      
      setDirections(result);
      onRouteCalculated?.(result);

      // Extract route information
      const route = result.routes[0];
      if (route) {
        setRouteInfo({
          distance: route.legs.reduce((total, leg) => total + leg.distance!.value, 0) / 1000 + ' km',
          duration: route.legs.reduce((total, leg) => total + leg.duration!.value, 0) / 60 + ' min',
          optimizedOrder: result.routes[0].waypoint_order || []
        });
      }
    } catch (error) {
      console.error('Route calculation failed:', error);
      setError('Failed to calculate route. Please try again.');
    } finally {
      setIsCalculating(false);
    }
  };

  const toggleShopSelection = (shopId: number) => {
    setSelectedShops(prev => 
      prev.includes(shopId) 
        ? prev.filter(id => id !== shopId)
        : [...prev, shopId]
    );
  };

  const selectAllShops = () => {
    setSelectedShops(validShops.map(shop => shop.id));
  };

  const clearSelection = () => {
    setSelectedShops([]);
    setDirections(null);
    setRouteInfo(null);
    setError(null);
  };

  if (loadError) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
        <div className="text-center">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">Failed to load map</p>
          <p className="text-sm text-gray-500">Please check your Google Maps API key</p>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg animate-pulse">
        <div className="text-center">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">Loading route optimizer...</p>
        </div>
      </div>
    );
  }

  const mapCenter = startLocation || (validShops.length > 0 
    ? {
        lat: validShops.reduce((sum, shop) => sum + shop.latitude!, 0) / validShops.length,
        lng: validShops.reduce((sum, shop) => sum + shop.longitude!, 0) / validShops.length
      }
    : defaultCenter);

  return (
    <div className="space-y-6">
      {/* Shop Selection */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Select Shops for Route</h3>
          <div className="space-x-2">
            <button
              onClick={selectAllShops}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Select All
            </button>
            <button
              onClick={clearSelection}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Clear All
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-60 overflow-y-auto">
          {validShops.map((shop) => (
            <label
              key={shop.id}
              className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedShops.includes(shop.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedShops.includes(shop.id)}
                onChange={() => toggleShopSelection(shop.id)}
                className="mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {shop.name}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {shop.address}
                </p>
              </div>
            </label>
          ))}
        </div>

        {validShops.length === 0 && (
          <div className="text-center py-8">
            <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No shops with location data available</p>
          </div>
        )}
      </div>

      {/* Route Controls */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600">
          {selectedShops.length} shop{selectedShops.length !== 1 ? 's' : ''} selected
        </div>
        <button
          onClick={calculateRoute}
          disabled={isCalculating || selectedShops.length === 0 || !startLocation}
          className="btn btn-primary flex items-center space-x-2"
        >
          {isCalculating ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Route className="w-4 h-4" />
          )}
          <span>Calculate Optimized Route</span>
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="text-red-800 font-medium">Error</span>
          </div>
          <p className="text-red-700 mt-1">{error}</p>
        </div>
      )}

      {/* Route Information */}
      {routeInfo && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <Navigation className="w-5 h-5 text-green-600" />
            <span className="text-green-800 font-medium">Route Calculated</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-green-600" />
              <span className="text-green-700">Distance: {routeInfo.distance}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-green-600" />
              <span className="text-green-700">Duration: {routeInfo.duration}</span>
            </div>
          </div>
        </div>
      )}

      {/* Map */}
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <GoogleMap
          mapContainerStyle={mapContainerStyle}
          center={mapCenter}
          zoom={10}
          options={{
            zoomControl: true,
            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: true,
          }}
        >
          {/* Start Location Marker */}
          {startLocation && (
            <Marker
              position={startLocation}
              title={startLocation.name || 'Start Location'}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="12" fill="#10B981" stroke="#059669" stroke-width="2"/>
                    <circle cx="16" cy="16" r="4" fill="white"/>
                  </svg>
                `),
                scaledSize: new window.google.maps.Size(32, 32),
                anchor: new window.google.maps.Point(16, 16)
              }}
            />
          )}

          {/* Shop Markers */}
          {validShops.map((shop) => (
            <Marker
              key={shop.id}
              position={{ lat: shop.latitude!, lng: shop.longitude! }}
              title={shop.name}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="12" fill="${selectedShops.includes(shop.id) ? '#3B82F6' : '#6B7280'}" stroke="${selectedShops.includes(shop.id) ? '#1E40AF' : '#4B5563'}" stroke-width="2"/>
                    <circle cx="16" cy="16" r="4" fill="white"/>
                  </svg>
                `),
                scaledSize: new window.google.maps.Size(32, 32),
                anchor: new window.google.maps.Point(16, 16)
              }}
            />
          ))}

          {/* Route Display */}
          {directions && (
            <DirectionsRenderer
              directions={directions}
              options={{
                suppressMarkers: true, // We're using custom markers
                polylineOptions: {
                  strokeColor: '#3B82F6',
                  strokeWeight: 4,
                  strokeOpacity: 0.8
                }
              }}
            />
          )}
        </GoogleMap>
      </div>
    </div>
  );
};