import React, { useState, useEffect } from 'react';
import { Users, Package, Calculator, DollarSign, BarChart3, Eye, Mail, AlertTriangle, TrendingUp, ArrowRight } from 'lucide-react';
import { ReturnsSummaryCard } from './ReturnsSummaryCard';
import { deliveryService } from '../services/apiServices';

interface SalesmanCentricViewProps {
  salesmanOverview: any;
  settlementQueue: any;
  dailySummary: any;
  selectedView: 'overview' | 'balances' | 'settlement' | 'summary';
  setSelectedView: (view: 'overview' | 'balances' | 'settlement' | 'summary') => void;
  onViewSalesmanDetails: (salesmanId: number) => void;
  onSettleSalesman: (salesmanId: number, notes?: string) => void;
  isSettling: number | null;
  onShowHistory: (salesman: any) => void;
  salesmanBalances?: any;
  cashCollectionAmounts: { [key: number]: string };
  setCashCollectionAmounts: React.Dispatch<React.SetStateAction<{ [key: number]: string }>>;
  onQuickCashCollection: (salesman: any) => void;
  onShowCashCollection: (settlement: any) => void;
}

export const SalesmanCentricView: React.FC<SalesmanCentricViewProps> = ({
  salesmanOverview,
  settlementQueue,
  dailySummary,
  selectedView,
  setSelectedView,
  onViewSalesmanDetails,
  onSettleSalesman,
  isSettling,
  onShowHistory,
  salesmanBalances,
  cashCollectionAmounts,
  setCashCollectionAmounts,
  onQuickCashCollection,
  onShowCashCollection
}) => {
  const [salesmen, setSalesmen] = useState<any[]>([]);

  useEffect(() => {
    import('../services/apiServices').then(({ salesmanService }) => {
      salesmanService.getSalesmen().then((data: any) => {
        setSalesmen(data.results || data);
      }).catch(() => { });
    });
  }, []);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Salesmen</p>
              <p className="text-2xl font-bold text-gray-900">
                {salesmanOverview?.salesmen_count || 0}
              </p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Stock Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {`LKR ${(
                  (salesmanOverview?.salesmen?.reduce((sum: number, s: any) =>
                    sum + (s.stock_by_product?.reduce((pSum: number, p: any) => pSum + (p.quantity * Number(p.unit_price || 0)), 0) || 0)
                    , 0) || 0)
                ).toFixed(2)}`}
              </p>
            </div>
            <Package className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Settlements</p>
              <p className="text-2xl font-bold text-gray-900">
                {settlementQueue?.total_deliveries_pending || 0}
              </p>
            </div>
            <Calculator className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Today's Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                LKR {(dailySummary?.summary?.total_sales_revenue || 0).toFixed(2)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Returns Summary Card */}
      <ReturnsSummaryCard className="col-span-full" />

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Stock Overview', icon: Package },
            { id: 'balances', label: 'Balance Summary', icon: DollarSign },
            { id: 'settlement', label: 'Settlement History', icon: Calculator },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${selectedView === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content based on selected view */}
      {selectedView === 'overview' && (
        <SalesmanStockOverview
          data={salesmanOverview}
          onViewDetails={onViewSalesmanDetails}
          onShowHistory={onShowHistory}
        />
      )}

      {selectedView === 'balances' && (
        <SalesmanBalanceSummary
          data={salesmanBalances}
          onViewDetails={onViewSalesmanDetails}
          onShowHistory={onShowHistory}
          cashCollectionAmounts={cashCollectionAmounts}
          setCashCollectionAmounts={setCashCollectionAmounts}
          onQuickCashCollection={onQuickCashCollection}
        />
      )}

      {selectedView === 'settlement' && (
        <SettlementHistoryFull
          salesmen={salesmen}
          onShowCashCollection={onShowCashCollection}
        />
      )}
    </div>
  );
};

