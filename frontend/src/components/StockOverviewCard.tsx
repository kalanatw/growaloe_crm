import React, { useState, useEffect } from 'react';
import { Package, TrendingUp, TrendingDown, AlertTriangle, Users } from 'lucide-react';

interface StockOverview {
  product_id: number;
  product_name: string;
  product_sku: string;
  total_stock: number;
  allocated_stock: number;
  available_stock: number;
  pending_returns: number;
  approved_returns_today: number;
  disposed_returns_today: number;
  sales_today: number;
  salesmen_count: number;
  low_stock_alert: boolean;
  salesman_breakdown: Array<{
    salesman_id: number;
    salesman_name: string;
    outstanding_quantity: number;
    pending_returns: number;
  }>;
}

interface StockOverviewCardProps {
  productId: number;
  className?: string;
}

export const StockOverviewCard: React.FC<StockOverviewCardProps> = ({ 
  productId, 
  className = '' 
}) => {
  const [overview, setOverview] = useState<StockOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStockOverview();
  }, [productId]);

  const loadStockOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/products/products/${productId}/stock_overview/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOverview(data);
      } else {
        setError('Failed to load stock overview');
      }
    } catch (error) {
      console.error('Error loading stock overview:', error);
      setError('Failed to load stock overview');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-center text-red-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p>{error || 'Failed to load stock overview'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{overview.product_name}</h3>
          <p className="text-sm text-gray-600">SKU: {overview.product_sku}</p>
        </div>
        {overview.low_stock_alert && (
          <div className="flex items-center text-red-600">
            <AlertTriangle className="w-5 h-5 mr-1" />
            <span className="text-sm font-medium">Low Stock</span>
          </div>
        )}
      </div>

      {/* Stock Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mx-auto mb-2">
            <Package className="w-6 h-6 text-blue-600" />
          </div>
          <p className="text-2xl font-semibold text-gray-900">{overview.total_stock}</p>
          <p className="text-xs text-gray-600">Total Stock</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mx-auto mb-2">
            <TrendingUp className="w-6 h-6 text-green-600" />
          </div>
          <p className="text-2xl font-semibold text-gray-900">{overview.available_stock}</p>
          <p className="text-xs text-gray-600">Available</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-lg mx-auto mb-2">
            <TrendingDown className="w-6 h-6 text-yellow-600" />
          </div>
          <p className="text-2xl font-semibold text-gray-900">{overview.pending_returns}</p>
          <p className="text-xs text-gray-600">Pending Returns</p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mx-auto mb-2">
            <Users className="w-6 h-6 text-purple-600" />
          </div>
          <p className="text-2xl font-semibold text-gray-900">{overview.salesmen_count}</p>
          <p className="text-xs text-gray-600">Salesmen</p>
        </div>
      </div>

      {/* Today's Activity */}
      <div className="border-t pt-4 mb-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Today's Activity</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-lg font-semibold text-green-600">{overview.approved_returns_today}</p>
            <p className="text-xs text-gray-600">Returns Approved</p>
          </div>
          <div>
            <p className="text-lg font-semibold text-red-600">{overview.disposed_returns_today}</p>
            <p className="text-xs text-gray-600">Returns Disposed</p>
          </div>
          <div>
            <p className="text-lg font-semibold text-blue-600">{overview.sales_today}</p>
            <p className="text-xs text-gray-600">Units Sold</p>
          </div>
        </div>
      </div>

      {/* Salesman Breakdown */}
      {overview.salesman_breakdown.length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Stock Distribution</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {overview.salesman_breakdown.map((salesman) => (
              <div key={salesman.salesman_id} className="flex items-center justify-between text-sm">
                <span className="text-gray-900">{salesman.salesman_name}</span>
                <div className="flex space-x-4 text-xs">
                  <span className="text-blue-600">
                    Outstanding: {salesman.outstanding_quantity}
                  </span>
                  {salesman.pending_returns > 0 && (
                    <span className="text-yellow-600">
                      Pending: {salesman.pending_returns}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stock Status Bar */}
      <div className="mt-4 pt-4 border-t">
        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
          <span>Stock Utilization</span>
          <span>{Math.round((overview.allocated_stock / overview.total_stock) * 100)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full" 
            style={{ 
              width: `${Math.min((overview.allocated_stock / overview.total_stock) * 100, 100)}%` 
            }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>Available: {overview.available_stock}</span>
          <span>Allocated: {overview.allocated_stock}</span>
        </div>
      </div>
    </div>
  );
};