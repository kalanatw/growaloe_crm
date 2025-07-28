import React, { useState, useEffect } from 'react';
import { 
  DollarSign, 
  CreditCard, 
  Banknote, 
  Building2, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Eye,
  X
} from 'lucide-react';
import { deliveryService } from '../services/apiServices';
import toast from 'react-hot-toast';

interface InvoiceSettlementBreakdownProps {
  deliveryId: number;
  isOpen: boolean;
  onClose: () => void;
}

interface SettlementBreakdownData {
  delivery_info: {
    id: number;
    delivery_number: string;
    salesman_name: string;
    delivery_date: string;
    total_value: number;
    status: string;
  };
  settlement_summary: {
    total_invoice_amount: number;
    total_collected: number;
    outstanding_balance: number;
    collection_rate: number;
    invoice_count: number;
  };
  payment_methods: Array<{
    method: string;
    total_amount: number;
    transaction_count: number;
    settlement_count: number;
    percentage: number;
  }>;
  recent_settlements: Array<{
    type: 'transaction' | 'settlement';
    id: number;
    date: string;
    amount: number;
    payment_method: string;
    invoice_number: string;
    shop_name: string;
    reference?: string;
    notes?: string;
  }>;
}

const PaymentMethodIcon = ({ method }: { method: string }) => {
  switch (method.toLowerCase()) {
    case 'cash':
      return <Banknote className="w-4 h-4" />;
    case 'cheque':
      return <CreditCard className="w-4 h-4" />;
    case 'bank_transfer':
      return <Building2 className="w-4 h-4" />;
    default:
      return <DollarSign className="w-4 h-4" />;
  }
};

const PaymentMethodBadge = ({ method }: { method: string }) => {
  const colors = {
    cash: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
    cheque: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    bank_transfer: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    bill_to_bill: 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400',
    credit_note: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  };

  const colorClass = colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
      <PaymentMethodIcon method={method} />
      <span className="ml-1 capitalize">{method.replace('_', ' ')}</span>
    </span>
  );
};

export const InvoiceSettlementBreakdown: React.FC<InvoiceSettlementBreakdownProps> = ({
  deliveryId,
  isOpen,
  onClose
}) => {
  const [data, setData] = useState<SettlementBreakdownData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && deliveryId) {
      loadSettlementBreakdown();
    }
  }, [isOpen, deliveryId]);

  const loadSettlementBreakdown = async () => {
    try {
      setLoading(true);
      const response = await deliveryService.getDeliverySettlementBreakdown(deliveryId);
      setData(response);
    } catch (error) {
      console.error('Error loading settlement breakdown:', error);
      toast.error('Failed to load settlement breakdown');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return `LKR ${amount.toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <TrendingUp className="w-6 h-6 mr-2 text-blue-600" />
              Invoice Settlement Breakdown
            </h2>
            {data && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {data.delivery_info.delivery_number} - {data.delivery_info.salesman_name}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : data ? (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-blue-600 dark:text-blue-400">Total Invoices</p>
                      <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                        {formatCurrency(data.settlement_summary.total_invoice_amount)}
                      </p>
                      <p className="text-xs text-blue-700 dark:text-blue-300">
                        {data.settlement_summary.invoice_count} invoices
                      </p>
                    </div>
                    <DollarSign className="w-8 h-8 text-blue-600" />
                  </div>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-green-600 dark:text-green-400">Total Collected</p>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {formatCurrency(data.settlement_summary.total_collected)}
                      </p>
                      <p className="text-xs text-green-700 dark:text-green-300">
                        {data.settlement_summary.collection_rate.toFixed(1)}% collected
                      </p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </div>

                <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-orange-600 dark:text-orange-400">Outstanding</p>
                      <p className="text-2xl font-bold text-orange-900 dark:text-orange-100">
                        {formatCurrency(data.settlement_summary.outstanding_balance)}
                      </p>
                      <p className="text-xs text-orange-700 dark:text-orange-300">
                        {(100 - data.settlement_summary.collection_rate).toFixed(1)}% pending
                      </p>
                    </div>
                    <AlertCircle className="w-8 h-8 text-orange-600" />
                  </div>
                </div>

                <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-purple-600 dark:text-purple-400">Delivery Value</p>
                      <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                        {formatCurrency(data.delivery_info.total_value)}
                      </p>
                      <p className="text-xs text-purple-700 dark:text-purple-300">
                        {data.delivery_info.status}
                      </p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-purple-600" />
                  </div>
                </div>
              </div>

              {/* Collection Progress Bar */}
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">Collection Progress</h3>
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {data.settlement_summary.collection_rate.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${data.settlement_summary.collection_rate}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mt-1">
                  <span>Collected: {formatCurrency(data.settlement_summary.total_collected)}</span>
                  <span>Outstanding: {formatCurrency(data.settlement_summary.outstanding_balance)}</span>
                </div>
              </div>

              {/* Payment Methods Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Payment Methods</h3>
                  <div className="space-y-3">
                    {data.payment_methods.map((method, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-600 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <PaymentMethodBadge method={method.method} />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {formatCurrency(method.total_amount)}
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {method.transaction_count} transactions, {method.settlement_count} settlements
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {method.percentage.toFixed(1)}%
                          </p>
                          <div className="w-16 bg-gray-200 dark:bg-gray-500 rounded-full h-2 mt-1">
                            <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${method.percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Settlements */}
                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center">
                    <Clock className="w-5 h-5 mr-2" />
                    Recent Settlements
                  </h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {data.recent_settlements.length > 0 ? (
                      data.recent_settlements.map((settlement, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-600 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <PaymentMethodBadge method={settlement.payment_method} />
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                settlement.type === 'transaction' 
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                                  : 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                              }`}>
                                {settlement.type}
                              </span>
                            </div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">
                              {settlement.invoice_number} - {settlement.shop_name}
                            </p>
                            <p className="text-xs text-gray-600 dark:text-gray-400">
                              {formatDate(settlement.date)}
                              {settlement.reference && ` • Ref: ${settlement.reference}`}
                            </p>
                            {settlement.notes && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                {settlement.notes}
                              </p>
                            )}
                          </div>
                          <div className="text-right ml-4">
                            <p className="text-sm font-bold text-gray-900 dark:text-white">
                              {formatCurrency(settlement.amount)}
                            </p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>No recent settlements found</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Failed to load settlement breakdown</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};