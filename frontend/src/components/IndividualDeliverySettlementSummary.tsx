import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { deliveryService } from '../services/apiServices';

interface SettlementSummaryData {
  delivery_metrics: {
    delivery_value: number;
    delivery_date: string;
    delivery_status: string;
    total_items: number;
  };
  cash_flow: {
    total_cash_collected: number;
    cash_to_settle_to_owner: number;
    outstanding_from_customers: number;
    collection_rate_percentage: number;
  };
  product_tracking: {
    product_value_in_circulation: number;
    circulation_percentage: number;
    conversion_rate: number;
  };
  invoice_breakdown: {
    total_invoices: number;
    total_invoice_amount: number;
    paid_invoices: number;
    pending_invoices: number;
    partial_invoices: number;
  };
  daily_settlements: Array<{
    date: string;
    cash_collected: number;
    invoice_count: number;
    settlement_due: number;
  }>;
  payment_methods: Array<{
    method: string;
    amount: number;
    transaction_count: number;
    percentage: number;
  }>;
}

interface IndividualDeliverySettlementSummaryProps {
  deliveryId: number;
  className?: string;
}

export const IndividualDeliverySettlementSummary: React.FC<IndividualDeliverySettlementSummaryProps> = ({ 
  deliveryId, 
  className = '' 
}) => {
  const [summaryData, setSummaryData] = useState<SettlementSummaryData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const loadSettlementSummary = async () => {
    try {
      setLoading(true);
      const response = await deliveryService.getDeliverySettlementSummary(deliveryId);
      setSummaryData(response.settlement_summary);
    } catch (error) {
      console.error('Error loading settlement summary:', error);
      toast.error('Failed to load settlement summary');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (deliveryId) {
      loadSettlementSummary();
    }
  }, [deliveryId]);

  const formatCurrency = (amount: number) => `LKR ${amount.toFixed(2)}`;

  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-32 rounded-lg" />;
  }

  if (!summaryData) {
    return null;
  }

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Settlement Summary
          </h3>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          {/* Delivery Investment */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-blue-800 mb-1">
              Product Investment
            </div>
            <div className="text-lg font-bold text-blue-900">
              {formatCurrency(summaryData.delivery_metrics.delivery_value)}
            </div>
            <div className="text-xs text-blue-700">
              {summaryData.delivery_metrics.total_items} items delivered
            </div>
          </div>

          {/* Cash to Settle */}
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-green-800 mb-1">
              Cash to Settle
            </div>
            <div className="text-lg font-bold text-green-900">
              {formatCurrency(summaryData.cash_flow.cash_to_settle_to_owner)}
            </div>
            <div className="text-xs text-green-700">
              {summaryData.cash_flow.collection_rate_percentage.toFixed(1)}% collected
            </div>
          </div>

          {/* Product Value in Circulation */}
          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-orange-800 mb-1">
              Products in Circulation
            </div>
            <div className="text-lg font-bold text-orange-900">
              {formatCurrency(summaryData.product_tracking.product_value_in_circulation)}
            </div>
            <div className="text-xs text-orange-700">
              {summaryData.product_tracking.circulation_percentage.toFixed(1)}% remaining
            </div>
          </div>

          {/* Outstanding from Customers */}
          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="text-xs font-medium text-purple-800 mb-1">
              Outstanding from Customers
            </div>
            <div className="text-lg font-bold text-purple-900">
              {formatCurrency(summaryData.cash_flow.outstanding_from_customers)}
            </div>
            <div className="text-xs text-purple-700">
              {summaryData.invoice_breakdown.pending_invoices + 
               summaryData.invoice_breakdown.partial_invoices} pending
            </div>
          </div>
        </div>

        {/* Collection Progress */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Collection Progress</span>
            <span>{summaryData.cash_flow.collection_rate_percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full"
              style={{ 
                width: `${Math.min(summaryData.cash_flow.collection_rate_percentage, 100)}%` 
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>
              Collected: {formatCurrency(summaryData.cash_flow.total_cash_collected)}
            </span>
            <span>
              In Circulation: {formatCurrency(summaryData.product_tracking.product_value_in_circulation)}
            </span>
          </div>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="space-y-4 border-t border-gray-200 pt-4">
            {/* Daily Settlements */}
            {summaryData.daily_settlements.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Daily Settlement Due
                </h4>
                <div className="space-y-2">
                  {summaryData.daily_settlements.map((day, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <div>
                        <span className="text-sm font-medium">
                          {new Date(day.date).toLocaleDateString()}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          {day.invoice_count} invoices
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-green-600">
                          {formatCurrency(day.settlement_due)}
                        </div>
                        <div className="text-xs text-gray-500">
                          to settle
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Payment Methods */}
            {summaryData.payment_methods.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Payment Methods
                </h4>
                <div className="space-y-2">
                  {summaryData.payment_methods.map((method, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium capitalize">
                          {method.method.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-gray-500">
                          {method.transaction_count} transactions
                        </span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium">
                          {formatCurrency(method.amount)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {method.percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};