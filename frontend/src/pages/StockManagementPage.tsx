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
  RefreshCw
} from 'lucide-react';
import { productService } from '../services/apiServices';
import { stockManagementService } from '../services/stockManagementService';
import { Product } from '../types';
import { formatCurrency } from '../utils/currency';
import { getCardAmountClass } from '../utils/responsiveFonts';
import toast from 'react-hot-toast';

interface StockItem extends Product {
  low_stock_alert?: boolean;
}

export const StockManagementPage: React.FC = () => {
  const [products, setProducts] = useState<StockItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showReduceModal, setShowReduceModal] = useState(false);
  const [stockOperation, setStockOperation] = useState({
    quantity: '',
    notes: '',
    reason: 'adjustment' as 'adjustment' | 'damage' | 'return'
  });

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      setIsLoading(true);
      const data = await productService.getProducts();
      setProducts(data.results || data);
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
      const result = await stockManagementService.addStock(selectedProduct.id, {
        quantity: parseInt(stockOperation.quantity),
        notes: stockOperation.notes
      });

      console.log('Add stock result:', result);
      
      if (result.success) {
        toast.success(result.message);
        setShowAddModal(false);
        setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
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
      setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
      loadProducts();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to reduce stock');
    }
  };

  const lowStockProducts = products.filter(p => p.stock_quantity <= p.min_stock_level);
  const totalStockValue = products.reduce((sum, p) => sum + (p.stock_quantity * p.base_price), 0);

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
                <p className={`${getCardAmountClass(products.length)} text-gray-900 dark:text-white`}>
                  {products.length}
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
              {lowStockProducts.map(product => (
                <div key={product.id} className="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{product.name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Current: {product.stock_quantity} | Minimum: {product.min_stock_level}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedProduct(product);
                      setShowAddModal(true);
                    }}
                    className="btn-primary text-sm"
                  >
                    Add Stock
                  </button>
                </div>
              ))}
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
                    Stock Qty
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
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {product.name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          SKU: {product.sku}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className={`text-sm font-medium ${
                        product.stock_quantity <= product.min_stock_level 
                          ? 'text-red-600 dark:text-red-400' 
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {product.stock_quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                      {product.min_stock_level}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900 dark:text-white">
                      {formatCurrency(product.stock_quantity * product.base_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center space-x-2">
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
                      </div>
                    </td>
                  </tr>
                ))}
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
                        setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
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
                      setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
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
                        setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
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
                        max={selectedProduct.stock_quantity}
                      />
                      <p className="text-sm text-gray-500 mt-1">
                        Current stock: {selectedProduct.stock_quantity}
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
                  <button
                    onClick={() => {
                      setShowReduceModal(false);
                      setStockOperation({ quantity: '', notes: '', reason: 'adjustment' });
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
      </div>
    </Layout>
  );
};
