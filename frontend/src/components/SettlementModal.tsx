import React, { useState, useEffect } from 'react';
import { X, DollarSign, TrendingUp, TrendingDown, Calculator, Receipt, Eye, Plus, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { cashFlowService, invoiceService } from '../services/apiServices';
import toast from 'react-hot-toast';

interface SettlementModalProps {
  salesman: any;
  isOpen: boolean;
  onClose: () => void;
  onSettle: (salesmanId: number, settlementData: SettlementData) => void;
  isSettling: boolean;
}

interface SettlementData {
  settlement_notes: string;
  cash_settlement_amount: number;
  settlement_method: 'full_cash' | 'partial_cash' | 'balance_carry';
  return_all_stock: boolean;
  create_settlement_record: boolean;
}

interface CashFlow {
  total_collections: number;
  total_expenses: number;
  net_cash_available: number;
  current_balance: number;
  last_settlement_date: string | null;
}

interface Invoice {
  id: number;
  invoice_number: string;
  shop_name: string;
  invoice_date: string;
  net_total: number;
  paid_amount: number;
  balance_due: number;
  status: string;
  cash_collected?: number;
}

interface CashTransaction {
  id: number;
  transaction_type: string;
  transaction_type_display: string;
  amount: number;
  balance_before: number;
  balance_after: number;
  description: string;
  notes: string | null;
  reference_type: string | null;
  reference_id: string | null;
  invoice_number: string | null;
  created_at: string;
  created_by: string | null;
}

export const SettlementModal: React.FC<SettlementModalProps> = ({
  salesman,
  isOpen,
  onClose,
  onSettle,
  isSettling
}) => {
  const [cashFlow, setCashFlow] = useState<CashFlow | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [cashTransactions, setCashTransactions] = useState<CashTransaction[]>([]);
  const [settlementAmount, setSettlementAmount] = useState(0);
  const [settlementMethod, setSettlementMethod] = useState<'full_cash' | 'partial_cash' | 'balance_carry'>('full_cash');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'invoices' | 'transactions'>('summary');
  const [cashCollections, setCashCollections] = useState<{[key: number]: number}>({});

  useEffect(() => {
    if (isOpen && salesman) {
      loadSettlementData();
    }
  }, [isOpen, salesman]);

  const loadSettlementData = async () => {
    try {
      setLoading(true);
      const salesmanId = salesman.salesman_id || salesman.id;
      
      // Load cash flow data
      const cashFlowData = await cashFlowService.getSettlementCashFlow(salesmanId);
      setCashFlow(cashFlowData);
      
      // Load recent invoices for this salesman
      const invoicesData = await invoiceService.getInvoices({ 
        salesman: salesmanId,
        status: 'pending,partial,paid',
        page_size: 50 
      });
      setInvoices(invoicesData.results || []);
      
      // Load cash transaction history
      const transactionsData = await cashFlowService.getCashTransactionHistory(salesmanId, 20);
      setCashTransactions(transactionsData);
      
      setSettlementAmount(cashFlowData.net_cash_available);
    } catch (error) {
      console.error('Error loading settlement data:', error);
      toast.error('Failed to load settlement data');
    } finally {
      setLoading(false);
    }
  };

  const handleSettle = () => {
    if (!cashFlow) return;

    if (settlementAmount > cashFlow.net_cash_available) {
      toast.error(`Settlement amount cannot exceed available cash (${cashFlow.net_cash_available.toFixed(2)})`);
      return;
    }

    onSettle(salesman.salesman_id || salesman.id, {
      settlement_notes: notes,
      cash_settlement_amount: settlementAmount,
      settlement_method: settlementMethod,
      return_all_stock: true,
      create_settlement_record: true
    });
  };

  const handleCashCollectionChange = (invoiceId: number, amount: number) => {
    setCashCollections(prev => ({
      ...prev,
      [invoiceId]: amount
    }));
  };

  const recordCashCollection = async (invoiceId: number, amount: number) => {
    try {
      await cashFlowService.recordCashCollection({
        invoice_id: invoiceId,
        amount: amount,
        notes: `Cash collection recorded during settlement`
      });
      toast.success(`Cash collection recorded: LKR ${amount.toFixed(2)}`);
      // Reload settlement data to reflect changes
      loadSettlementData();
    } catch (error) {
      console.error('Error recording cash collection:', error);
      toast.error('Failed to record cash collection');
    }
  };

  const getTotalCashCollected = () => {
    return Object.values(cashCollections).reduce((sum, amount) => sum + amount, 0);
  };

  const handleClose = () => {
    setNotes('');
    setSettlementAmount(0);
    setSettlementMethod('full_cash');
    setCashFlow(null);
    setInvoices([]);
    setCashTransactions([]);
    setCashCollections({});
    setActiveTab('summary');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Settle Salesman - {salesman?.salesman_name || salesman?.name}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : cashFlow ? (
            <>
              {/* Tabs Navigation */}
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="-mb-px flex space-x-8">
                  {[
                    { id: 'summary', label: 'Cash Flow Summary', icon: Calculator },
                    { id: 'invoices', label: 'Invoices & Collections', icon: Receipt },
                    { id: 'transactions', label: 'Transaction History', icon: Eye },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                      }`}
                    >
                      <tab.icon className="w-4 h-4" />
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </nav>
              </div>

              {/* Tab Content */}
              {activeTab === 'summary' && (
                <div className="space-y-4">
                  {/* Cash Flow Summary */}
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                    <h3 className="font-semibold mb-3 text-blue-900 dark:text-blue-100">Cash Flow Summary</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="flex items-center space-x-2">
                        <TrendingUp className="w-4 h-4 text-green-600" />
                        <span className="text-gray-600 dark:text-gray-400">Total Collections:</span>
                        <span className="font-medium text-green-600">LKR {cashFlow.total_collections.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <TrendingDown className="w-4 h-4 text-red-600" />
                        <span className="text-gray-600 dark:text-gray-400">Total Expenses:</span>
                        <span className="font-medium text-red-600">LKR {cashFlow.total_expenses.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <DollarSign className="w-4 h-4 text-blue-600" />
                        <span className="text-gray-600 dark:text-gray-400">Net Available:</span>
                        <span className="font-bold text-blue-600">LKR {cashFlow.net_cash_available.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Calculator className="w-4 h-4 text-purple-600" />
                        <span className="text-gray-600 dark:text-gray-400">Current Balance:</span>
                        <span className={`font-medium ${cashFlow.current_balance >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                          LKR {cashFlow.current_balance.toFixed(2)}
                        </span>
                      </div>
                    </div>
                    {cashFlow.last_settlement_date && (
                      <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
                        Last settlement: {new Date(cashFlow.last_settlement_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'invoices' && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-yellow-600" />
                      <span className="text-sm text-yellow-800 dark:text-yellow-200">
                        Record cash collections from invoices to update the net balance calculation
                      </span>
                    </div>
                  </div>
                  
                  <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                      <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Invoice
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Shop
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Total
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Paid
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Balance
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Status
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Cash Collection
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                        {invoices.map((invoice) => (
                          <tr key={invoice.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-3 py-2 text-sm font-medium text-gray-900 dark:text-white">
                              {invoice.invoice_number}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">
                              {invoice.shop_name}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-900 dark:text-white">
                              LKR {invoice.net_total.toFixed(2)}
                            </td>
                            <td className="px-3 py-2 text-sm text-green-600">
                              LKR {invoice.paid_amount.toFixed(2)}
                            </td>
                            <td className="px-3 py-2 text-sm text-red-600">
                              LKR {invoice.balance_due.toFixed(2)}
                            </td>
                            <td className="px-3 py-2">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                invoice.status === 'paid' 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : invoice.status === 'partial'
                                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {invoice.status === 'paid' ? (
                                  <><CheckCircle className="w-3 h-3 mr-1" /> Paid</>
                                ) : invoice.status === 'partial' ? (
                                  <><Clock className="w-3 h-3 mr-1" /> Partial</>
                                ) : (
                                  <><AlertCircle className="w-3 h-3 mr-1" /> Pending</>
                                )}
                              </span>
                            </td>
                            <td className="px-3 py-2">
                              <div className="flex items-center space-x-2">
                                <input
                                  type="number"
                                  step="0.01"
                                  value={cashCollections[invoice.id] || 0}
                                  onChange={(e) => handleCashCollectionChange(invoice.id, parseFloat(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                  placeholder="0.00"
                                />
                                <button
                                  onClick={() => recordCashCollection(invoice.id, cashCollections[invoice.id] || 0)}
                                  disabled={!cashCollections[invoice.id] || cashCollections[invoice.id] <= 0}
                                  className="p-1 text-blue-600 hover:text-blue-800 disabled:text-gray-400 disabled:cursor-not-allowed"
                                  title="Record cash collection"
                                >
                                  <Plus className="w-3 h-3" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {getTotalCashCollected() > 0 && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-green-800 dark:text-green-200">
                          Total Cash to Record:
                        </span>
                        <span className="text-sm font-bold text-green-600">
                          LKR {getTotalCashCollected().toFixed(2)}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'transactions' && (
                <div className="space-y-4">
                  <div className="max-h-64 overflow-y-auto border border-gray-200 dark:border-gray-600 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                      <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                        <tr>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Date
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Type
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Amount
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Description
                          </th>
                          <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                            Invoice
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                        {cashTransactions.map((transaction) => (
                          <tr key={transaction.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                            <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">
                              {new Date(transaction.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-3 py-2">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                transaction.transaction_type === 'collection'
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : transaction.transaction_type === 'settlement'
                                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                  : transaction.transaction_type === 'expense'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                              }`}>
                                {transaction.transaction_type}
                              </span>
                            </td>
                            <td className={`px-3 py-2 text-sm font-medium ${
                              transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {transaction.amount >= 0 ? '+' : ''}LKR {transaction.amount.toFixed(2)}
                            </td>
                            <td className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">
                              {transaction.description}
                            </td>
                            <td className="px-3 py-2 text-sm text-blue-600">
                              {transaction.invoice_number || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Settlement Method */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Settlement Method
                </label>
                <select
                  value={settlementMethod}
                  onChange={(e) => setSettlementMethod(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="full_cash">Full Cash Settlement</option>
                  <option value="partial_cash">Partial Cash Settlement</option>
                  <option value="balance_carry">Carry Balance Forward</option>
                </select>
              </div>

              {/* Settlement Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Settlement Amount
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    value={settlementAmount}
                    onChange={(e) => setSettlementAmount(parseFloat(e.target.value) || 0)}
                    max={cashFlow.net_cash_available}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="0.00"
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <span className="text-gray-500 text-sm">LKR</span>
                  </div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Maximum available: LKR {cashFlow.net_cash_available.toFixed(2)}
                </p>
                {settlementAmount > cashFlow.net_cash_available && (
                  <p className="text-xs text-red-600 mt-1">
                    Amount exceeds available cash
                  </p>
                )}
              </div>

              {/* Settlement Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Settlement Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  rows={3}
                  placeholder="Add settlement notes..."
                />
              </div>

              {/* Balance Impact Preview */}
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">Settlement Impact</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Current Balance:</span>
                    <span className={cashFlow.current_balance >= 0 ? 'text-red-600' : 'text-green-600'}>
                      LKR {cashFlow.current_balance.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Settlement Amount:</span>
                    <span className="text-blue-600">- LKR {settlementAmount.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between border-t border-gray-200 dark:border-gray-600 pt-1">
                    <span className="font-medium text-gray-900 dark:text-white">New Balance:</span>
                    <span className={`font-bold ${(cashFlow.current_balance - settlementAmount) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                      LKR {(cashFlow.current_balance - settlementAmount).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">Failed to load cash flow data</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSettling}
          >
            Cancel
          </button>
          <button
            onClick={handleSettle}
            disabled={isSettling || !cashFlow || settlementAmount > (cashFlow?.net_cash_available || 0)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSettling ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Settling...</span>
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4" />
                <span>Settle Salesman</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};