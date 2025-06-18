import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { shopService, companyService } from '../services/apiServices';
import { CreateShopData } from '../types';
import { ArrowLeft, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';

export const CreateShopPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [maxShopMargin, setMaxShopMargin] = useState<number>(20); // Default to 20%
  const userRole = user?.role || 'salesman'; // Get role from auth context

  useEffect(() => {
    loadCompanySettings();
  }, []);

  const loadCompanySettings = async () => {
    try {
      const [companySettings] = await Promise.all([
        companyService.getPublicSettings(),
      ]);

      setMaxShopMargin(companySettings.max_shop_margin_for_salesmen);
    } catch (error) {
      console.error('Error loading company settings:', error);
      // Use default values if settings can't be loaded
    }
  };

  // Helper function to get effective max margin based on user role
  const getEffectiveMaxMargin = () => {
    return userRole === 'salesman' ? maxShopMargin : 100;
  };

  const {
    register,
    handleSubmit,
    formState: { errors },
    clearErrors,
    setError,
  } = useForm<CreateShopData>({
    defaultValues: {
      shop_margin: 0,
      credit_limit: 0,
      is_active: true,
    },
  });

  // Custom validation for shop margin
  const validateShopMargin = (value: number | undefined) => {
    if (value === undefined || value === null) return true; // Allow undefined/null (not required field)
    if (value < 0) return 'Margin cannot be negative';
    if (value > 100) return 'Margin cannot exceed 100%';
    if (userRole === 'salesman' && value > maxShopMargin) {
      return `Salesmen cannot set margin above ${maxShopMargin}%`;
    }
    return true;
  };

  const onSubmit = async (data: CreateShopData) => {
    // Validate shop margin for salesmen
    const shopMargin = data.shop_margin || 0;
    if (userRole === 'salesman' && shopMargin > maxShopMargin) {
      toast.error(`Shop margin cannot exceed ${maxShopMargin}% for salesmen`);
      return;
    }

    try {
      setIsSubmitting(true);
      const shop = await shopService.createShop(data);
      toast.success('Shop created successfully!');
      navigate(`/shops/${shop.id}`);
    } catch (error: any) {
      console.error('Error creating shop:', error);
      toast.error(error.response?.data?.detail || 'Failed to create shop');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout title="Create Shop">
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
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Add New Shop
              </h2>
            </div>
          </div>

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
                    max={getEffectiveMaxMargin()}
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
                {isSubmitting ? 'Creating...' : 'Create Shop'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};
