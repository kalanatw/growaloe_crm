import { apiClient } from './api';

export interface PlaceResult {
  place_id: string;
  name: string;
  formatted_address: string;
  types: string[];
  rating?: number;
  location: {
    lat: number;
    lng: number;
  };
  business_status?: string;
  price_level?: number;
}

export interface GeocodeResult {
  formatted_address: string;
  location: {
    lat: number;
    lng: number;
  };
  place_id: string;
  types: string[];
}

export const mapsService = {
  // Search for places using backend proxy
  searchPlaces: async (query: string): Promise<PlaceResult[]> => {
    try {
      const response = await apiClient.post('/auth/shops/search_places/', {
        query: query
      }) as { places?: PlaceResult[] };
      return response.places || [];
    } catch (error) {
      console.error('Places search error:', error);
      throw error;
    }
  },

  // Search nearby places
  searchNearbyPlaces: async (
    location: { lat: number; lng: number },
    type: string = 'establishment'
  ): Promise<PlaceResult[]> => {
    try {
      const response = await apiClient.post('/auth/shops/search_places/', {
        location: location,
        type: type
      }) as { places?: PlaceResult[] };
      return response.places || [];
    } catch (error) {
      console.error('Nearby places search error:', error);
      throw error;
    }
  },

  // Geocode an address
  geocodeAddress: async (address: string): Promise<GeocodeResult[]> => {
    try {
      const response = await apiClient.post('/auth/shops/geocode_address/', {
        address: address
      }) as { results?: GeocodeResult[] };
      return response.results || [];
    } catch (error) {
      console.error('Geocoding error:', error);
      throw error;
    }
  }
};