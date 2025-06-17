import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { 
  BuildingStorefrontIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  BanknotesIcon,
  CreditCardIcon,
  ReceiptRefundIcon,
  PlusIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { shopService, transactionService } from '../services/apiServices';
import { Shop } from '../types';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';

interface OutstandingInvoice {
  id: number;
  invoice_number: string;
  invoice_date: string;
  net_total: number;
  paid_amount: number;
  balance_due: number;
  status: string;
  due_date?: string;
}

interface DebitsData {
  total_debits: number;
  invoices_count: number;
  by_status: { pending: number; partial: number; overdue: number };
  by_shop: Array<{
    shop__id: number;
    shop__name: string;
    outstanding_amount: number;
    invoices_count: number;
  }>;
}

export const InvoiceSettlementPage: React.FC = () => {
  const [shops, setShops] = useState<Shop[]>([]);
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);
  const [outstandingInvoices, setOutstandingInvoices] = useState<OutstandingInvoice[]>([]);
  const [totalOutstanding, setTotalOutstanding] = useState(0);
  const [debitsData, setDebitsData] = useState<DebitsData | null>(null);
  
  // Loading states
  const [shopsLoading, setShopsLoading] = useState(true);
  const [invoicesLoading, setInvoicesLoading] = useState(false);
  const [debitsLoading, setDebitsLoading] = useState(true);
  
  // Modal states
  const [isShopModalOpen, setIsShopModalOpen] = useState(false);
  const [isSettlementModalOpen, setIsSettlementModalOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<OutstandingInvoice | null>(null);
  const [isSettling, setIsSettling] = useState(false);
  
  // Search and filter states
  const [shopSearchTerm, setShopSearchTerm] = useState('');
  
  // Settlement form - now supports multiple payments
  const [settlementForm, setSettlementForm] = useState({
    payments: [
      {
        id: Math.random().toString(36).substr(2, 9),
        payment_method: 'cash',
        amount: '',
        reference_number: '',
        bank_name: '',
        cheque_date: '',
        notes: ''
      }
    ],
    notes: ''
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setShopsLoading(true);
      setDebitsLoading(true);
      
      const [shopsData, debitsResponse] = await Promise.all([
        shopService.getShops(),
        transactionService.getTotalDebits()
      ]);

      setShops(shopsData.results);
      setDebitsData(debitsResponse);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setShopsLoading(false);
      setDebitsLoading(false);
    }
  };

  const loadOutstandingInvoices = async (shop: Shop) => {
    try {
      setInvoicesLoading(true);
      const response = await transactionService.getOutstandingInvoices(shop.id);
      setOutstandingInvoices(response.invoices);
      setTotalOutstanding(response.total_outstanding);
    } catch (error) {
      console.error('Error loading invoices:', error);
      toast.error('Failed to load outstanding invoices');
    } finally {
      setInvoicesLoading(false);
    }
  };

  const handleSelectShop = async (shop: Shop) => {
    setSelectedShop(shop);
    setIsShopModalOpen(false);
    setShopSearchTerm('');
    await loadOutstandingInvoices(shop);
  };

  const handleSelectInvoice = (invoice: OutstandingInvoice) => {
    setSelectedInvoice(invoice);
    setSettlementForm({
      payments: [
        {
          id: Math.random().toString(36).substr(2, 9),
          payment_method: 'cash',
          amount: invoice.balance_due.toString(),
          reference_number: '',
          bank_name: '',
          cheque_date: '',
          notes: ''
        }
      ],
      notes: ''
    });
    setIsSettlementModalOpen(true);
  };

  const addPaymentRow = () => {
    setSettlementForm(prev => ({
      ...prev,
      payments: [
        ...prev.payments,
        {
          id: Math.random().toString(36).substr(2, 9),
          payment_method: 'cash',
          amount: '',
          reference_number: '',
          bank_name: '',
          cheque_date: '',
          notes: ''
        }
      ]
    }));
  };

  const removePaymentRow = (paymentId: string) => {
    setSettlementForm(prev => ({
      ...prev,
      payments: prev.payments.filter(p => p.id !== paymentId)
    }));
  };

  const updatePayment = (paymentId: string, field: string, value: string) => {
    setSettlementForm(prev => ({
      ...prev,
      payments: prev.payments.map(p => 
        p.id === paymentId ? { ...p, [field]: value } : p
      )
    }));
  };

  const getTotalPaymentAmount = (): number => {
    return settlementForm.payments.reduce((total, payment) => {
      const amount = parseFloat(payment.amount) || 0;
      return total + amount;
    }, 0);
  };

  const handleSettleInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedInvoice) return;
    
    const totalAmount = getTotalPaymentAmount();
    
    if (totalAmount <= 0) {
      toast.error('Please enter valid payment amounts');
      return;
    }
    
    if (totalAmount > selectedInvoice.balance_due) {
      toast.error('Total payment amount cannot exceed outstanding balance');
      return;
    }

    // Validate that all payment rows have amounts
    const invalidPayments = settlementForm.payments.filter(p => !p.amount || parseFloat(p.amount) <= 0);
    if (invalidPayments.length > 0) {
      toast.error('Please enter valid amounts for all payment methods');
      return;
    }

    try {
      setIsSettling(true);
      
      const paymentData = settlementForm.payments.map(payment => ({
        payment_method: payment.payment_method,
        amount: parseFloat(payment.amount),
        reference_number: payment.reference_number,
        bank_name: payment.bank_name,
        cheque_date: payment.cheque_date || undefined,
        notes: payment.notes
      }));

      const response = await transactionService.settleInvoiceMultiPayment({
        invoice_id: selectedInvoice.id,
        payments: paymentData,
        notes: settlementForm.notes
      });

      toast.success(response.message);
      setIsSettlementModalOpen(false);
      setSelectedInvoice(null);
      
      // Reload data
      if (selectedShop) {
        await loadOutstandingInvoices(selectedShop);
      }
      await loadInitialData();
      
    } catch (error: any) {
      console.error('Error settling invoice:', error);
      toast.error(error.response?.data?.error || 'Failed to settle invoice');
    } finally {
      setIsSettling(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'partial':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'overdue':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getPaymentMethodIcon = (method: string) => {
    switch (method) {
      case 'cash':
        return <BanknotesIcon className="h-5 w-5" />;
      case 'cheque':
        return <ReceiptRefundIcon className="h-5 w-5" />;
      case 'bank_transfer':
        return <CreditCardIcon className="h-5 w-5" />;
      default:
        return <CurrencyDollarIcon className="h-5 w-5" />;
    }
  };

  const filteredShops = shops.filter(shop =>
    shop.name.toLowerCase().includes(shopSearchTerm.toLowerCase()) ||
    shop.contact_person.toLowerCase().includes(shopSearchTerm.toLowerCase())
  );

  if (shopsLoading || debitsLoading) {
    return (
      <Layout title="Invoice Settlement">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Invoice Settlement">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header with Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Total Debits Card */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CurrencyDollarIcon className="h-8 w-8 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Outstanding
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(debitsData?.total_debits || 0)}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {debitsData?.invoices_count || 0} invoices
                </p>
              </div>
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              By Status
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Pending:</span>
                <span className="font-medium">{formatCurrency(debitsData?.by_status.pending || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Partial:</span>
                <span className="font-medium">{formatCurrency(debitsData?.by_status.partial || 0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Overdue:</span>
                <span className="font-medium text-red-600">{formatCurrency(debitsData?.by_status.overdue || 0)}</span>
              </div>
            </div>
          </div>

          {/* Current Shop Info */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <BuildingStorefrontIcon className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Selected Shop
                  </p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {selectedShop?.name || 'None'}
                  </p>
                  {selectedShop && (
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {formatCurrency(totalOutstanding)} outstanding
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="btn-primary"
              >
                {selectedShop ? 'Change' : 'Select'} Shop
              </button>
            </div>
          </div>
        </div>

        {/* Outstanding Invoices */}
        {selectedShop && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Outstanding Invoices - {selectedShop.name}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Click on an invoice to settle payment
              </p>
            </div>

            {invoicesLoading ? (
              <div className="p-6">
                <LoadingSpinner size="sm" />
              </div>
            ) : outstandingInvoices.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Invoice
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Total
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Paid
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Outstanding
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {outstandingInvoices.map((invoice) => (
                      <tr 
                        key={invoice.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                        onClick={() => handleSelectInvoice(invoice)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {invoice.invoice_number}
                          </div>
                          {invoice.due_date && (
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Due: {new Date(invoice.due_date).toLocaleDateString()}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {new Date(invoice.invoice_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(invoice.net_total)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {formatCurrency(invoice.paid_amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">
                          {formatCurrency(invoice.balance_due)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(invoice.status)}`}>
                            {invoice.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectInvoice(invoice);
                            }}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-200"
                          >
                            Settle
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-6 text-center">
                <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  All Settled!
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  This shop has no outstanding invoices.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Shop Selection Modal */}
        {isShopModalOpen && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Select Shop for Settlement
                    </h3>
                    <button
                      onClick={() => setIsShopModalOpen(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Search */}
                  <div className="mb-4">
                    <div className="relative">
                      <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search shops..."
                        value={shopSearchTerm}
                        onChange={(e) => setShopSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>

                  {/* Shop List */}
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {filteredShops.map((shop) => {
                      const shopDebit = debitsData?.by_shop.find(s => s.shop__id === shop.id);
                      return (
                        <div
                          key={shop.id}
                          onClick={() => handleSelectShop(shop)}
                          className="p-3 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                          <div className="font-medium text-gray-900 dark:text-white">{shop.name}</div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            Contact: {shop.contact_person}
                          </div>
                          {shopDebit && (
                            <div className="text-sm text-red-600 font-medium">
                              Outstanding: {formatCurrency(shopDebit.outstanding_amount)} ({shopDebit.invoices_count} invoices)
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {filteredShops.length === 0 && (
                    <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                      No shops found
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settlement Modal */}
        {isSettlementModalOpen && selectedInvoice && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full max-h-[90vh] overflow-y-auto">
                <form onSubmit={handleSettleInvoice}>
                  <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Settle Invoice
                      </h3>
                      <button
                        type="button"
                        onClick={() => setIsSettlementModalOpen(false)}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>

                    {/* Invoice Details */}
                    <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg mb-6">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                        {selectedInvoice.invoice_number}
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Total:</span>
                          <span className="font-medium">{formatCurrency(selectedInvoice.net_total)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Paid:</span>
                          <span className="font-medium">{formatCurrency(selectedInvoice.paid_amount)}</span>
                        </div>
                        <div className="flex justify-between border-t pt-1">
                          <span className="text-gray-600 dark:text-gray-400">Outstanding:</span>
                          <span className="font-bold text-red-600">{formatCurrency(selectedInvoice.balance_due)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Settlement Form */}
                    <div className="space-y-6">
                      {/* Payment Methods */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Payment Methods
                          </label>
                          <button
                            type="button"
                            onClick={addPaymentRow}
                            className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800"
                          >
                            <PlusIcon className="h-3 w-3 mr-1" />
                            Add Payment
                          </button>
                        </div>

                        <div className="space-y-3">
                          {settlementForm.payments.map((payment, index) => (
                            <div key={payment.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                  Payment {index + 1}
                                </span>
                                {settlementForm.payments.length > 1 && (
                                  <button
                                    type="button"
                                    onClick={() => removePaymentRow(payment.id)}
                                    className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                  >
                                    <TrashIcon className="h-4 w-4" />
                                  </button>
                                )}
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div>
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    Method
                                  </label>
                                  <select
                                    value={payment.payment_method}
                                    onChange={(e) => updatePayment(payment.id, 'payment_method', e.target.value)}
                                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                  >
                                    <option value="cash">Cash</option>
                                    <option value="cheque">Cheque</option>
                                    <option value="return">Return</option>
                                    <option value="bill_to_bill">Bill to Bill</option>
                                    <option value="bank_transfer">Bank Transfer</option>
                                    <option value="credit_note">Credit Note</option>
                                  </select>
                                </div>

                                <div>
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    Amount
                                  </label>
                                  <input
                                    type="number"
                                    step="0.01"
                                    min="0.01"
                                    value={payment.amount}
                                    onChange={(e) => updatePayment(payment.id, 'amount', e.target.value)}
                                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                    placeholder="0.00"
                                  />
                                </div>
                              </div>

                              {(payment.payment_method === 'cheque' || payment.payment_method === 'bank_transfer') && (
                                <div className="grid grid-cols-2 gap-3 mt-3">
                                  <div>
                                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                      Reference Number
                                    </label>
                                    <input
                                      type="text"
                                      value={payment.reference_number}
                                      onChange={(e) => updatePayment(payment.id, 'reference_number', e.target.value)}
                                      className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                      placeholder="Cheque/Transfer ID"
                                    />
                                  </div>

                                  {payment.payment_method === 'bank_transfer' && (
                                    <div>
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Bank Name
                                      </label>
                                      <input
                                        type="text"
                                        value={payment.bank_name}
                                        onChange={(e) => updatePayment(payment.id, 'bank_name', e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                        placeholder="Bank name"
                                      />
                                    </div>
                                  )}

                                  {payment.payment_method === 'cheque' && (
                                    <div>
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Cheque Date
                                      </label>
                                      <input
                                        type="date"
                                        value={payment.cheque_date}
                                        onChange={(e) => updatePayment(payment.id, 'cheque_date', e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                      />
                                    </div>
                                  )}
                                </div>
                              )}

                              {payment.notes && (
                                <div className="mt-3">
                                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                    Notes
                                  </label>
                                  <input
                                    type="text"
                                    value={payment.notes}
                                    onChange={(e) => updatePayment(payment.id, 'notes', e.target.value)}
                                    className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                    placeholder="Payment notes..."
                                  />
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        {/* Payment Summary */}
                        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              Total Payment Amount:
                            </span>
                            <span className="text-lg font-bold text-green-600 dark:text-green-400">
                              {formatCurrency(getTotalPaymentAmount())}
                            </span>
                          </div>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Remaining Balance:
                            </span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {formatCurrency(selectedInvoice.balance_due - getTotalPaymentAmount())}
                            </span>
                          </div>
                          {getTotalPaymentAmount() > selectedInvoice.balance_due && (
                            <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                              ⚠️ Payment amount exceeds outstanding balance
                            </div>
                          )}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Settlement Notes (Optional)
                        </label>
                        <textarea
                          rows={2}
                          value={settlementForm.notes}
                          onChange={(e) => setSettlementForm(prev => ({ ...prev, notes: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          placeholder="Overall settlement notes..."
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-900 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="submit"
                      disabled={isSettling}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                    >
                      {isSettling ? (
                        <>
                          <LoadingSpinner size="sm" />
                          <span className="ml-2">Processing...</span>
                        </>
                      ) : (
                        <>
                          <CurrencyDollarIcon className="h-4 w-4" />
                          <span className="ml-2">
                            Settle {formatCurrency(getTotalPaymentAmount())}
                            {settlementForm.payments.length > 1 && ` (${settlementForm.payments.length} payments)`}
                          </span>
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsSettlementModalOpen(false)}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
