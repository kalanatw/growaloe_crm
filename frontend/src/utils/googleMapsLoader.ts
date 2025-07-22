// Centralized Google Maps loader configuration
// This ensures all components use the same loader options

export const GOOGLE_MAPS_LIBRARIES: ("places" | "geometry" | "drawing" | "visualization")[] = ['places'];

export const GOOGLE_MAPS_CONFIG = {
  id: 'google-map-script',
  googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || '',
  libraries: GOOGLE_MAPS_LIBRARIES
};

// Export the libraries array as a constant to prevent re-creation
export { GOOGLE_MAPS_LIBRARIES as libraries };