import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { 
  Package, 
  Plus, 
  Minus, 
  AlertTriangle, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Eye
} from 'lucide-react';
import { productService } from '../services/apiServices';
import { stockManagementService } from '../services/stockManagementService';
import { Product } from '../types';
import { formatCurrency } from '../utils/currency';
import { getCardAmountClass } from '../utils/responsiveFonts';
import toast from 'react-hot-toast';

interface StockSummaryItem {
  product_id: number;
  product_name: string;
  product_sku: string;
  total_stock: number;
  allocated_stock: number;
  available_stock: number;
  salesmen_count: number;
}

interface BatchInfo {
  id: number;
  batch_number: string;
  current_quantity: number;
  original_quantity: number;
  expiry_date: string | null;
  cost_per_unit: number;
  created_at: string;
  is_active: boolean;
}

export const StockManagementPage: React.FC = () => {
  const [stockSummary, setStockSummary] = useState<StockSummaryItem[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [batchDetails, setBatchDetails] = useState<BatchInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedStockItem, setSelectedStockItem] = useState<StockSummaryItem | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showReduceModal, setShowReduceModal] = useState(false);
  const [showBatchDetailsModal, setShowBatchDetailsModal] = useState(false);
  const [stockOperation, setStockOperation] = useState({
    quantity: '',
    notes: '',
    reason: 'adjustment' as 'adjustment' | 'damage' | 'return',
    batch_number: '',
    expiry_date: '',
    cost_per_unit: ''
  });

  const resetStockOperation = () => {
    setStockOperation({
      quantity: '',
      notes: '',
      reason: 'adjustment',
      batch_number: '',
      expiry_date: '',
      cost_per_unit: ''
    });
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setIsLoading(true);
      
      // Load stock summary (batch-based) and products
      const [stockData, productsData] = await Promise.all([
        productService.getProductStockSummary(),
        productService.getProducts()
      ]);
      
      setStockSummary(stockData.results || stockData);
      setProducts(productsData.results || productsData);
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Failed to load products');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddStock = async () => {
    if (!selectedProduct || !stockOperation.quantity) {
      toast.error('Please enter a valid quantity');
      return;
    }

    try {
      console.log('Attempting to add stock to product:', selectedProduct.id);
      const addStockData: any = {
        quantity: parseInt(stockOperation.quantity),
        notes: stockOperation.notes
      };

      // Add batch fields if provided
      if (stockOperation.batch_number) {
        addStockData.batch_number = stockOperation.batch_number;
      }
      if (stockOperation.expiry_date) {
        addStockData.expiry_date = stockOperation.expiry_date;
      }
      if (stockOperation.cost_per_unit) {
        addStockData.cost_per_unit = parseFloat(stockOperation.cost_per_unit);
      }

      const result = await stockManagementService.addStock(selectedProduct.id, addStockData);

      console.log('Add stock result:', result);
      
      if (result.success) {
        toast.success(result.message);
        setShowAddModal(false);
        resetStockOperation();
        loadProducts();
      } else {
        toast.error(result.message || 'Failed to add stock');
      }
    } catch (error: any) {
      console.error('Add stock error:', error);
      toast.error(error.response?.data?.error || error.message || 'Failed to add stock');
    }
  };

  const handleReduceStock = async () => {
    if (!selectedProduct || !stockOperation.quantity) {
      toast.error('Please enter a valid quantity');
      return;
    }

    try {
      const result = await stockManagementService.reduceStock(selectedProduct.id, {
        quantity: parseInt(stockOperation.quantity),
        notes: stockOperation.notes,
        reason: stockOperation.reason
      });

      toast.success(result.message);
      setShowReduceModal(false);
      resetStockOperation();
      loadProducts();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reduce stock');
    }
  };

  const loadBatchDetails = async (productId: number) => {
    try {
      const response = await fetch(`/api/products/batches/?product=${productId}&is_active=true`);
      const data = await response.json();
      setBatchDetails(data.results || data);
    } catch (error) {
      console.error('Error loading batch details:', error);
      toast.error('Failed to load batch details');
    }
  };

  const handleViewBatches = async (stockItem: StockSummaryItem) => {
    setSelectedStockItem(stockItem);
    await loadBatchDetails(stockItem.product_id);
    setShowBatchDetailsModal(true);
  };

  const lowStockProducts = stockSummary.filter(s => {
    const product = products.find(p => p.id === s.product_id);
    return product && s.available_stock <= product.min_stock_level;
  });
  const totalStockValue = stockSummary.reduce((sum, s) => {
    const product = products.find(p => p.id === s.product_id);
    return sum + (s.available_stock * (product?.base_price || 0));
  }, 0);

  if (isLoading) {
    return (
      <Layout title="Stock Management">
        <LoadingCard title="Loading stock data..." />
      </Layout>
    );
  }

  return (
    <Layout title="Stock Management">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-3">
            <Package className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Stock Management
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage inventory levels and track stock movements
              </p>
            </div>
          </div>
          
          <button
            onClick={loadProducts}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                <Package className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Products
                </p>
                <p className={`${getCardAmountClass(stockSummary.length)} text-gray-900 dark:text-white`}>
                  {stockSummary.length}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Stock Value
                </p>
                <p className={`${getCardAmountClass(totalStockValue)} text-gray-900 dark:text-white`}>
                  {formatCurrency(totalStockValue)}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-red-500">
                <AlertTriangle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Low Stock Alerts
                </p>
                <p className={`${getCardAmountClass(lowStockProducts.length)} ${
                  lowStockProducts.length > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'
                }`}>
                  {lowStockProducts.length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Low Stock Alerts */}
        {lowStockProducts.length > 0 && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-4 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Low Stock Alerts
            </h3>
            <div className="space-y-2">
              {lowStockProducts.map(stockItem => {
                const product = products.find(p => p.id === stockItem.product_id);
                return (
                  <div key={stockItem.product_id} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{stockItem.product_name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Current: {stockItem.available_stock} | Minimum: {product?.min_stock_level || 0}
                      </p>
                    </div>
                    {product && (
                      <button
                        onClick={() => {
                          setSelectedProduct(product);
                          setShowAddModal(true);
                        }}
                        className="btn-primary text-sm"
                      >
                        Add Stock
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Products Table */}
        <div className="card">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Product Inventory
            </h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Available Stock
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Allocated Stock
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Min Level
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {stockSummary.map((stockItem) => {
                  const product = products.find(p => p.id === stockItem.product_id);
                  const isLowStock = product && stockItem.available_stock <= product.min_stock_level;
                  return (
                    <tr key={stockItem.product_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {stockItem.product_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            SKU: {stockItem.product_sku}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className={`text-sm font-medium ${
                          isLowStock
                            ? 'text-red-600 dark:text-red-400' 
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {stockItem.available_stock}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                        {stockItem.allocated_stock}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                        {product?.min_stock_level || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900 dark:text-white">
                        {formatCurrency(stockItem.available_stock * (product?.base_price || 0))}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={() => handleViewBatches(stockItem)}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="View Batches"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {product && (
                            <>
                              <button
                                onClick={() => {
                                  setSelectedProduct(product);
                                  setShowAddModal(true);
                                }}
                                className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                                title="Add Stock"
                              >
                                <Plus className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => {
                                  setSelectedProduct(product);
                                  setShowReduceModal(true);
                                }}
                                className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                                title="Reduce Stock"
                              >
                                <Minus className="h-4 w-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Add Stock Modal */}
        {showAddModal && selectedProduct && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Add Stock: {selectedProduct.name}
                    </h3>
                    <button
                      onClick={() => {
                        setShowAddModal(false);
                        resetStockOperation();
                      }}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ×
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="label">Quantity to Add</label>
                      <input
                        type="number"
                        value={stockOperation.quantity}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, quantity: e.target.value }))}
                        className="input"
                        placeholder="Enter quantity"
                        min="1"
                      />
                    </div>

                    <div>
                      <label className="label">Batch Number (Optional)</label>
                      <input
                        type="text"
                        value={stockOperation.batch_number}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, batch_number: e.target.value }))}
                        className="input"
                        placeholder="Auto-generated if not provided"
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        Leave empty to auto-generate batch number
                      </p>
                    </div>

                    <div>
                      <label className="label">Expiry Date (Optional)</label>
                      <input
                        type="date"
                        value={stockOperation.expiry_date}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, expiry_date: e.target.value }))}
                        className="input"
                      />
                    </div>

                    <div>
                      <label className="label">Cost per Unit (Optional)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={stockOperation.cost_per_unit}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, cost_per_unit: e.target.value }))}
                        className="input"
                        placeholder={`Default: ${selectedProduct.cost_price}`}
                        min="0"
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        Uses product cost price if not specified: {formatCurrency(selectedProduct.cost_price)}
                      </p>
                    </div>

                    <div>
                      <label className="label">Notes (Optional)</label>
                      <textarea
                        value={stockOperation.notes}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, notes: e.target.value }))}
                        className="input"
                        rows={3}
                        placeholder="Add notes about this stock addition..."
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    onClick={handleAddStock}
                    className="btn-primary w-full sm:ml-3 sm:w-auto"
                  >
                    Add Stock
                  </button>
                  <button
                    onClick={() => {
                      setShowAddModal(false);
                      resetStockOperation();
                    }}
                    className="btn-secondary mt-3 w-full sm:mt-0 sm:w-auto"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reduce Stock Modal */}
        {showReduceModal && selectedProduct && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Reduce Stock: {selectedProduct.name}
                    </h3>
                    <button
                      onClick={() => {
                        setShowReduceModal(false);
                        resetStockOperation();
                      }}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ×
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="label">Quantity to Reduce</label>
                      <input
                        type="number"
                        value={stockOperation.quantity}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, quantity: e.target.value }))}
                        className="input"
                        placeholder="Enter quantity"
                        min="1"
                        max={stockSummary.find(s => s.product_id === selectedProduct.id)?.available_stock || 0}
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        Current stock: {stockSummary.find(s => s.product_id === selectedProduct.id)?.available_stock || 0}
                      </p>
                    </div>

                    <div>
                      <label className="label">Reason</label>
                      <select
                        value={stockOperation.reason}
                        onChange={(e) => setStockOperation(prev => ({ 
                          ...prev, 
                          reason: e.target.value as 'adjustment' | 'damage' | 'return'
                        }))}
                        className="input"
                      >
                        <option value="adjustment">Stock Adjustment</option>
                        <option value="damage">Damage/Loss</option>
                        <option value="return">Return</option>
                      </select>
                    </div>

                    <div>
                      <label className="label">Notes (Optional)</label>
                      <textarea
                        value={stockOperation.notes}
                        onChange={(e) => setStockOperation(prev => ({ ...prev, notes: e.target.value }))}
                        className="input"
                        rows={3}
                        placeholder="Add notes about this stock reduction..."
                      />
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    onClick={handleReduceStock}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg w-full sm:ml-3 sm:w-auto"
                  >
                    Reduce Stock
                  </button>
                  <button                      onClick={() => {
                        setShowReduceModal(false);
                        resetStockOperation();
                      }}
                    className="btn-secondary mt-3 w-full sm:mt-0 sm:w-auto"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Batch Details Modal */}
        {showBatchDetailsModal && selectedStockItem && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Batch Details: {selectedStockItem.product_name}
                    </h3>
                    <button
                      onClick={() => setShowBatchDetailsModal(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      ×
                    </button>
                  </div>

                  <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700 dark:text-gray-300">Total Stock:</span>
                        <span className="ml-2 text-gray-900 dark:text-white">{selectedStockItem.total_stock}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700 dark:text-gray-300">Available:</span>
                        <span className="ml-2 text-green-600 dark:text-green-400">{selectedStockItem.available_stock}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700 dark:text-gray-300">Allocated:</span>
                        <span className="ml-2 text-orange-600 dark:text-orange-400">{selectedStockItem.allocated_stock}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700 dark:text-gray-300">Salesmen:</span>
                        <span className="ml-2 text-blue-600 dark:text-blue-400">{selectedStockItem.salesmen_count}</span>
                      </div>
                    </div>
                  </div>

                  {batchDetails.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-800">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Batch Number
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Current Qty
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Original Qty
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Cost/Unit
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Expiry Date
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                              Created
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                          {batchDetails.map((batch) => (
                            <tr key={batch.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                                {batch.batch_number}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 dark:text-white">
                                {batch.current_quantity}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                                {batch.original_quantity}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                                {formatCurrency(batch.cost_per_unit)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500 dark:text-gray-400">
                                {batch.expiry_date ? new Date(batch.expiry_date).toLocaleDateString() : 'No expiry'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-center text-sm text-gray-500 dark:text-gray-400">
                                {new Date(batch.created_at).toLocaleDateString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 dark:text-gray-400">No batches found for this product</p>
                    </div>
                  )}
                </div>

                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    onClick={() => setShowBatchDetailsModal(false)}
                    className="btn-secondary w-full sm:w-auto"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
