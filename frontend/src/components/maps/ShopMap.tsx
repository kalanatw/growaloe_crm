import React, { useState, useCallback } from 'react';
import { GoogleMap, Marker, InfoWindow, useJsApiLoader } from '@react-google-maps/api';
import { Shop } from '../../types';
import { MapPin, Phone, User } from 'lucide-react';
import { GOOGLE_MAPS_CONFIG } from '../../utils/googleMapsLoader';

interface ShopMapProps {
  shops: Shop[];
  onShopSelect?: (shop: Shop) => void;
  height?: string;
  center?: { lat: number; lng: number };
}

const mapContainerStyle = {
  width: '100%',
  height: '400px'
};

const defaultCenter = {
  lat: 7.8731, // Sri Lanka center
  lng: 80.7718
};

export const ShopMap: React.FC<ShopMapProps> = ({ 
  shops, 
  onShopSelect, 
  height = '400px',
  center 
}) => {
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);

  const { isLoaded, loadError } = useJsApiLoader(GOOGLE_MAPS_CONFIG);

  const onLoad = useCallback((map: google.maps.Map) => {
    // Map loaded successfully
  }, []);

  const onUnmount = useCallback(() => {
    // Map unmounted
  }, []);

  const handleMarkerClick = (shop: Shop) => {
    setSelectedShop(shop);
    onShopSelect?.(shop);
  };

  const validShops = shops.filter(shop => {
    const lat = typeof shop.latitude === 'number' ? shop.latitude : parseFloat(shop.latitude as any);
    const lng = typeof shop.longitude === 'number' ? shop.longitude : parseFloat(shop.longitude as any);
    
    return shop.latitude !== null && 
           shop.longitude !== null && 
           shop.latitude !== undefined && 
           shop.longitude !== undefined &&
           !isNaN(lat) && 
           !isNaN(lng) &&
           lat >= -90 && lat <= 90 &&
           lng >= -180 && lng <= 180;
  });

  // Calculate center based on shops if not provided
  const mapCenter = center || (validShops.length > 0 
    ? {
        lat: validShops.reduce((sum, shop) => {
          const lat = typeof shop.latitude === 'number' ? shop.latitude : parseFloat(shop.latitude as any);
          return sum + lat;
        }, 0) / validShops.length,
        lng: validShops.reduce((sum, shop) => {
          const lng = typeof shop.longitude === 'number' ? shop.longitude : parseFloat(shop.longitude as any);
          return sum + lng;
        }, 0) / validShops.length
      }
    : defaultCenter);

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
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <GoogleMap
        mapContainerStyle={{ ...mapContainerStyle, height }}
        center={mapCenter}
        zoom={validShops.length > 1 ? 10 : 12}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          zoomControl: true,
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: true,
        }}
      >
        {validShops.map((shop) => {
          const lat = typeof shop.latitude === 'number' ? shop.latitude : parseFloat(shop.latitude as any);
          const lng = typeof shop.longitude === 'number' ? shop.longitude : parseFloat(shop.longitude as any);
          
          return (
            <Marker
              key={shop.id}
              position={{ lat, lng }}
              onClick={() => handleMarkerClick(shop)}
              title={shop.name}
              icon={{
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                  <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="12" fill="#3B82F6" stroke="#1E40AF" stroke-width="2"/>
                    <circle cx="16" cy="16" r="4" fill="white"/>
                  </svg>
                `),
                scaledSize: new window.google.maps.Size(32, 32),
                anchor: new window.google.maps.Point(16, 16)
              }}
            />
          );
        })}

        {selectedShop && (
          <InfoWindow
            position={{ 
              lat: typeof selectedShop.latitude === 'number' ? selectedShop.latitude : parseFloat(selectedShop.latitude as any),
              lng: typeof selectedShop.longitude === 'number' ? selectedShop.longitude : parseFloat(selectedShop.longitude as any)
            }}
            onCloseClick={() => setSelectedShop(null)}
          >
            <div className="p-2 max-w-xs">
              <h3 className="font-semibold text-gray-900 mb-2">{selectedShop.name}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="flex items-center">
                  <MapPin className="w-3 h-3 mr-1" />
                  <span className="truncate">{selectedShop.address}</span>
                </div>
                <div className="flex items-center">
                  <User className="w-3 h-3 mr-1" />
                  <span>{selectedShop.contact_person}</span>
                </div>
                <div className="flex items-center">
                  <Phone className="w-3 h-3 mr-1" />
                  <span>{selectedShop.phone}</span>
                </div>
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <span className="text-xs text-gray-500">
                    Salesman: {selectedShop.salesman.name}
                  </span>
                </div>
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
      
      {validShops.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-90">
          <div className="text-center">
            <MapPin className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">No shops with location data</p>
            <p className="text-sm text-gray-500">Add location coordinates to shops to see them on the map</p>
          </div>
        </div>
      )}
    </div>
  );
};