// Salesman Stock Overview Component
const SalesmanStockOverview: React.FC<{
  data: any;
  onViewDetails: (salesmanId: number) => void;
  onShowHistory: (salesman: any) => void;
}> = ({ data, onViewDetails, onShowHistory }) => {
  if (!data?.salesmen?.length) {
    return (
      <div className="text-center py-12">
        <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No stock distributed</h3>
        <p className="text-gray-600">No salesmen currently have allocated stock</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.salesmen.map((salesman: any) => (
        <div key={salesman.salesman_id} className="card p-6 hover:shadow-lg transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3
                  className="font-semibold text-gray-900 cursor-pointer hover:underline"
                  onClick={() => onShowHistory(salesman)}
                >
                  {salesman.salesman_name}
                </h3>
                <p className="text-sm text-gray-600 flex items-center">
                  <Mail className="w-3 h-3 mr-1" />
                  {salesman.salesman_phone}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-blue-800">Current Stock</span>
                <Package className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-lg font-bold text-blue-900">
                {salesman.total_stock_quantity} items
              </p>
              <p className="text-sm text-blue-700">
                {`LKR ${(
                  salesman.stock_by_product.reduce((sum: number, p: any) => sum + (p.quantity * Number(p.unit_price || 0)), 0)
                ).toFixed(2)}`}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-green-800">Today's Sales</span>
                <TrendingUp className="w-4 h-4 text-green-600" />
              </div>
              <p className="text-lg font-bold text-green-900">
                {salesman.today_sales_quantity} items
              </p>
              <p className="text-sm text-green-700">
                LKR {salesman.today_sales_revenue.toFixed(2)}
              </p>
            </div>

            {salesman.stock_by_product.length > 0 && (
              <div className="space-y-1">
                <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  Products ({salesman.total_products})
                </h4>
                <div className="max-h-20 overflow-y-auto space-y-1">
                  {salesman.stock_by_product.slice(0, 3).map((product: any) => (
                    <div key={product.product_id} className="flex justify-between text-xs">
                      <span className="text-gray-600 truncate">
                        {product.product_name}
                      </span>
                      <span className="text-gray-900 font-medium">
                        {product.quantity}
                      </span>
                      <span className="text-gray-700 ml-2">
                        LKR {Number(product.unit_price || 0).toFixed(2)}
                      </span>
                    </div>
                  ))}
                  {salesman.stock_by_product.length > 3 && (
                    <p className="text-xs text-gray-500">
                      +{salesman.stock_by_product.length - 3} more...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={() => onViewDetails(salesman.salesman_id)}
              className="w-full btn btn-outline btn-sm flex items-center justify-center space-x-2"
            >
              <Eye className="w-4 h-4" />
              <span>View Details</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

// Salesman Balance Summary Component
const SalesmanBalanceSummary: React.FC<{
  data: any;
  onViewDetails: (salesmanId: number) => void;
  onShowHistory: (salesman: any) => void;
  cashCollectionAmounts: { [key: number]: string };
  setCashCollectionAmounts: React.Dispatch<React.SetStateAction<{ [key: number]: string }>>;
  onQuickCashCollection: (salesman: any) => void;
}> = ({ data, onViewDetails, onShowHistory, cashCollectionAmounts, setCashCollectionAmounts, onQuickCashCollection }) => {
  if (!data?.salesman_balances?.length) {
    return (
      <div className="text-center py-12">
        <DollarSign className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No balance data available</h3>
        <p className="text-gray-600">Salesman balance information will appear here</p>
      </div>
    );
  }

  const totalBalance = data.salesman_balances.reduce((sum: number, s: any) => sum + s.current_balance, 0);

  return (
    <div className="space-y-6">
      {/* Balance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Cash Balance</p>
              <p className={`text-2xl font-bold ${totalBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                LKR {totalBalance.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">
                {totalBalance >= 0 ? 'Salesmen owe owner' : 'Owner owes salesmen'}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Current Balance</p>
              <p className="text-2xl font-bold text-green-600">
                LKR {totalBalance.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Available cash with salesmen</p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Outstanding Invoices</p>
              <p className="text-2xl font-bold text-orange-600">
                LKR {data.salesman_balances.reduce((sum: number, s: any) => sum + s.outstanding_invoices_value, 0).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">Pending collections</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Individual Salesman Balances */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.salesman_balances.map((salesman: any) => (
          <div key={salesman.salesman_id} className="card p-6 hover:shadow-lg transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${salesman.current_balance >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
                  <DollarSign className={`w-5 h-5 ${salesman.current_balance >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                </div>
                <div>
                  <h3
                    className="font-semibold text-gray-900 cursor-pointer hover:underline"
                    onClick={() => onShowHistory(salesman)}
                  >
                    {salesman.salesman_name}
                  </h3>
                  <p className="text-xs text-gray-500">
                    Last settled: {salesman.last_settlement_date
                      ? new Date(salesman.last_settlement_date).toLocaleDateString()
                      : 'Never'
                    }
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {/* Current Balance */}
              <div className={`rounded-lg p-3 ${salesman.current_balance >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                <div className="flex justify-between items-center mb-1">
                  <span className={`text-sm font-medium ${salesman.current_balance >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                    Current Balance
                  </span>
                  <DollarSign className={`w-4 h-4 ${salesman.current_balance >= 0 ? 'text-green-600' : 'text-red-600'}`} />
                </div>
                <p className={`text-lg font-bold ${salesman.current_balance >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                  LKR {salesman.current_balance.toFixed(2)}
                </p>
                <p className={`text-xs ${salesman.current_balance >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  {salesman.current_balance >= 0 ? 'Owes owner' : 'Owner owes'}
                </p>
              </div>

              {/* Cash Flow Summary */}
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-blue-800">Cash Flow</span>
                  <BarChart3 className="w-4 h-4 text-blue-600" />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs border-t border-blue-200 pt-1">
                    <span className="text-blue-700 font-medium">Current Balance:</span>
                    <span className="text-blue-900 font-bold">LKR {salesman.current_balance.toFixed(2)}</span>
                  </div>
                </div>

                {/* Cash Collection Input */}
                {salesman.current_balance > 0 && (
                  <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
                    <div className="text-xs font-medium text-green-800 mb-2">Collect Physical Cash</div>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        placeholder="Amount"
                        className="flex-1 text-xs px-2 py-1 border border-green-300 rounded focus:outline-none focus:ring-1 focus:ring-green-500"
                        step="0.01"
                        min="0"
                        max={salesman.current_balance}
                        value={cashCollectionAmounts[salesman.id] || ''}
                        onChange={(e) => setCashCollectionAmounts(prev => ({
                          ...prev,
                          [salesman.id]: e.target.value
                        }))}
                      />
                      <button
                        onClick={() => onQuickCashCollection(salesman)}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                        disabled={!cashCollectionAmounts[salesman.id] || parseFloat(cashCollectionAmounts[salesman.id]) <= 0}
                      >
                        Collect
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Outstanding Values */}
              <div className="bg-orange-50 rounded-lg p-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-orange-800">Outstanding</span>
                  <AlertTriangle className="w-4 h-4 text-orange-600" />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-orange-700">Deliveries:</span>
                    <span className="text-orange-900 font-medium">LKR {salesman.pending_deliveries_value.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-orange-700">Invoices:</span>
                    <span className="text-orange-900 font-medium">LKR {salesman.outstanding_invoices_value.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={() => onViewDetails(salesman.salesman_id)}
                className="w-full btn btn-outline btn-sm flex items-center justify-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>View Details</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pending Returns Summary */}
      {data.pending_returns && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Pending Returns Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {data.pending_returns.total_pending}
              </p>
              <p className="text-sm text-gray-600">Total Pending</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {data.pending_returns.total_quantity}
              </p>
              <p className="text-sm text-gray-600">Total Quantity</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {Object.keys(data.pending_returns.by_reason || {}).length}
              </p>
              <p className="text-sm text-gray-600">Return Reasons</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {data.pending_returns.by_salesman?.length || 0}
              </p>
              <p className="text-sm text-gray-600">Salesmen Affected</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Settlement History Full Component
const SettlementHistoryFull: React.FC<{
  salesmen: any[];
  onShowCashCollection: (settlement: any) => void;
}> = ({ salesmen, onShowCashCollection }) => {
  const [settlements, setSettlements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSettlements = async () => {
      try {
        setLoading(true);
        const allSettlements: any[] = [];
        
        for (const salesman of salesmen) {
          try {
            const data = await deliveryService.getSettlementHistory(salesman.id) as any;
            const salesmanSettlements = data.results || data;
            if (Array.isArray(salesmanSettlements)) {
              allSettlements.push(...salesmanSettlements.map((s: any) => ({
                ...s,
                salesman_name: salesman.user?.first_name + ' ' + salesman.user?.last_name || salesman.name
              })));
            }
          } catch (error) {
            console.error(`Error loading settlements for ${salesman.name}:`, error);
          }
        }
        
        // Sort by settlement date descending
        allSettlements.sort((a, b) => new Date(b.settlement_date).getTime() - new Date(a.settlement_date).getTime());
        setSettlements(allSettlements.slice(0, 50)); // Limit to 50 most recent
      } catch (error) {
        console.error('Error loading settlement history:', error);
      } finally {
        setLoading(false);
      }
    };

    if (salesmen.length > 0) {
      loadSettlements();
    }
  }, [salesmen]);

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading settlement history...</p>
      </div>
    );
  }

  if (settlements.length === 0) {
    return (
      <div className="text-center py-12">
        <Calculator className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No settlements found</h3>
        <p className="text-gray-600">Settlement history will appear here</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Settlement #
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Salesman
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Delivered
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sold
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Returned
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cash Collection
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {settlements.map((settlement: any) => (
              <tr key={settlement.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {settlement.settlement_number}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {settlement.salesman_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(settlement.settlement_date).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  LKR {Number(settlement.total_delivered_value).toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  LKR {Number(settlement.total_sold_value).toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  LKR {Number(settlement.total_returned_value).toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    settlement.status === 'completed' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {settlement.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {settlement.physical_cash_collected ? (
                    <div className="flex flex-col">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ Collected
                      </span>
                      {settlement.physical_cash_amount && (
                        <span className="text-xs text-gray-500 mt-1">
                          LKR {Number(settlement.physical_cash_amount).toFixed(2)}
                        </span>
                      )}
                      {settlement.physical_cash_collected_date && (
                        <span className="text-xs text-gray-500">
                          {new Date(settlement.physical_cash_collected_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="flex flex-col space-y-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        Pending
                      </span>
                      <button
                        onClick={() => {
                          if (!settlement.physical_cash_collected) {
                            onShowCashCollection({
                              salesman_id: settlement.salesman_id,
                              salesman_name: settlement.salesman_name,
                              current_balance: settlement.current_balance || settlement.total_cash_collected || 0
                            });
                          }
                        }}
                        className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={settlement.physical_cash_collected}
                      >
                        Collect Cash
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};