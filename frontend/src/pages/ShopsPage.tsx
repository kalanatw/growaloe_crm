import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { Users, Phone, MapPin, CreditCard, Eye, Plus } from 'lucide-react';
import { shopService } from '../services/apiServices';
import { Shop } from '../types';
import { format } from 'date-fns';
import { formatCurrency, formatBalance } from '../utils/currency';

export const ShopsPage: React.FC = () => {
  const [shops, setShops] = useState<Shop[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
        </div>

        {/* Shops Grid */}
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
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      shop.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {shop.is_active ? 'Active' : 'Inactive'}
                  </span>
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

                <div className="mt-4">
                  <button 
                    onClick={() => navigate(`/shops/${shop.id}`)}
                    className="w-full btn-primary text-sm py-2"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </button>
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
      </div>
    </Layout>
  );
};
