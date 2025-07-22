import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { shopService, companyService } from '../services/apiServices';
import { CreateShopData, Shop } from '../types';
import { ArrowLeft, Save, MapPin } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { LocationPicker } from '../components/maps/LocationPicker';

export const EditShopPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [maxShopMargin, setMaxShopMargin] = useState<number>(20);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lng: number; address?: string } | null>(null);
  const [shop, setShop] = useState<Shop | null>(null);
  const userRole = user?.role || 'salesman';

  // Check if we should focus on location section
  const focusLocation = searchParams.get('focus') === 'location';

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset
  } = useForm<CreateShopData>();

  useEffect(() => {
    if (id) {
      loadShopData();
      loadCompanySettings();
    }
  }, [id]);

  const loadShopData = async () => {
    try {
      setIsLoading(true);
      const shopData = await shopService.getShop(parseInt(id!));
      setShop(shopData);

      // Set form values
      reset({
        name: shopData.name,
        address: shopData.address,
        contact_person: shopData.contact_person,
        phone: shopData.phone,
        email: shopData.email || '',
        shop_margin: shopData.shop_margin,
        credit_limit: shopData.credit_limit,
        is_active: shopData.is_active
      });

      // Set location if available
      if (shopData.latitude && shopData.longitude) {
        setSelectedLocation({
          lat: shopData.latitude,
          lng: shopData.longitude
        });
      }
    } catch (error) {
      console.error('Error loading shop:', error);
      toast.error('Failed to load shop data');
      navigate('/shops');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCompanySettings = async () => {
    try {
      const companySettings = await companyService.getPublicSettings();
      setMaxShopMargin(companySettings.max_shop_margin_for_salesmen);
    } catch (error) {
      console.error('Error loading company settings:', error);
    }
  };

  const validateShopMargin = (value: number | undefined) => {
    if (value === undefined || value === null) return true;
    if (value < 0) return 'Margin cannot be negative';
    if (value > 100) return 'Margin cannot exceed 100%';
    if (userRole === 'salesman' && value > maxShopMargin) {
      return `Salesmen cannot set margin above ${maxShopMargin}%`;
    }
    return true;
  };

  const onSubmit = async (data: CreateShopData) => {
    const shopMargin = data.shop_margin || 0;
    if (userRole === 'salesman' && shopMargin > maxShopMargin) {
      toast.error(`Shop margin cannot exceed ${maxShopMargin}% for salesmen`);
      return;
    }

    try {
      setIsSubmitting(true);

      const shopData = {
        ...data,
        ...(selectedLocation && {
          latitude: selectedLocation.lat,
          longitude: selectedLocation.lng
        })
      };

      await shopService.updateShop(parseInt(id!), shopData);
      toast.success('Shop updated successfully!');
      navigate('/shops');
    } catch (error: any) {
      console.error('Error updating shop:', error);
      toast.error(error.response?.data?.detail || 'Failed to update shop');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Edit Shop">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (!shop) {
    return (
      <Layout title="Edit Shop">
        <div className="text-center py-12">
          <p className="text-gray-600">Shop not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Edit Shop">
      <div className="max-w-2xl mx-auto">
        <div className="card p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/shops')}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Edit Shop
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {shop.name}
                </p>
              </div>
            </div>
          </div>

          {focusLocation && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <MapPin className="h-5 w-5 text-blue-600" />
                <h3 className="font-medium text-blue-800">Set Shop Location</h3>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                Use the location picker below to set the precise location for this shop.
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Basic Information
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Shop Name *</label>
                  <input
                    {...register('name', { required: 'Shop name is required' })}
                    type="text"
                    className="input"
                    placeholder="Enter shop name"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Contact Person *</label>
                  <input
                    {...register('contact_person', { required: 'Contact person is required' })}
                    type="text"
                    className="input"
                    placeholder="Enter contact person name"
                  />
                  {errors.contact_person && (
                    <p className="mt-1 text-sm text-red-600">{errors.contact_person.message}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="label">Address *</label>
                <textarea
                  {...register('address', { required: 'Address is required' })}
                  className="input"
                  rows={3}
                  placeholder="Enter complete address"
                />
                {errors.address && (
                  <p className="mt-1 text-sm text-red-600">{errors.address.message}</p>
                )}
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Contact Information
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Phone Number *</label>
                  <input
                    {...register('phone', {
                      required: 'Phone number is required',
                      pattern: {
                        value: /^[+]?[\d\s\-()]+$/,
                        message: 'Please enter a valid phone number'
                      }
                    })}
                    type="tel"
                    className="input"
                    placeholder="+1234567890"
                  />
                  {errors.phone && (
                    <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Email Address</label>
                  <input
                    {...register('email', {
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Please enter a valid email address'
                      }
                    })}
                    type="email"
                    className="input"
                    placeholder="shop@example.com"
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Location Information */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <MapPin className="h-5 w-5 text-gray-600" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Shop Location
                </h3>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-800 mb-2">📍 How to set location:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• <strong>Use Current Location:</strong> Click the green button to use your device's GPS</li>
                  <li>• <strong>Search for Business:</strong> Type the shop name to find it on Google Maps</li>
                  <li>• <strong>Click on Map:</strong> Click anywhere on the map to set the exact location</li>
                  <li>• <strong>Search Address:</strong> Enter an address to find and select the location</li>
                </ul>
              </div>

              <LocationPicker
                onLocationSelect={(lat, lng, address) => {
                  setSelectedLocation({ lat, lng, address });
                  if (address) {
                    toast.success('Location updated successfully!');
                  }
                }}
                initialLocation={selectedLocation || undefined}
              />

              {selectedLocation && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Location Set</span>
                  </div>
                  <p className="text-sm text-green-700 mt-1">
                    Coordinates: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lng.toFixed(6)}
                  </p>
                  {selectedLocation.address && (
                    <p className="text-sm text-green-700">
                      Address: {selectedLocation.address}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Business Settings */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Business Settings
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Shop Margin (%)</label>
                  <input
                    {...register('shop_margin', {
                      valueAsNumber: true,
                      validate: validateShopMargin
                    })}
                    type="number"
                    step="0.1"
                    min="0"
                    max={userRole === 'salesman' ? maxShopMargin : 100}
                    className="input"
                    placeholder="0.0"
                  />
                  {errors.shop_margin && (
                    <p className="mt-1 text-sm text-red-600">{errors.shop_margin.message}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    Profit margin percentage for this shop
                    {userRole === 'salesman' && (
                      <span className="block text-orange-600 dark:text-orange-400">
                        Maximum allowed for salesmen: {maxShopMargin}%
                      </span>
                    )}
                  </p>
                </div>

                <div>
                  <label className="label">Credit Limit (LKR)</label>
                  <input
                    {...register('credit_limit', {
                      valueAsNumber: true,
                      min: { value: 0, message: 'Credit limit cannot be negative' }
                    })}
                    type="number"
                    step="0.01"
                    min="0"
                    className="input"
                    placeholder="0.00"
                  />
                  {errors.credit_limit && (
                    <p className="mt-1 text-sm text-red-600">{errors.credit_limit.message}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">
                    Maximum credit amount allowed for this shop
                  </p>
                </div>
              </div>

              <div className="flex items-center">
                <input
                  {...register('is_active')}
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-900 dark:text-white">
                  Shop is active
                </label>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4 pt-6">
              <button
                type="button"
                onClick={() => navigate('/shops')}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
              >
                {isSubmitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {isSubmitting ? 'Updating...' : 'Update Shop'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};