import React, { useState, useEffect, useCallback } from 'react';
import { DollarSign, TrendingUp, AlertCircle } from 'lucide-react';

interface DeliverySettlementSummaryProps {
  salesmanId: number;
  deliveries: any[];
  className?: string;
}

export const DeliverySettlementSummary: React.FC<DeliverySettlementSummaryProps> = ({
  salesmanId,
  deliveries,
  className = ''
}) => {
  const [salesmanBalance, setSalesmanBalance] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadSalesmanBalance = useCallback(async () => {
    try {
      setLoading(true);
      const { deliveryService } = await import('../services/apiServices');
      const balanceData = await deliveryService.getSalesmanBalanceSummary();
      const currentSalesmanBalance = balanceData.salesman_balances?.find(
        (s: any) => s.salesman_id === salesmanId
      );
      setSalesmanBalance(currentSalesmanBalance);
    } catch (error) {
      console.error('Error loading salesman balance:', error);
    } finally {
      setLoading(false);
    }
  }, [salesmanId]);

  useEffect(() => {
    if (salesmanId) {
      loadSalesmanBalance();
    }
  }, [salesmanId, loadSalesmanBalance]);

  const formatCurrency = (amount: number) => `LKR ${amount.toFixed(2)}`;

  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-24 rounded-lg" />;
  }

  if (!salesmanBalance) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-2 text-gray-500">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">No balance data available</span>
        </div>
      </div>
    );
  }

  const currentBalance = salesmanBalance.current_balance || 0;

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Net Position Balance
        </h3>
      </div>

      {/* Main Balance Display */}
      <div className="p-4">
        {/* Current Balance - Main Focus */}
        <div className={`rounded-lg p-4 mb-4 ${currentBalance >= 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <DollarSign className={`w-6 h-6 ${currentBalance >= 0 ? 'text-green-600' : 'text-red-600'}`} />
              <div>
                <p className={`text-sm font-medium ${currentBalance >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                  {currentBalance >= 0 ? 'Salesman Owes Owner' : 'Owner Owes Salesman'}
                </p>
                <p className={`text-2xl font-bold ${currentBalance >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                  {formatCurrency(Math.abs(currentBalance))}
                </p>
              </div>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${currentBalance >= 0
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
              }`}>
              {currentBalance >= 0 ? 'COLLECT' : 'PAY OUT'}
            </div>
          </div>
        </div>

        {/* Cash Available to Collect */}
        {currentBalance > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-blue-800">
                    Physical Cash Available
                  </p>
                  <p className="text-lg font-bold text-blue-900">
                    {formatCurrency(currentBalance)}
                  </p>
                </div>
              </div>
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                READY TO COLLECT
              </div>
            </div>
          </div>
        )}

        {/* Quick Summary */}
        <div className="grid grid-cols-1 gap-3">
          <div className="flex justify-between items-center py-2">
            <span className="text-sm font-medium text-gray-700">Current Balance</span>
            <span className={`text-sm font-bold ${currentBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {currentBalance >= 0 ? '+' : ''}{formatCurrency(currentBalance)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};