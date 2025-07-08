import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { 
  ArrowPathIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  DocumentTextIcon,
  BuildingStorefrontIcon,
  UserIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  ClockIcon,
  ChartBarIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import { batchReturnService } from '../services/batchReturnService';
import { formatCurrency } from '../utils/currency';
import { formatDate } from '../utils/date';
import toast from 'react-hot-toast';

interface BatchReturn {
  id: number;
  return_number: string;
  invoice_number: string;
  product_name: string;
  product_sku: string;
  batch_number: string;
  batch_expiry_date: string;
  quantity: number;
  reason: string;
  return_amount: number;
  approved: boolean;
  shop_name: string;
  salesman_name: string;
  created_at: string;
  notes?: string;
}

interface BatchInfo {
  batch_id: number;
  batch_number: string;
  product_name: string;
  product_sku: string;
  manufacturing_date: string;
  expiry_date: string;
  initial_quantity: number;
  current_quantity: number;
  total_sold: number;
  total_returned: number;
  return_rate: number;
  quality_status: string;
  shops_sold_to: any[];
}

interface BatchSaleSummary {
  shop_id: number;
  shop_name: string;
  invoice_id: number;
  invoice_number: string;
  quantity_sold: number;
  unit_price: number;
  salesman_name: string;
  sale_date: string;
}

interface BatchReturnSummary {
  shop_id: number;
  shop_name: string;
  return_id: number;
  return_number: string;
  quantity_returned: number;
  return_amount: number;
  reason: string;
  return_date: string;
}

interface SalesmanAssignment {
  salesman_id: number;
  salesman_name: string;
  assigned_quantity: number;
  delivered_quantity: number;
  returned_quantity: number;
  outstanding_quantity: number;
  assignment_date: string;
  status: string;
}

interface BatchTraceability {
  batch_id: number;
  batch_number: string;
  product_name: string;
  product_sku: string;
  manufacturing_date: string;
  expiry_date: string | null;
  initial_quantity: number;
  current_quantity: number;
  total_sold: number;
  total_returned: number;
  shops_sold_to: BatchSaleSummary[];
  shops_returned_from: BatchReturnSummary[];
  salesmen_assigned: SalesmanAssignment[];
  quality_status: string;
  return_rate: number;
  is_expired: boolean;
}

interface ReturnsAnalytics {
  total_returns: number;
  total_return_amount: number;
  returns_by_reason: Array<{
    reason: string;
    count: number;
    amount: number;
  }>;
  daily_trends: Array<{
    date: string;
    count: number;
    amount: number;
  }>;
  top_returned_products: Array<{
    product__name: string;
    product__sku: string;
    count: number;
    amount: number;
  }>;
  batch_analysis: Array<{
    batch__batch_number: string;
    batch__product__name: string;
    count: number;
    amount: number;
  }>;
}

export const ReturnsPage: React.FC = () => {
  const [returns, setReturns] = useState<BatchReturn[]>([]);
  const [analytics, setAnalytics] = useState<ReturnsAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  
  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [batchSearchTerm, setBatchSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'approved' | 'pending'>('all');
  const [reasonFilter, setReasonFilter] = useState<string>('all');
  
  // Modal states
  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const [isBatchSearchModalOpen, setIsBatchSearchModalOpen] = useState(false);
  const [isTraceabilityModalOpen, setIsTraceabilityModalOpen] = useState(false);
  const [isAnalyticsModalOpen, setIsAnalyticsModalOpen] = useState(false);
  
  // Selected data
  const [selectedReturn, setSelectedReturn] = useState<BatchReturn | null>(null);
  const [selectedBatch, setSelectedBatch] = useState<BatchInfo | null>(null);
  const [batchSearchResults, setBatchSearchResults] = useState<BatchInfo[]>([]);
  const [traceabilityData, setTraceabilityData] = useState<BatchTraceability | null>(null);
  
  // View states
  const [activeTab, setActiveTab] = useState<'returns' | 'search' | 'analytics'>('returns');
  const [showFilters, setShowFilters] = useState(false);

  const RETURN_REASONS = [
    { value: 'defective', label: 'Defective Product' },
    { value: 'wrong_item', label: 'Wrong Item' },
    { value: 'damaged', label: 'Damaged in Transit' },
    { value: 'expired', label: 'Expired Product' },
    { value: 'customer_request', label: 'Customer Request' },
    { value: 'other', label: 'Other' }
  ];

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setAnalyticsLoading(true);
      
      const [returnsData, analyticsData] = await Promise.all([
        batchReturnService.getReturns(),
        batchReturnService.getReturnsAnalytics()
      ]);
      
      setReturns(returnsData.results || returnsData);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load returns data');
    } finally {
      setLoading(false);
      setAnalyticsLoading(false);
    }
  };

  const searchBatches = async () => {
    if (!batchSearchTerm.trim()) {
      toast.error('Please enter a batch number or product name');
      return;
    }
    
    try {
      setLoading(true);
      const results = await batchReturnService.searchBatches({
        batch_number: batchSearchTerm
      });
      setBatchSearchResults(results.batches || []);
      setIsBatchSearchModalOpen(true);
    } catch (error) {
      console.error('Error searching batches:', error);
      toast.error('Failed to search batches');
    } finally {
      setLoading(false);
    }
  };

  const loadBatchTraceability = async (batchId: number) => {
    try {
      setLoading(true);
      const data = await batchReturnService.getBatchTraceability(batchId);
      setTraceabilityData(data);
      setIsTraceabilityModalOpen(true);
    } catch (error) {
      console.error('Error loading batch traceability:', error);
      toast.error('Failed to load batch traceability');
    } finally {
      setLoading(false);
    }
  };

  const approveReturn = async (returnId: number) => {
    try {
      await batchReturnService.approveReturn(returnId);
      toast.success('Return approved successfully');
      loadInitialData();
    } catch (error) {
      console.error('Error approving return:', error);
      toast.error('Failed to approve return');
    }
  };

  const filteredReturns = returns.filter(returnItem => {
    const matchesSearch = !searchTerm || 
      returnItem.return_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      returnItem.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      returnItem.batch_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      returnItem.shop_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = selectedFilter === 'all' || 
      (selectedFilter === 'approved' && returnItem.approved) ||
      (selectedFilter === 'pending' && !returnItem.approved);
    
    const matchesReason = reasonFilter === 'all' || returnItem.reason === reasonFilter;
    
    return matchesSearch && matchesFilter && matchesReason;
  });

  const getStatusColor = (approved: boolean) => {
    return approved ? 'text-green-600 bg-green-50' : 'text-yellow-600 bg-yellow-50';
  };

  const getQualityStatusColor = (status: string) => {
    const colors = {
      'GOOD': 'text-green-600 bg-green-50',
      'WARNING': 'text-yellow-600 bg-yellow-50',
      'DEFECTIVE': 'text-red-600 bg-red-50',
      'RECALLED': 'text-red-600 bg-red-100'
    };
    return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-50';
  };

  if (loading && returns.length === 0) {
    return (
      <Layout title="Returns Management">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Returns Management">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Returns Management</h1>
            <p className="text-gray-600">Track and manage product returns with batch traceability</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setIsReturnModalOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
            >
              <PlusIcon className="h-5 w-5" />
              <span>New Return</span>
            </button>
            <button
              onClick={loadInitialData}
              className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 flex items-center space-x-2"
            >
              <ArrowPathIcon className="h-5 w-5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Analytics Summary */}
        {analytics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Returns</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_returns}</p>
                </div>
                <ArrowPathIcon className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Return Amount</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(analytics.total_return_amount)}</p>
                </div>
                <CurrencyDollarIcon className="h-8 w-8 text-red-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Top Reason</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {analytics.returns_by_reason[0]?.reason || 'N/A'}
                  </p>
                </div>
                <ExclamationTriangleIcon className="h-8 w-8 text-yellow-600" />
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Batch Issues</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.batch_analysis.length}</p>
                </div>
                <ChartBarIcon className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'returns', label: 'Returns', icon: ArrowPathIcon },
              { id: 'search', label: 'Batch Search', icon: MagnifyingGlassIcon },
              { id: 'analytics', label: 'Analytics', icon: ChartBarIcon }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <tab.icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'returns' && (
          <div className="space-y-4">
            {/* Search and Filters */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
              <div className="flex-1 max-w-md">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search returns..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  <FunnelIcon className="h-5 w-5" />
                  <span>Filters</span>
                  {showFilters ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                    <select
                      value={selectedFilter}
                      onChange={(e) => setSelectedFilter(e.target.value as any)}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="all">All Status</option>
                      <option value="approved">Approved</option>
                      <option value="pending">Pending</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Reason</label>
                    <select
                      value={reasonFilter}
                      onChange={(e) => setReasonFilter(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="all">All Reasons</option>
                      {RETURN_REASONS.map(reason => (
                        <option key={reason.value} value={reason.value}>{reason.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => {
                        setSelectedFilter('all');
                        setReasonFilter('all');
                        setSearchTerm('');
                      }}
                      className="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      Clear Filters
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Returns List */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Return Details
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product & Batch
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Shop & Salesman
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity & Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredReturns.map((returnItem) => (
                      <tr key={returnItem.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <div className="text-sm font-medium text-gray-900">{returnItem.return_number}</div>
                            <div className="text-sm text-gray-500">Invoice: {returnItem.invoice_number}</div>
                            <div className="text-sm text-gray-500">{formatDate(returnItem.created_at)}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <div className="text-sm font-medium text-gray-900">{returnItem.product_name}</div>
                            <div className="text-sm text-gray-500">SKU: {returnItem.product_sku}</div>
                            <div className="text-sm text-gray-500">Batch: {returnItem.batch_number}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <div className="text-sm font-medium text-gray-900">{returnItem.shop_name}</div>
                            <div className="text-sm text-gray-500">{returnItem.salesman_name}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <div className="text-sm font-medium text-gray-900">{returnItem.quantity} units</div>
                            <div className="text-sm text-gray-500">{formatCurrency(returnItem.return_amount)}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(returnItem.approved)}`}>
                            {returnItem.approved ? 'Approved' : 'Pending'}
                          </span>
                          <div className="text-xs text-gray-500 mt-1">{RETURN_REASONS.find(r => r.value === returnItem.reason)?.label}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => {
                                setSelectedReturn(returnItem);
                                setIsReturnModalOpen(true);
                              }}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            {!returnItem.approved && (
                              <button
                                onClick={() => approveReturn(returnItem.id)}
                                className="text-green-600 hover:text-green-900"
                              >
                                <CheckCircleIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Batch Search & Traceability</h3>
              <div className="flex space-x-4">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Enter batch number or product name..."
                    value={batchSearchTerm}
                    onChange={(e) => setBatchSearchTerm(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <button
                  onClick={searchBatches}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
                >
                  <MagnifyingGlassIcon className="h-5 w-5" />
                  <span>Search</span>
                </button>
              </div>
            </div>

            {batchSearchResults.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Search Results</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Batch Details
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantities
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quality
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {batchSearchResults.map((batch) => (
                        <tr key={batch.batch_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col">
                              <div className="text-sm font-medium text-gray-900">{batch.batch_number}</div>
                              <div className="text-sm text-gray-500">Mfg: {formatDate(batch.manufacturing_date)}</div>
                              <div className="text-sm text-gray-500">Exp: {formatDate(batch.expiry_date)}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col">
                              <div className="text-sm font-medium text-gray-900">{batch.product_name}</div>
                              <div className="text-sm text-gray-500">SKU: {batch.product_sku}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-col">
                              <div className="text-sm text-gray-900">Initial: {batch.initial_quantity}</div>
                              <div className="text-sm text-gray-900">Current: {batch.current_quantity}</div>
                              <div className="text-sm text-gray-900">Sold: {batch.total_sold}</div>
                              <div className="text-sm text-gray-900">Returned: {batch.total_returned}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getQualityStatusColor(batch.quality_status)}`}>
                              {batch.quality_status}
                            </span>
                            <div className="text-xs text-gray-500 mt-1">Return Rate: {batch.return_rate.toFixed(1)}%</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <button
                              onClick={() => loadBatchTraceability(batch.batch_id)}
                              className="text-blue-600 hover:text-blue-900 flex items-center space-x-1"
                            >
                              <EyeIcon className="h-4 w-4" />
                              <span>View Traceability</span>
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && analytics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Returns by Reason */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Returns by Reason</h3>
                <div className="space-y-3">
                  {analytics.returns_by_reason.map((reason, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{RETURN_REASONS.find(r => r.value === reason.reason)?.label}</div>
                        <div className="text-sm text-gray-500">{reason.count} returns</div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">{formatCurrency(reason.amount)}</div>
                        <div className="text-sm text-gray-500">{((reason.count / analytics.total_returns) * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Returned Products */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Top Returned Products</h3>
                <div className="space-y-3">
                  {analytics.top_returned_products.slice(0, 5).map((product, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">{product.product__name}</div>
                        <div className="text-sm text-gray-500">SKU: {product.product__sku}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-gray-900">{product.count} returns</div>
                        <div className="text-sm text-gray-500">{formatCurrency(product.amount)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Batch Analysis */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Problematic Batches</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Batch Number
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Returns
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Amount
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.batch_analysis.map((batch, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {batch.batch__batch_number}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {batch.batch__product__name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {batch.count}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(batch.amount)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Batch Traceability Modal */}
      {isTraceabilityModalOpen && traceabilityData && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full max-h-[90vh] overflow-y-auto">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <InformationCircleIcon className="h-6 w-6 text-blue-600 mr-2" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Batch Traceability - {traceabilityData.batch_number}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsTraceabilityModalOpen(false)}
                    className="text-gray-400 hover:text-gray-600 dark:text-gray-300 dark:hover:text-white"
                  >
                    <XCircleIcon className="h-5 w-5" />
                  </button>
                </div>
                
                {loading ? (
                  <div className="flex justify-center p-6">
                    <LoadingSpinner size="md" />
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Batch Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Batch Information</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Product:</span>
                            <span className="font-medium text-gray-900">{traceabilityData.product_name} ({traceabilityData.product_sku})</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Manufactured:</span>
                            <span className="font-medium">{formatDate(traceabilityData.manufacturing_date)}</span>
                          </div>
                          {traceabilityData.expiry_date && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Expires:</span>
                              <span className="font-medium">{formatDate(traceabilityData.expiry_date)}</span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-gray-600">Quality Status:</span>
                            <span className={`font-medium ${
                              traceabilityData.quality_status === 'GOOD' 
                                ? 'text-green-600' 
                                : traceabilityData.quality_status === 'WARNING'
                                  ? 'text-yellow-600'
                                  : 'text-red-600'
                            }`}>{traceabilityData.quality_status}</span>
                          </div>
                        </div>
                      </div>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Quantity Summary</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Initial Quantity:</span>
                            <span className="font-medium">{traceabilityData.initial_quantity}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Current Quantity:</span>
                            <span className="font-medium">{traceabilityData.current_quantity}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Sold:</span>
                            <span className="font-medium">{traceabilityData.total_sold}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Returned:</span>
                            <span className="font-medium">{traceabilityData.total_returned}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Shops Sold To - Main Focus */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="text-sm font-semibold text-gray-700 mb-3">Shops Sold To</h4>
                      {traceabilityData.shops_sold_to.length > 0 ? (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shop</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Salesman</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {traceabilityData.shops_sold_to.map((sale: BatchSaleSummary, index: number) => (
                                <tr key={`${sale.invoice_id}-${index}`} className="hover:bg-gray-50">
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{sale.shop_name}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{sale.invoice_number}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{formatDate(sale.sale_date)}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{sale.salesman_name}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs font-medium">{sale.quantity_sold}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{formatCurrency(sale.unit_price)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No sales found for this batch.</p>
                      )}
                    </div>

                    {/* Shops Returned From */}
                    {traceabilityData.shops_returned_from && traceabilityData.shops_returned_from.length > 0 && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">Returns History</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shop</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Return #</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {traceabilityData.shops_returned_from.map((returnItem: BatchReturnSummary) => (
                                <tr key={returnItem.return_id} className="hover:bg-gray-50">
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{returnItem.shop_name}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{returnItem.return_number}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{formatDate(returnItem.return_date)}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs font-medium">{returnItem.quantity_returned}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{formatCurrency(returnItem.return_amount)}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{returnItem.reason}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Salesmen Assigned */}
                    {traceabilityData.salesmen_assigned && traceabilityData.salesmen_assigned.length > 0 && (
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-semibold text-gray-700 mb-3">Salesmen Assignments</h4>
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Salesman</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assigned</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Delivered</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Returned</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Outstanding</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {traceabilityData.salesmen_assigned.map((assignment: SalesmanAssignment) => (
                                <tr key={assignment.salesman_id} className="hover:bg-gray-50">
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{assignment.salesman_name}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{assignment.assigned_quantity}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{assignment.delivered_quantity}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{assignment.returned_quantity}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">{assignment.outstanding_quantity}</td>
                                  <td className="px-4 py-2 whitespace-nowrap text-xs">
                                    <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                                      assignment.status === 'delivered' ? 'bg-green-100 text-green-800' :
                                      assignment.status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                                      assignment.status === 'pending' ? 'bg-blue-100 text-blue-800' :
                                      'bg-gray-100 text-gray-800'
                                    }`}>
                                      {assignment.status}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setIsTraceabilityModalOpen(false)}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Other Modals - ReturnModal, etc. */}
    </Layout>
  );
};
