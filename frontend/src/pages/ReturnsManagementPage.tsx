import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { Package, CheckCircle, XCircle, Clock, Search, Filter, RefreshCw, RotateCcw } from 'lucide-react';
import { getCardAmountClass } from '../utils/responsiveFonts';
import toast from 'react-hot-toast';
import returnService, { ProductReturn, PendingReturnsSummary } from '../services/returnService';

const RETURN_REASONS = {
  unsold: 'Unsold Stock',
  damaged: 'Damaged Product',
  expired: 'Expired Product',
  defective: 'Defective Product',
  customer_return: 'Customer Return',
  other: 'Other Reason'
};

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  disposed: 'bg-red-100 text-red-800'
};

export const ReturnsManagementPage: React.FC = () => {
  const [returns, setReturns] = useState<ProductReturn[]>([]);
  const [summary, setSummary] = useState<PendingReturnsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedReturns, setSelectedReturns] = useState<number[]>([]);
  const [filters, setFilters] = useState({
    status: '',
    return_reason: '',
    search: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [processingReturn, setProcessingReturn] = useState<number | null>(null);

  useEffect(() => {
    loadReturns();
    loadSummary();
  }, [filters]);

  const loadReturns = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filters.status) params.status = filters.status;
      if (filters.return_reason) params.return_reason = filters.return_reason;
      if (filters.search) params.search = filters.search;
      const data = await returnService.getReturns(params);
      setReturns(data.results || data);
    } catch (error) {
      console.error('Error loading returns:', error);
      toast.error('Failed to load returns');
    } finally {
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    try {
      const data = await returnService.getPendingReturnsSummary();
      setSummary(data);
    } catch (error) {
      console.error('Error loading summary:', error);
    }
  };

  const processReturn = async (returnId: number, action: 'approve' | 'dispose', notes = '') => {
    try {
      setProcessingReturn(returnId);
      let response;
      if (action === 'approve') {
        response = await returnService.approveReturn(returnId, notes);
      } else {
        response = await returnService.disposeReturn(returnId, notes);
      }
      toast.success(`Return ${action}d successfully`);
      loadReturns();
      loadSummary();
    } catch (error: any) {
      console.error(`Error ${action}ing return:`, error);
      toast.error(error?.message || `Failed to ${action} return`);
    } finally {
      setProcessingReturn(null);
    }
  };

  const bulkProcess = async (action: 'approve' | 'dispose', notes = '') => {
    if (selectedReturns.length === 0) {
      toast.error('Please select returns to process');
      return;
    }
    try {
      const response = await returnService.bulkProcessReturns({
        return_ids: selectedReturns,
        action,
        processing_notes: notes
      });
      toast.success(response.message);
      setSelectedReturns([]);
      loadReturns();
      loadSummary();
    } catch (error: any) {
      console.error(`Error bulk ${action}ing returns:`, error);
      toast.error(error?.message || `Failed to ${action} returns`);
    }
  };

  const toggleSelectReturn = (returnId: number) => {
    setSelectedReturns(prev =>
      prev.includes(returnId)
        ? prev.filter(id => id !== returnId)
        : [...prev, returnId]
    );
  };

  const selectAllPending = () => {
    const pendingReturns = returns.filter(r => r.status === 'pending').map(r => r.id);
    setSelectedReturns(pendingReturns);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Layout title="Returns Management">
        <LoadingCard title="Loading returns data..." />
      </Layout>
    );
  }

  return (
    <Layout title="Returns Management">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-3">
            <RotateCcw className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Returns Management
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage product returns and approvals
              </p>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn-secondary flex items-center space-x-2"
            >
              <Filter className="h-4 w-4" />
              <span>Filters</span>
            </button>
            <button
              onClick={() => { loadReturns(); loadSummary(); }}
              className="btn-secondary flex items-center space-x-2"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="card p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-3 rounded-lg bg-yellow-500">
                  <Clock className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Pending Returns
                  </p>
                  <p className={`${getCardAmountClass(summary.total_pending)} text-gray-900 dark:text-white`}>
                    {summary.total_pending}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-3 rounded-lg bg-orange-500">
                  <Package className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Pending Quantity
                  </p>
                  <p className={`${getCardAmountClass(summary.total_quantity)} text-gray-900 dark:text-white`}>
                    {summary.total_quantity}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                  <Package className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Unsold Returns
                  </p>
                  <p className={`${getCardAmountClass(summary.by_reason.unsold?.count || 0)} text-gray-900 dark:text-white`}>
                    {summary.by_reason.unsold?.count || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="card p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0 p-3 rounded-lg bg-red-500">
                  <XCircle className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4 flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Damaged Returns
                  </p>
                  <p className={`${getCardAmountClass(summary.by_reason.damaged?.count || 0)} text-gray-900 dark:text-white`}>
                    {summary.by_reason.damaged?.count || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        {showFilters && (
          <div className="card p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                  className="input-field"
                >
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="disposed">Disposed</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Return Reason</label>
                <select
                  value={filters.return_reason}
                  onChange={(e) => setFilters(prev => ({ ...prev, return_reason: e.target.value }))}
                  className="input-field"
                >
                  <option value="">All Reasons</option>
                  {Object.entries(RETURN_REASONS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                    placeholder="Search products, salesmen..."
                    className="input-field pl-10"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Actions */}
        {selectedReturns.length > 0 && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-800 dark:text-blue-200">
                {selectedReturns.length} return(s) selected
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={() => bulkProcess('approve')}
                  className="btn-primary bg-green-600 hover:bg-green-700 text-white px-3 py-1 text-sm"
                >
                  Approve Selected
                </button>
                <button
                  onClick={() => bulkProcess('dispose')}
                  className="btn-primary bg-red-600 hover:bg-red-700 text-white px-3 py-1 text-sm"
                >
                  Dispose Selected
                </button>
                <button
                  onClick={() => setSelectedReturns([])}
                  className="btn-secondary px-3 py-1 text-sm"
                >
                  Clear Selection
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Returns Table */}
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Product Returns</h3>
              <button
                onClick={selectAllPending}
                className="text-sm text-primary-600 hover:text-primary-800 dark:text-primary-400 dark:hover:text-primary-300"
              >
                Select All Pending
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedReturns.length === returns.filter(r => r.status === 'pending').length}
                      onChange={selectAllPending}
                      className="rounded border-gray-300 dark:border-gray-600"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Salesman
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Return Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {returns.map((returnItem) => (
                  <tr key={returnItem.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {returnItem.status === 'pending' && (
                        <input
                          type="checkbox"
                          checked={selectedReturns.includes(returnItem.id)}
                          onChange={() => toggleSelectReturn(returnItem.id)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {returnItem.product_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          SKU: {returnItem.product_sku} | Batch: {returnItem.batch_number}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900 dark:text-white">{returnItem.salesman_name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Delivery: {returnItem.delivery_number}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {returnItem.return_quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 dark:text-white">
                        {RETURN_REASONS[returnItem.return_reason as keyof typeof RETURN_REASONS]}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${STATUS_COLORS[returnItem.status]}`}>
                        {returnItem.status.charAt(0).toUpperCase() + returnItem.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {formatDate(returnItem.return_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {returnItem.status === 'pending' ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => processReturn(returnItem.id, 'approve')}
                            disabled={processingReturn === returnItem.id}
                            className="text-green-600 hover:text-green-900 disabled:opacity-50 dark:text-green-400 dark:hover:text-green-300"
                            title="Approve Return"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => processReturn(returnItem.id, 'dispose')}
                            disabled={processingReturn === returnItem.id}
                            className="text-red-600 hover:text-red-900 disabled:opacity-50 dark:text-red-400 dark:hover:text-red-300"
                            title="Dispose Return"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="text-gray-400 dark:text-gray-500">
                          {returnItem.processed_date && (
                            <span>Processed {formatDate(returnItem.processed_date)}</span>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {returns.length === 0 && (
            <div className="text-center py-12">
              <Package className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No returns found</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                No product returns match your current filters.
              </p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};