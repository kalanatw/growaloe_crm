import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { shopService, transactionService } from '../services/apiServices';
import { Shop, Transaction } from '../types';
import { 
  ArrowLeftIcon, 
  MapPinIcon, 
  PhoneIcon, 
  EnvelopeIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  FlagIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { formatBalance, formatCurrency, formatCurrencyWithSign } from '../utils/currency';
import { ShopMap } from '../components/maps/ShopMap';

const getTransactionStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
    case 'pending':
      return <ClockIcon className="w-4 h-4 text-yellow-500" />;
    case 'failed':
      return <XCircleIcon className="w-4 h-4 text-red-500" />;
    default:
      return <ClockIcon className="w-4 h-4 text-gray-500" />;
  }
};

const getTransactionStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'failed':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export const ShopDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [shop, setShop] = useState<Shop | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'transactions' | 'invoices' | 'location'>('overview');
  const [isFlagged, setIsFlagged] = useState(false);

  useEffect(() => {
    if (id) {
      fetchShopDetails(id);
      if (activeTab === 'transactions') {
        fetchTransactions(id);
      }
    }
  }, [id, activeTab]);

  const fetchShopDetails = async (shopId: string) => {
    try {
      setLoading(true);
      const data = await shopService.getShop(parseInt(shopId));
      setShop(data);
    } catch (error) {
      console.error('Error fetching shop details:', error);
      toast.error('Failed to load shop details');
      navigate('/shops');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async (shopId: string) => {
    try {
      setTransactionsLoading(true);
      const data = await transactionService.getTransactions({ shop_id: parseInt(shopId) });
      setTransactions(data.results || []);
    } catch (error) {
      console.error('Error fetching transactions:', error);
      toast.error('Failed to load transactions');
    } finally {
      setTransactionsLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Shop Details">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  if (!shop) {
    return (
      <Layout title="Shop Details">
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Shop not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={shop.name}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/shops')}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{shop.name}</h1>
              <p className="text-gray-600 dark:text-gray-400">Shop Details & Balance History</p>
            </div>
          </div>
          
          {/* Shop Actions */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsFlagged(!isFlagged)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isFlagged
                  ? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-300 dark:hover:bg-red-800'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
              title={isFlagged ? 'Remove flag' : 'Flag this shop'}
            >
              <FlagIcon className="w-4 h-4" />
              <span>{isFlagged ? 'Flagged' : 'Flag Shop'}</span>
            </button>
            
            {shop.latitude && shop.longitude && (
              <button
                onClick={() => setActiveTab('location')}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800 rounded-md text-sm font-medium transition-colors"
                title="View shop location on map"
              >
                <EyeIcon className="w-4 h-4" />
                <span>View on Map</span>
              </button>
            )}
          </div>
        </div>

        {/* Shop Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-primary-100 dark:bg-primary-900">
                <CurrencyDollarIcon className="w-8 h-8 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Current Balance</p>
                <p className={`text-2xl font-bold ${
                  shop.current_balance >= 0 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {formatBalance(shop.current_balance)}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-orange-100 dark:bg-orange-900">
                <CurrencyDollarIcon className="w-8 h-8 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Credit Limit</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(shop.credit_limit, { useLocaleString: true })}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-full ${
                shop.is_active 
                  ? 'bg-green-100 dark:bg-green-900' 
                  : 'bg-red-100 dark:bg-red-900'
              }`}>
                <CheckCircleIcon className={`w-8 h-8 ${
                  shop.is_active 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Status</p>
                <p className={`text-2xl font-bold ${
                  shop.is_active 
                    ? 'text-green-600 dark:text-green-400' 
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {shop.is_active ? 'Active' : 'Inactive'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'overview', label: 'Overview' },
              { key: 'transactions', label: 'Transaction History' },
              { key: 'invoices', label: 'Recent Invoices' },
              ...(shop.latitude && shop.longitude ? [{ key: 'location', label: 'Location' }] : [])
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Contact Information */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Contact Information
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <MapPinIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Address</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.address}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <PhoneIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Phone</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <EnvelopeIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Email</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.email}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Account Details */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Account Details
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Shop Code</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{shop.shop_code || shop.id}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Registration Date</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(shop.date_created || shop.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Last Updated</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(shop.date_updated || shop.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Payment Terms</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {shop.payment_terms || 'Net 30 days'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'transactions' && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Transaction History
                </h3>
              </div>
              
              {transactionsLoading ? (
                <div className="flex items-center justify-center h-32">
                  <LoadingSpinner />
                </div>
              ) : transactions.length === 0 ? (
                <div className="p-6 text-center">
                  <p className="text-gray-500 dark:text-gray-400">No transactions found</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                      {transactions.map((transaction) => (
                        <tr key={transaction.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                            {new Date(transaction.date_created).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                            {transaction.description || `${transaction.transaction_type} transaction`}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              transaction.transaction_type === 'credit' 
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            }`}>
                              {transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">                            <span className={
                              transaction.transaction_type === 'credit'
                                ? 'text-green-600 dark:text-green-400'
                                : 'text-red-600 dark:text-red-400'
                            }>
                              {formatCurrencyWithSign(
                                transaction.transaction_type === 'credit' ? transaction.amount : -transaction.amount,
                                { showPositiveSign: true }
                              )}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center space-x-1">
                              {getTransactionStatusIcon(transaction.status)}
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTransactionStatusColor(transaction.status)}`}>
                                {transaction.status.charAt(0).toUpperCase() + transaction.status.slice(1)}
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'invoices' && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Recent Invoices
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                Invoice history will be displayed here. This feature can be implemented to show recent invoices for this shop.
              </p>
            </div>
          )}

          {activeTab === 'location' && shop.latitude && shop.longitude && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Shop Location
                  </h3>
                  {isFlagged && (
                    <div className="flex items-center space-x-2 px-3 py-1 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-full text-sm">
                      <FlagIcon className="w-4 h-4" />
                      <span>Flagged Shop</span>
                    </div>
                  )}
                </div>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  View {shop.name} on the map and get directions
                </p>
              </div>
              
              <div className="p-6">
                {/* Location Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Address</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.address}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Coordinates</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {(() => {
                          const lat = typeof shop.latitude === 'number' ? shop.latitude : parseFloat(shop.latitude as any);
                          const lng = typeof shop.longitude === 'number' ? shop.longitude : parseFloat(shop.longitude as any);
                          
                          if (!isNaN(lat) && !isNaN(lng)) {
                            return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                          }
                          return 'Invalid coordinates';
                        })()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Contact Person</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.contact_person}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">Phone</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{shop.phone}</p>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-3 mb-6">
                  <a
                    href={`https://www.google.com/maps/dir/?api=1&destination=${shop.latitude},${shop.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                  >
                    <MapPinIcon className="w-4 h-4" />
                    <span>Get Directions</span>
                  </a>
                  
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${shop.latitude},${shop.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                  >
                    <EyeIcon className="w-4 h-4" />
                    <span>View in Google Maps</span>
                  </a>
                  
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`${shop.latitude}, ${shop.longitude}`);
                      toast.success('Coordinates copied to clipboard!');
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm"
                  >
                    <span>📋</span>
                    <span>Copy Coordinates</span>
                  </button>
                </div>

                {/* Map */}
                <div className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
                  <ShopMap
                    shops={[{
                      ...shop,
                      // Highlight the shop if it's flagged
                      name: isFlagged ? `🚩 ${shop.name}` : shop.name
                    }]}
                    height="500px"
                    center={{ lat: shop.latitude, lng: shop.longitude }}
                    onShopSelect={(selectedShop) => {
                      toast.success(`Selected: ${selectedShop.name}`);
                    }}
                  />
                </div>

                {/* Map Legend */}
                <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                        <span className="text-gray-600 dark:text-gray-400">Shop Location</span>
                      </div>
                      {isFlagged && (
                        <div className="flex items-center space-x-2">
                          <FlagIcon className="w-3 h-3 text-red-500" />
                          <span className="text-red-600 dark:text-red-400">Flagged Shop</span>
                        </div>
                      )}
                    </div>
                    <span className="text-gray-500 dark:text-gray-400">
                      Click marker for details
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};
