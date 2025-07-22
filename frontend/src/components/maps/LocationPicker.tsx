import React, { useState, useCallback, useEffect } from 'react';
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
import { MapPin, Search, Navigation, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { GOOGLE_MAPS_CONFIG } from '../../utils/googleMapsLoader';

interface LocationPickerProps {
  onLocationSelect: (lat: number, lng: number, address?: string) => void;
  initialLocation?: { lat: number; lng: number };
  height?: string;
}

const mapContainerStyle = {
  width: '100%',
  height: '300px'
};

const defaultCenter = {
  lat: 7.8731, // Sri Lanka center
  lng: 80.7718
};

export const LocationPicker: React.FC<LocationPickerProps> = ({
  onLocationSelect,
  initialLocation,
  height = '300px'
}) => {
  const [selectedLocation, setSelectedLocation] = useState(() => {
    if (initialLocation) {
      const lat = typeof initialLocation.lat === 'number' ? initialLocation.lat : parseFloat(initialLocation.lat as any);
      const lng = typeof initialLocation.lng === 'number' ? initialLocation.lng : parseFloat(initialLocation.lng as any);

      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        return { lat, lng };
      }
    }
    return undefined;
  });
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [searchResults, setSearchResults] = useState<google.maps.places.PlaceResult[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  const { isLoaded, loadError } = useJsApiLoader(GOOGLE_MAPS_CONFIG);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
    };
  }, [searchTimeout]);

  const onLoad = useCallback((map: google.maps.Map) => {
    setMap(map);
  }, []);

  const onUnmount = useCallback(() => {
    setMap(null);
  }, []);

  const handleMapClick = useCallback((event: google.maps.MapMouseEvent) => {
    if (event.latLng) {
      const lat = event.latLng.lat();
      const lng = event.latLng.lng();
      setSelectedLocation({ lat, lng });

      // Reverse geocoding to get address
      const geocoder = new window.google.maps.Geocoder();
      geocoder.geocode({ location: { lat, lng } }, (results, status) => {
        if (status === 'OK' && results?.[0]) {
          onLocationSelect(lat, lng, results[0].formatted_address);
        } else {
          onLocationSelect(lat, lng);
        }
      });
    }
  }, [onLocationSelect]);

  const handleSearch = async () => {
    if (!searchQuery.trim() || !map) return;

    setIsSearching(true);
    const geocoder = new window.google.maps.Geocoder();

    try {
      geocoder.geocode({ address: searchQuery }, (results, status) => {
        setIsSearching(false);
        if (status === 'OK' && results?.[0]) {
          const location = results[0].geometry.location;
          const lat = location.lat();
          const lng = location.lng();

          setSelectedLocation({ lat, lng });
          map.setCenter({ lat, lng });
          map.setZoom(15);

          onLocationSelect(lat, lng, results[0].formatted_address);
        } else {
          console.error('Geocoding failed:', status);
        }
      });
    } catch (error) {
      setIsSearching(false);
      console.error('Search error:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchPlaces();
    }
  };

  // Real-time search as user types
  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);

    // Clear previous timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    if (value.trim() === '') {
      setShowResults(false);
      setSearchResults([]);
      return;
    }

    // Set new timeout for real-time search
    const timeout = setTimeout(() => {
      if (value.trim().length >= 3) { // Only search after 3 characters
        searchPlaces();
      }
    }, 500); // Wait 500ms after user stops typing

    setSearchTimeout(timeout);
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by this browser.');
      return;
    }

    setIsGettingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        setSelectedLocation({ lat, lng });

        if (map) {
          map.setCenter({ lat, lng });
          map.setZoom(18); // Zoom in closer for current location
        }

        // Get address for current location
        const geocoder = new window.google.maps.Geocoder();
        geocoder.geocode({ location: { lat, lng } }, (results, status) => {
          setIsGettingLocation(false);
          if (status === 'OK' && results?.[0]) {
            onLocationSelect(lat, lng, results[0].formatted_address);
            toast.success('📍 Current location set successfully!');
          } else {
            onLocationSelect(lat, lng, 'Current Location');
            toast.success('📍 Current location set!');
          }
        });
      },
      (error) => {
        setIsGettingLocation(false);
        console.error('Error getting location:', error);

        let errorMessage = 'Unable to get your location. ';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage += 'Please allow location access and try again.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage += 'Location information is unavailable.';
            break;
          case error.TIMEOUT:
            errorMessage += 'Location request timed out.';
            break;
          default:
            errorMessage += 'An unknown error occurred.';
            break;
        }
        alert(errorMessage);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  const searchPlaces = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setShowResults(false);

    try {
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

      // First try Places API Text Search using direct HTTP request
      const textSearchUrl = `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${encodeURIComponent(searchQuery)}&key=${apiKey}`;

      // Since we can't make direct CORS requests to Google Maps API from browser,
      // we'll use the JavaScript API as a fallback, but with better error handling
      if (window.google?.maps?.places && map) {
        const service = new window.google.maps.places.PlacesService(map);

        const request = {
          query: searchQuery,
          fields: ['name', 'formatted_address', 'geometry', 'place_id', 'types', 'business_status'],
        };

        service.textSearch(request, (results, status) => {
          setIsSearching(false);

          if (status === window.google.maps.places.PlacesServiceStatus.OK && results) {
            // Filter out closed businesses and prioritize active ones
            const filteredResults = results.filter(place =>
              place.business_status !== 'CLOSED_PERMANENTLY' &&
              place.geometry?.location
            );
            setSearchResults(filteredResults);
            setShowResults(true);

            if (filteredResults.length === 0) {
              toast.error('No active businesses found. Try a different search term.');
            }
          } else {
            // Fallback to geocoding using direct HTTP request
            fallbackToGeocoding();
          }
        });
      } else {
        // If JavaScript API not available, fallback to geocoding
        fallbackToGeocoding();
      }
    } catch (error) {
      console.error('Places search error:', error);
      setIsSearching(false);
      fallbackToGeocoding();
    }
  };

  const fallbackToGeocoding = async () => {
    try {
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
      const geocodeUrl = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(searchQuery)}&key=${apiKey}`;

      // We can't make direct requests due to CORS, so use the JavaScript Geocoder
      if (window.google?.maps?.Geocoder) {
        const geocoder = new window.google.maps.Geocoder();
        geocoder.geocode({ address: searchQuery }, (results, status) => {
          setIsSearching(false);
          if (status === 'OK' && results?.[0]) {
            // Convert geocoding results to place-like format
            const placeResults = results.map(result => ({
              name: result.formatted_address,
              formatted_address: result.formatted_address,
              geometry: result.geometry,
              place_id: result.place_id,
              types: result.types
            }));
            setSearchResults(placeResults as any);
            setShowResults(true);
          } else {
            toast.error('No locations found. Try a different search term.');
          }
        });
      } else {
        setIsSearching(false);
        toast.error('Search service not available. Please try again.');
      }
    } catch (error) {
      console.error('Geocoding fallback error:', error);
      setIsSearching(false);
      toast.error('Search failed. Please try again.');
    }
  };

  const selectPlace = (place: google.maps.places.PlaceResult) => {
    if (place.geometry?.location) {
      const lat = place.geometry.location.lat();
      const lng = place.geometry.location.lng();

      setSelectedLocation({ lat, lng });
      setShowResults(false);
      setSearchQuery(place.name || place.formatted_address || '');

      if (map) {
        map.setCenter({ lat, lng });
        map.setZoom(17);
      }

      onLocationSelect(lat, lng, place.formatted_address || place.name);
    }
  };

  if (loadError) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
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
      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg animate-pulse">
        <div className="text-center">
          <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Bar and Current Location Button */}
      <div className="flex space-x-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Search for a business or location..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {/* Search Results Dropdown */}
          {showResults && searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 z-10 mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
              {searchResults.map((place, index) => (
                <button
                  key={place.place_id || index}
                  onClick={() => selectPlace(place)}
                  className="w-full text-left px-3 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
                >
                  <div className="font-medium text-gray-900">{place.name}</div>
                  <div className="text-sm text-gray-600">{place.formatted_address}</div>
                  {place.types && place.types.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      {place.types.slice(0, 3).join(', ')}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={searchPlaces}
          disabled={isSearching || !searchQuery.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {isSearching ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          <span>Search</span>
        </button>

        <button
          onClick={getCurrentLocation}
          disabled={isGettingLocation}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          title="Use current location"
        >
          {isGettingLocation ? (
            <Loader className="w-4 h-4 animate-spin" />
          ) : (
            <Navigation className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">Current</span>
        </button>
      </div>

      {/* Instructions */}
      <p className="text-sm text-gray-600">
        Click on the map to select a location, or use the search bar above.
      </p>

      {/* Map */}
      <div className="relative border border-gray-300 rounded-lg overflow-hidden">
        <GoogleMap
          mapContainerStyle={{ ...mapContainerStyle, height }}
          center={selectedLocation || defaultCenter}
          zoom={selectedLocation ? 15 : 8}
          onLoad={onLoad}
          onUnmount={onUnmount}
          onClick={handleMapClick}
          options={{
            zoomControl: true,
            streetViewControl: false,
            mapTypeControl: false,
            fullscreenControl: false,
          }}
        >
          {selectedLocation && (
            <Marker
              position={selectedLocation}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="12" fill="#EF4444" stroke="#DC2626" stroke-width="2"/>
                    <circle cx="16" cy="16" r="4" fill="white"/>
                  </svg>
                `),
                scaledSize: new window.google.maps.Size(32, 32),
                anchor: new window.google.maps.Point(16, 16)
              }}
            />
          )}
        </GoogleMap>
      </div>

      {/* Selected Location Display */}
      {selectedLocation && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Location Selected</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            Latitude: {selectedLocation.lat.toFixed(6)}, Longitude: {selectedLocation.lng.toFixed(6)}
          </p>
        </div>
      )}
    </div>
  );
};