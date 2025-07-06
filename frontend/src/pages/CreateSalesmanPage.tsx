import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ArrowLeft, Save, User, Mail, Phone, MapPin, DollarSign, FileText } from 'lucide-react';
import { salesmanService } from '../services/apiServices';
import { CreateSalesmanData } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { USER_ROLES } from '../config/constants';
import toast from 'react-hot-toast';

interface SalesmanFormData {
  // User fields
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  confirmPassword: string;
  phone?: string;
  address?: string;
  
  // Salesman fields
  name: string;
  description?: string;
  profit_margin: number;
  is_active: boolean;
}

export const CreateSalesmanPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SalesmanFormData>({
    defaultValues: {
      profit_margin: 10,
      is_active: true,
    },
  });

  const watchPassword = watch('password');

  // Only allow owners to access this page
  if (user?.role !== USER_ROLES.OWNER) {
    return (
      <Layout title="Access Denied">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Access Denied
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Only owners can create salesmen.
          </p>
        </div>
      </Layout>
    );
  }

  const onSubmit = async (data: SalesmanFormData) => {
    try {
      setIsSubmitting(true);

      // Validate password confirmation
      if (data.password !== data.confirmPassword) {
        toast.error('Passwords do not match');
        return;
      }

      const salesmanData: CreateSalesmanData = {
        user: {
          username: data.username,
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
          password: data.password,
          confirm_password: data.confirmPassword,
          phone: data.phone || '',
          address: data.address || '',
          role: USER_ROLES.SALESMAN,
        },
        name: data.name,
        description: data.description || '',
        profit_margin: data.profit_margin,
        is_active: data.is_active,
      };

      await salesmanService.createSalesman(salesmanData);
      toast.success('Salesman created successfully!');
      navigate('/salesmen');
    } catch (error: any) {
      console.error('Error creating salesman:', error);
      if (error.response?.data?.user?.username) {
        toast.error('Username already exists');
      } else if (error.response?.data?.user?.email) {
        toast.error('Email already exists');
      } else {
        toast.error(error.response?.data?.detail || 'Failed to create salesman');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Layout title="Create Salesman">
      <div className="max-w-2xl mx-auto">
        <div className="card p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/salesmen')}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Create New Salesman
              </h2>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* User Account Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <User className="h-5 w-5 mr-2" />
                Account Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Username *</label>
                  <input
                    {...register('username', { 
                      required: 'Username is required',
                      minLength: {
                        value: 3,
                        message: 'Username must be at least 3 characters'
                      }
                    })}
                    type="text"
                    className="input"
                    placeholder="Enter username"
                  />
                  {errors.username && (
                    <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Email *</label>
                  <input
                    {...register('email', { 
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    type="email"
                    className="input"
                    placeholder="Enter email"
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">First Name *</label>
                  <input
                    {...register('first_name', { required: 'First name is required' })}
                    type="text"
                    className="input"
                    placeholder="Enter first name"
                  />
                  {errors.first_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Last Name *</label>
                  <input
                    {...register('last_name', { required: 'Last name is required' })}
                    type="text"
                    className="input"
                    placeholder="Enter last name"
                  />
                  {errors.last_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Password *</label>
                  <input
                    {...register('password', { 
                      required: 'Password is required',
                      minLength: {
                        value: 6,
                        message: 'Password must be at least 6 characters'
                      }
                    })}
                    type="password"
                    className="input"
                    placeholder="Enter password"
                  />
                  {errors.password && (
                    <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Confirm Password *</label>
                  <input
                    {...register('confirmPassword', { 
                      required: 'Please confirm password',
                      validate: value => value === watchPassword || 'Passwords do not match'
                    })}
                    type="password"
                    className="input"
                    placeholder="Confirm password"
                  />
                  {errors.confirmPassword && (
                    <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Contact Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <Phone className="h-5 w-5 mr-2" />
                Contact Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label flex items-center">
                    <Phone className="h-4 w-4 mr-1" />
                    Phone
                  </label>
                  <input
                    {...register('phone')}
                    type="tel"
                    className="input"
                    placeholder="Enter phone number"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="label flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    Address
                  </label>
                  <input
                    {...register('address')}
                    type="text"
                    className="input"
                    placeholder="Enter address"
                  />
                </div>
              </div>
            </div>

            {/* Salesman Information */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                <DollarSign className="h-5 w-5 mr-2" />
                Salesman Details
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="label">Display Name *</label>
                  <input
                    {...register('name', { required: 'Display name is required' })}
                    type="text"
                    className="input"
                    placeholder="Enter display name"
                  />
                  {errors.name && (
                    <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="label flex items-center">
                    <DollarSign className="h-4 w-4 mr-1" />
                    Profit Margin (%) *
                  </label>
                  <input
                    {...register('profit_margin', { 
                      required: 'Profit margin is required',
                      min: {
                        value: 0,
                        message: 'Profit margin cannot be negative'
                      },
                      max: {
                        value: 100,
                        message: 'Profit margin cannot exceed 100%'
                      }
                    })}
                    type="number"
                    step="0.01"
                    className="input"
                    placeholder="10.00"
                  />
                  {errors.profit_margin && (
                    <p className="mt-1 text-sm text-red-600">{errors.profit_margin.message}</p>
                  )}
                </div>

                <div className="md:col-span-2">
                  <label className="label flex items-center">
                    <FileText className="h-4 w-4 mr-1" />
                    Description
                  </label>
                  <textarea
                    {...register('description')}
                    rows={3}
                    className="input resize-none"
                    placeholder="Enter description (optional)"
                  />
                </div>

                <div className="md:col-span-2">
                  <div className="flex items-center">
                    <input
                      {...register('is_active')}
                      type="checkbox"
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900 dark:text-white">
                      Active (salesman can login and access the system)
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={() => navigate('/salesmen')}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>{isSubmitting ? 'Creating...' : 'Create Salesman'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};
