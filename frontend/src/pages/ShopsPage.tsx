import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { Users, Phone, MapPin, CreditCard, Eye, Plus, Map, Route, Grid, Navigation, ExternalLink, Copy, MapPinOff } from 'lucide-react';
import { shopService } from '../services/apiServices';
import { Shop } from '../types';
import { format } from 'date-fns';
import { formatCurrency, formatBalance } from '../utils/currency';
import { ShopMap } from '../components/maps/ShopMap';
import { RouteOptimizer } from '../components/maps/RouteOptimizer';
import toast from 'react-hot-toast';

export const ShopsPage: React.FC = () => {
  const [shops, setShops] = useState<Shop[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'map' | 'route'>('grid');
  const [startLocation, setStartLocation] = useState<{ lat: number; lng: number; name?: string } | null>(null);
  const navigate = useNavigate();

  // Generate Google Maps link for a shop
  const generateGoogleMapsLink = (shop: Shop): string => {
    if (shop.latitude && shop.longitude) {
      return `https://www.google.com/maps?q=${shop.latitude},${shop.longitude}`;
    }
    return '';
  };

  // Copy Google Maps link to clipboard
  const copyMapsLinkToClipboard = async (shop: Shop) => {
    const mapsLink = generateGoogleMapsLink(shop);
    if (mapsLink) {
      try {
        await navigator.clipboard.writeText(mapsLink);
        toast.success(`📍 Maps link copied for ${shop.name}!`);
      } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        toast.error('Failed to copy link to clipboard');
      }
    }
  };

  // Handle setting location for a shop
  const handleSetLocation = (shop: Shop) => {
    // Navigate to edit shop page with focus on location
    navigate(`/shops/${shop.id}/edit?focus=location`);
  };

  useEffect(() => {
    loadShops();
  }, []);

  const loadShops = async () => {
    try {
      setIsLoading(true);
      const data = await shopService.getShops();
      setShops(data.results);
    } catch (error) {
      console.error('Error loading shops:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Shops">
        <LoadingCard title="Loading shops data..." />
      </Layout>
    );
  }

  const totalBalance = shops.reduce((sum, shop) => sum + shop.current_balance, 0);
  const activeShops = shops.filter(shop => shop.is_active).length;

  return (
    <Layout title="Shops">
      <div className="space-y-6">
        {/* Header with Add Shop Button */}
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Shops Management</h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">Manage your shop network and monitor performance</p>
          </div>
          <button 
            onClick={() => navigate('/shops/create')}
            className="btn-primary inline-flex items-center px-4 py-2"
          >
            <Plus className="h-5 w-5 mr-2" />
            Add Shop
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                <Users className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Shops
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {shops.length}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
                <Users className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Active Shops
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {activeShops}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-purple-500">
                <CreditCard className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Balance
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(totalBalance, { useLocaleString: true })}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-orange-500">
                <MapPin className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  With Location
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {shops.filter(shop => shop.latitude && shop.longitude).length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* View Toggle */}
        <div className="flex justify-between items-center">
          <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'grid'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Grid className="w-4 h-4" />
              <span>Grid View</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'map'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Map className="w-4 h-4" />
              <span>Map View</span>
            </button>
            <button
              onClick={() => setViewMode('route')}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'route'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <Route className="w-4 h-4" />
              <span>Route Planner</span>
            </button>
          </div>

          {viewMode === 'route' && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Start Location:</span>
              {startLocation ? (
                <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                  {startLocation.name || 'Location Set'}
                </span>
              ) : (
                <span className="text-sm text-gray-500">Not set</span>
              )}
              <button
                onClick={() => {
                  // Get current location
                  if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                      (position) => {
                        setStartLocation({
                          lat: position.coords.latitude,
                          lng: position.coords.longitude,
                          name: 'Current Location'
                        });
                        toast.success('🚗 Current location set as start point!');
                      },
                      (error) => {
                        console.error('Error getting location:', error);
                        alert('Unable to get your location. Please allow location access.');
                      },
                      {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 60000
                      }
                    );
                  } else {
                    alert('Geolocation is not supported by this browser.');
                  }
                }}
                className="text-sm bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700 flex items-center space-x-1"
              >
                <Navigation className="w-3 h-3" />
                <span>Use Current Location</span>
              </button>
            </div>
          )}
        </div>

        {/* Content based on view mode */}
        {viewMode === 'grid' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {shops.length > 0 ? (
              shops.map((shop) => (
                <div key={shop.id} className="card p-6 hover:shadow-lg transition-shadow duration-200">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
                        {shop.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Contact: {shop.contact_person}
                      </p>
                    </div>
                    <div className="flex flex-col items-end space-y-1">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          shop.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {shop.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {shop.latitude && shop.longitude && (
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                          <MapPin className="w-3 h-3 mr-1" />
                          Located
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <MapPin className="h-4 w-4 mr-2 flex-shrink-0" />
                      <span className="truncate">{shop.address}</span>
                    </div>

                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <Phone className="h-4 w-4 mr-2 flex-shrink-0" />
                      <span>{shop.phone}</span>
                    </div>

                    {shop.email && (
                      <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                        <span>✉</span>
                        <span className="ml-2 truncate">{shop.email}</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Current Balance</p>
                        <p className={`text-lg font-semibold ${
                          shop.current_balance >= 0 
                            ? 'text-green-600' 
                            : 'text-red-600'
                        }`}>
                          {formatBalance(shop.current_balance)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500 dark:text-gray-400">Credit Limit</p>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(shop.credit_limit, { useLocaleString: true })}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Shop Margin</p>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {shop.shop_margin}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500 dark:text-gray-400">Joined</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {format(new Date(shop.created_at), 'MMM yyyy')}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Location Section */}
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                        Location
                      </p>
                      {shop.latitude && shop.longitude ? (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          <MapPin className="w-3 h-3 mr-1" />
                          Set
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                          <MapPinOff className="w-3 h-3 mr-1" />
                          Not Set
                        </span>
                      )}
                    </div>

                    {shop.latitude && shop.longitude ? (
                      <div className="space-y-2">
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          <span className="font-mono">
                            {Number(shop.latitude).toFixed(6)}, {Number(shop.longitude).toFixed(6)}
                          </span>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => copyMapsLinkToClipboard(shop)}
                            className="flex-1 inline-flex items-center justify-center px-3 py-2 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
                          >
                            <Copy className="w-3 h-3 mr-1" />
                            Copy Maps Link
                          </button>
                          <a
                            href={generateGoogleMapsLink(shop)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center justify-center px-3 py-2 text-xs font-medium text-green-700 bg-green-50 border border-green-200 rounded-md hover:bg-green-100 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Open Maps
                          </a>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          No location coordinates set for this shop
                        </p>
                        <button
                          onClick={() => handleSetLocation(shop)}
                          className="w-full inline-flex items-center justify-center px-3 py-2 text-xs font-medium text-orange-700 bg-orange-50 border border-orange-200 rounded-md hover:bg-orange-100 transition-colors"
                        >
                          <MapPin className="w-3 h-3 mr-1" />
                          Set Location
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex space-x-2">
                    <button 
                      onClick={() => navigate(`/shops/${shop.id}`)}
                      className="flex-1 btn-primary text-sm py-2"
                    >
                      <Eye className="h-4 w-4 mr-2" />
                      View Details
                    </button>
                    {shop.latitude && shop.longitude && (
                      <button 
                        onClick={() => setViewMode('map')}
                        className="btn-outline text-sm py-2 px-3"
                        title="View on Map"
                      >
                        <Map className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-full text-center py-12">
                <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">No shops found</p>
              </div>
            )}
          </div>
        )}

        {viewMode === 'map' && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Shop Locations Map
            </h3>
            <ShopMap 
              shops={shops}
              onShopSelect={(shop) => {
                console.log('Selected shop:', shop);
                // You can add additional functionality here
              }}
            />
          </div>
        )}

        {viewMode === 'route' && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Route Optimizer
            </h3>
            {startLocation ? (
              <RouteOptimizer 
                shops={shops}
                startLocation={startLocation}
                onRouteCalculated={(route) => {
                  console.log('Route calculated:', route);
                  // You can add additional functionality here
                }}
              />
            ) : (
              <div className="text-center py-12">
                <Route className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Please set a start location to begin route planning
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 max-w-md mx-auto">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">🚗 Start Your Route:</h4>
                  <p className="text-sm text-blue-700">
                    Use your current location as the starting point for the most accurate route planning.
                  </p>
                </div>
                <button
                  onClick={() => {
                    if (navigator.geolocation) {
                      navigator.geolocation.getCurrentPosition(
                        (position) => {
                          setStartLocation({
                            lat: position.coords.latitude,
                            lng: position.coords.longitude,
                            name: 'Current Location'
                          });
                          toast.success('🚗 Current location set as start point!');
                        },
                        (error) => {
                          console.error('Error getting location:', error);
                          alert('Unable to get your location. Please allow location access.');
                        },
                        {
                          enableHighAccuracy: true,
                          timeout: 10000,
                          maximumAge: 60000
                        }
                      );
                    } else {
                      alert('Geolocation is not supported by this browser.');
                    }
                  }}
                  className="btn-primary flex items-center space-x-2"
                >
                  <Navigation className="w-4 h-4" />
                  <span>Use Current Location</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};
