# Shop Location Mapping Feature Setup Guide

This guide explains how to set up and use the new shop location mapping feature that includes map visualization, location picking, and route optimization.

## Features Added

1. **Shop Location Storage**: Shops can now have latitude and longitude coordinates
2. **Interactive Map View**: View all shops on a Google Maps interface
3. **Location Picker**: Select shop locations when creating/editing shops
4. **Route Optimizer**: Calculate optimized routes to visit multiple shops
5. **Multiple View Modes**: Switch between grid view, map view, and route planner

## Setup Instructions

### 1. Google Maps API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Maps JavaScript API
   - Places API
   - Directions API
   - Geocoding API
4. Create credentials (API Key)
5. Restrict the API key to your domain for security

### 2. Environment Configuration

Update your `frontend/.env` file:

```env
# Google Maps API Key
REACT_APP_GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
```

**Important**: Replace `your_actual_google_maps_api_key_here` with your real Google Maps API key.

### 3. Database Migration

Run the database migration to add location fields to the Shop model:

```bash
cd backend
python manage.py migrate accounts
```

This will add `latitude` and `longitude` fields to the shops table.

### 4. Dependencies

The required npm packages have already been installed:
- `@googlemaps/js-api-loader`
- `@react-google-maps/api`

## Usage Guide

### For Shop Owners/Managers

#### Adding Shop Locations

1. **When Creating a New Shop**:
   - Navigate to "Add Shop" page
   - Fill in the basic shop information
   - In the "Shop Location" section, either:
     - Search for the location using the search bar
     - Click directly on the map to select the location
   - The coordinates will be automatically saved

2. **For Existing Shops**:
   - Edit the shop details
   - Add location using the same location picker interface

#### Viewing Shops on Map

1. Go to the Shops page
2. Click on "Map View" tab
3. All shops with location data will be displayed as markers
4. Click on any marker to see shop details

#### Route Planning

1. Go to the Shops page
2. Click on "Route Planner" tab
3. Set your start location (or use current location)
4. Select the shops you want to visit
5. Click "Calculate Optimized Route"
6. The system will show the most efficient route

### For Developers

#### Backend Changes

1. **Shop Model** (`backend/accounts/models.py`):
   - Added `latitude` and `longitude` fields
   - Both fields are optional (null=True, blank=True)

2. **Shop Serializer** (`backend/accounts/serializers.py`):
   - Updated to include location fields in API responses

3. **Route Optimization Endpoint**:
   - `POST /api/auth/shops/optimize_route/`
   - Accepts shop IDs and start location
   - Returns shop data for route calculation

#### Frontend Components

1. **ShopMap** (`frontend/src/components/maps/ShopMap.tsx`):
   - Displays shops on Google Maps
   - Interactive markers with shop information
   - Handles shop selection events

2. **LocationPicker** (`frontend/src/components/maps/LocationPicker.tsx`):
   - Interactive map for selecting locations
   - Search functionality for addresses
   - Geocoding integration

3. **RouteOptimizer** (`frontend/src/components/maps/RouteOptimizer.tsx`):
   - Shop selection interface
   - Route calculation using Google Maps Directions API
   - Optimized waypoint ordering

#### API Endpoints

- `GET /api/auth/shops/` - Now includes latitude/longitude in response
- `POST /api/auth/shops/` - Accepts latitude/longitude when creating shops
- `PATCH /api/auth/shops/{id}/` - Update shop location
- `POST /api/auth/shops/optimize_route/` - Route optimization endpoint

## Testing

### Test the Map Components

1. Create a test page to verify map functionality:

```typescript
import { MapTest } from '../components/maps/MapTest';

// Add to your routing or create a test page
<MapTest />
```

2. Check browser console for any API key or loading errors
3. Verify that maps load correctly and interactions work

### Common Issues

1. **Maps not loading**:
   - Check if Google Maps API key is set correctly
   - Verify API key has necessary permissions
   - Check browser console for errors

2. **Location not saving**:
   - Ensure backend migration has been run
   - Check API requests in browser network tab
   - Verify serializer includes location fields

3. **Route calculation fails**:
   - Ensure Directions API is enabled
   - Check that shops have valid coordinates
   - Verify start location is provided

## Security Considerations

1. **API Key Security**:
   - Restrict API key to your domain
   - Set up billing alerts
   - Monitor API usage

2. **Data Validation**:
   - Validate latitude/longitude ranges
   - Sanitize location data before storage
   - Implement rate limiting for route calculations

## Future Enhancements

1. **Offline Maps**: Cache map tiles for offline usage
2. **Real-time Tracking**: Track salesman locations during routes
3. **Advanced Analytics**: Route efficiency metrics and reporting
4. **Mobile App**: Companion mobile app for field salesmen
5. **Geofencing**: Automatic check-ins when visiting shops

## Support

For issues or questions:
1. Check the browser console for error messages
2. Verify Google Maps API key configuration
3. Test with the provided MapTest component
4. Review the network requests in browser dev tools

## Cost Considerations

Google Maps API usage is charged based on:
- Map loads
- Geocoding requests
- Directions API calls
- Places API searches

Monitor your usage in the Google Cloud Console and set up billing alerts to avoid unexpected charges.