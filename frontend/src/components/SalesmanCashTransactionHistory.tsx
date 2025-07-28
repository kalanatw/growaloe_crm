import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

interface CashTransaction {
  id: number;
  transaction_type: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string;
  reference_type: string | null;
  reference_id: string | null;
  notes: string | null;
  created_at: string;
  created_by: number | null;
  invoice: any | null;
  cash_collection: any | null;
}

interface SalesmanCashTransactionHistoryProps {
  salesmanId: number;
  salesmanName: string;
  currentBalance: number;
  isOpen: boolean;
  onClose: () => void;
}

export const SalesmanCashTransactionHistory: React.FC<SalesmanCashTransactionHistoryProps> = ({
  salesmanId,
  salesmanName,
  currentBalance,
  isOpen,
  onClose
}) => {
  const [transactions, setTransactions] = useState<CashTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTransactionHistory = async () => {
    try {
      setIsLoading(true);
      // Fetch cash transactions for the salesman
      const response = await apiClient.get<CashTransaction[]>(`/api/accounts/salesmen/${salesmanId}/cash-transactions/`);
      setTransactions(response);
    } catch (error) {
      console.error('Error fetching transaction history:', error);
      toast.error('Failed to fetch transaction history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTransactionHistory();
    }
  }, [salesmanId, isOpen]);

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTransactionTypeLabel = (type: string) => {
    switch (type) {
      case 'collection':
        return 'Cash Collection from Customer';
      case 'settlement':
        return 'Settlement with Owner';
      case 'expense':
        return 'Delivery Expense';
      case 'advance':
        return 'Advance from Owner';
      case 'adjustment':
        return 'Balance Adjustment';
      default:
        return type;
    }
  };

  const getTransactionTypeColor = (type: string, amount: number) => {
    if (amount > 0) {
      return 'text-green-600'; // Credit (money in)
    } else {
      return 'text-red-600'; // Debit (money out)
    }
  };

  const getTransactionIcon = (type: string, amount: number) => {
    if (amount > 0) {
      return (
        <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      );
    } else {
      return (
        <svg className="w-5 h-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      );
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-4xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Cash Transaction History</h2>
            <p className="text-sm text-gray-600 mt-1">{salesmanName} - Bank Book View</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 focus:outline-none"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Current Balance Header */}
        <div className="px-6 py-4 bg-gray-50 border-b">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">Current Balance:</span>
            <span className={`text-lg font-bold ${currentBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              LKR {currentBalance.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Transaction List */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="animate-pulse border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                  </div>
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-lg">No transactions found</p>
              <p className="text-gray-400 text-sm mt-1">Transaction history will appear here</p>
            </div>
          ) : (
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div key={transaction.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-start space-x-3">
                      <div className="mt-1">
                        {getTransactionIcon(transaction.transaction_type, transaction.amount)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="font-medium text-gray-900">
                            {getTransactionTypeLabel(transaction.transaction_type)}
                          </span>
                          {transaction.reference_id && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              {transaction.reference_id}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{transaction.description}</p>
                        {transaction.notes && (
                          <p className="text-xs text-gray-500 mt-1 italic">{transaction.notes}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-semibold ${getTransactionTypeColor(transaction.transaction_type, transaction.amount)}`}>
                        {transaction.amount > 0 ? '+' : ''}LKR {transaction.amount.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDateTime(transaction.created_at)}
                      </div>
                    </div>
                  </div>
                  
                  {/* Balance Information */}
                  <div className="flex justify-between items-center pt-3 border-t border-gray-100 text-sm">
                    <div className="flex space-x-4">
                      <span className="text-gray-600">
                        Before: <span className="font-medium">LKR {transaction.balance_before.toFixed(2)}</span>
                      </span>
                      <span className="text-gray-600">
                        After: <span className="font-medium">LKR {transaction.balance_after.toFixed(2)}</span>
                      </span>
                    </div>
                    {transaction.reference_type && (
                      <span className="text-xs text-gray-500 capitalize">
                        {transaction.reference_type.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer with Current Balance */}
        <div className="px-6 py-4 bg-gray-50 border-t">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              Total Transactions: <span className="font-medium">{transactions.length}</span>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Current Balance</div>
              <div className={`text-xl font-bold ${currentBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                LKR {currentBalance.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};