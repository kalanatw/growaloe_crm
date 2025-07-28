import React, { useState, useEffect, useCallback } from 'react';
import { Mail, Calculator, AlertTriangle, DollarSign, Plus } from 'lucide-react';
import { deliveryService } from '../services/apiServices';
import { apiClient } from '../services/api';
import { ReturnsSummaryCard } from './ReturnsSummaryCard';
import toast from 'react-hot-toast';

interface SalesmanDetailsModalProps {
  salesman: any;
  isOpen: boolean;
  onClose: () => void;
  onSettle: (salesmanId: number, notes?: string, deliveryId?: number, netCash?: number) => void;
  isSettling: number | null;
  activeDeliveryId?: number;
  user: any;
}

export const SalesmanDetailsModal: React.FC<SalesmanDetailsModalProps> = ({
  salesman,
  isOpen,
  onClose,
  onSettle,
  isSettling,
  activeDeliveryId,
  user
}) => {
  const deliveryList = salesman.deliveries?.recent_deliveries || [];
  const defaultDeliveryId = activeDeliveryId || (deliveryList.length > 0 ? deliveryList[0].id : null);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [cashCollections, setCashCollections] = useState<any[]>([]);
  const [salesmanBalance, setSalesmanBalance] = useState<any>(null);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [isCashCollectionModalOpen, setIsCashCollectionModalOpen] = useState(false);
  const [showSettlementConfirmation, setShowSettlementConfirmation] = useState(false);
  const [editingExpense, setEditingExpense] = useState<any | null>(null);

  const [expenseForm, setExpenseForm] = useState({
    category: '',
    amount: '',
    ref_id: '',
    notes: ''
  });
  const [cashCollectionForm, setCashCollectionForm] = useState({
    amount: '',
    collection_method: 'partial_amount' as 'partial_amount' | 'full_amount' | 'excess_returned',
    collection_notes: ''
  });
  const [expenseError, setExpenseError] = useState('');
  const [cashCollectionError, setCashCollectionError] = useState('');
  const expenseCategories = [
    { value: 'food', label: 'Food' },
    { value: 'transportation', label: 'Transportation' },
    { value: 'labour', label: 'Labour' },
    { value: 'accommodation', label: 'Accommodation' },
    { value: 'other', label: 'Other' },
  ];
  const isOwner = user?.role === 'owner';
  const [isSavingExpense, setIsSavingExpense] = useState(false);
  const categoryRef = React.useRef<HTMLSelectElement>(null);

  const activeDelivery = deliveryList.find((d: any) => d.id === defaultDeliveryId) || null;

  const loadCashCollections = useCallback(async () => {
    if (!activeDelivery) return;
    try {
      const settlements = await deliveryService.getSettlementHistory(salesman.salesman.id) as any;
      const settlementData = settlements.results || settlements;

      const collections: any[] = [];
      if (Array.isArray(settlementData)) {
        settlementData.slice(0, 10).forEach((settlement: any) => {
          if (settlement.physical_cash_collections && settlement.physical_cash_collections.length > 0) {
            settlement.physical_cash_collections.forEach((collection: any) => {
              collections.push({
                ...collection,
                settlement_id: settlement.id,
                settlement_number: settlement.settlement_number
              });
            });
          }
        });
      }

      setCashCollections(collections);
    } catch (error: any) {
      console.error('Error loading cash collections:', error);
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
      }
      setCashCollections([]);
    }
  }, [activeDelivery, salesman.salesman.id]);

  const loadSalesmanBalance = useCallback(async () => {
    try {
      const balanceData = await deliveryService.getSalesmanBalanceSummary();
      const currentSalesmanBalance = balanceData.salesman_balances?.find(
        (s: any) => s.salesman_id === salesman.salesman.id
      );
      setSalesmanBalance(currentSalesmanBalance);
    } catch (error) {
      console.error('Error loading salesman balance:', error);
    }
  }, [salesman.salesman.id]);

  useEffect(() => {
    if (activeDelivery) {
      if (activeDelivery.status !== 'settled') {
        deliveryService.getDeliveryExpenses(activeDelivery.id, { is_settled: false }).then((res: any) => {
          setExpenses(res.results || res);
        });
      } else {
        setExpenses([]);
      }

      loadCashCollections();
      loadSalesmanBalance();
    }
  }, [activeDelivery, loadCashCollections, loadSalesmanBalance]);

  useEffect(() => {
    if (isExpenseModalOpen && categoryRef.current) {
      categoryRef.current.focus();
    }
  }, [isExpenseModalOpen]);

  const handleOpenAddExpense = () => {
    setEditingExpense(null);
    setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
    setExpenseError('');
    setIsExpenseModalOpen(true);
  };

  const handleOpenAddCashCollection = () => {
    setCashCollectionForm({ amount: '', collection_method: 'partial_amount', collection_notes: '' });
    setCashCollectionError('');
    setIsCashCollectionModalOpen(true);
  };

  const handleOpenEditExpense = (expense: any) => {
    setEditingExpense(expense);
    setExpenseForm({
      category: expense.category || '',
      amount: expense.amount ? expense.amount.toString() : '',
      ref_id: expense.ref_id || '',
      notes: expense.notes || ''
    });
    setExpenseError('');
    setIsExpenseModalOpen(true);
  };

  const handleCloseCashCollectionModal = () => {
    setIsCashCollectionModalOpen(false);
    setCashCollectionForm({ amount: '', collection_method: 'partial_amount', collection_notes: '' });
    setCashCollectionError('');
  };

  const handleCashCollectionFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    if (e.target.name === 'amount') {
      if (e.target.value && parseFloat(e.target.value) < 0) return;
    }
    setCashCollectionForm({ ...cashCollectionForm, [e.target.name]: e.target.value });
  };

  const handleSaveCashCollection = async () => {
    setCashCollectionError('');
    const amount = parseFloat(cashCollectionForm.amount);
    if (!amount || amount <= 0) {
      setCashCollectionError('Amount must be greater than zero');
      return;
    }

    try {
      await apiClient.post(`auth/salesmen/${salesman.salesman.id}/collect-cash/`, {
        salesman: salesman.salesman.id,
        amount: amount,
        collection_date: new Date().toISOString().split('T')[0],
        collection_method: 'physical_handover',
        notes: cashCollectionForm.collection_notes || `Cash collection from delivery view - ${new Date().toLocaleString()}`
      });

      toast.success(`Cash collected: LKR ${amount.toFixed(2)}`);

      setIsCashCollectionModalOpen(false);
      setCashCollectionForm({ amount: '', collection_method: 'partial_amount', collection_notes: '' });
      loadCashCollections();
      loadSalesmanBalance();

    } catch (error: any) {
      setCashCollectionError(error.response?.data?.error || 'Failed to collect cash');
    }
  };

  const handleCloseExpenseModal = () => {
    setIsExpenseModalOpen(false);
    setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
    setExpenseError('');
    setEditingExpense(null);
  };

  const handleDeleteExpense = async (id: number) => {
    if (!window.confirm('Delete this expense?')) return;
    try {
      await deliveryService.deleteDeliveryExpense(id);
      setExpenses((prev) => prev.filter((e: any) => e.id !== id));
      toast.success('Expense deleted');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete expense');
    }
  };

  const handleExpenseFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    if (e.target.name === 'amount') {
      if (e.target.value && parseFloat(e.target.value) < 0) return;
    }
    setExpenseForm({ ...expenseForm, [e.target.name]: e.target.value });
  };

  const handleSaveExpense = async () => {
    setExpenseError('');
    if (!expenseForm.category) {
      setExpenseError('Category is required');
      return;
    }
    const amount = parseFloat(expenseForm.amount);
    if (!amount || amount <= 0) {
      setExpenseError('Amount must be greater than zero');
      return;
    }
    if (!activeDelivery) {
      setExpenseError('No delivery selected');
      return;
    }
    const data = {
      delivery: activeDelivery.id,
      category: expenseForm.category,
      amount,
      ref_id: expenseForm.ref_id || undefined,
      notes: expenseForm.notes || undefined
    };
    setIsSavingExpense(true);
    try {
      if (editingExpense) {
        const updated = await deliveryService.updateDeliveryExpense(editingExpense.id, data) as any;
        setExpenses((prev) => prev.map((e: any) => e.id === editingExpense.id ? updated : e));
        toast.success('Expense updated');
      } else {
        const created = await deliveryService.createDeliveryExpense(data) as any;
        setExpenses((prev) => [...prev, created]);
        toast.success('Expense added');
      }
      setIsExpenseModalOpen(false);
      setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
      setEditingExpense(null);
    } catch (err: any) {
      setExpenseError(err.response?.data?.detail || 'Failed to save expense');
    } finally {
      setIsSavingExpense(false);
    }
  };

  if (!isOpen || !activeDelivery) return null;

  const deliveryTotal = activeDelivery.items?.reduce((sum: number, item: any) => sum + (item.quantity * Number(item.unit_price || 0)), 0) || 0;
  const unsettledExpenses = expenses.filter((e: any) => !e.is_settled);
  const totalExpenses = unsettledExpenses.reduce((sum: number, e: any) => sum + Number(e.amount), 0);
  const settledExpenses = expenses.filter((e: any) => e.is_settled);
  const totalSettledExpenses = settledExpenses.reduce((sum: number, e: any) => sum + Number(e.amount), 0);
  const currentBalance = salesmanBalance?.current_balance || 0;
  const adjustedBalance = currentBalance - totalExpenses;
  const adjustedNetCashPosition = Math.max(0, currentBalance - totalExpenses);
  const netCash = adjustedNetCashPosition;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {salesman.salesman.name}
              </h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {salesman.salesman.phone}
                </span>
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {salesman.salesman.email}
                </span>
              </div>
            </div>
            <button onClick={onClose} className="btn btn-outline btn-sm">
              Close
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Current Stock */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Current Stock</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {salesman.current_stock.total_products}
                  </p>
                  <p className="text-sm text-gray-600">Products</p>
                </div>
              </div>
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {salesman.current_stock.total_quantity}
                  </p>
                  <p className="text-sm text-gray-600">Items</p>
                </div>
              </div>
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    LKR {salesman.current_stock.total_value.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">Value</p>
                </div>
              </div>
            </div>

            {salesman.current_stock.products.length > 0 && (
              <div className="card">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          SKU
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Unit Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Value
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {salesman.current_stock.products.map((product: any) => (
                        <tr key={product.product_id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {product.product_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {product.product_sku}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {product.quantity}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            LKR {Number(product.unit_price || 0).toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            LKR {(product.quantity * Number(product.unit_price || 0)).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Returns Summary */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Returns Status</h3>
            <ReturnsSummaryCard
              salesmanId={salesman.salesman.id}
              salesmanName={salesman.salesman.name}
            />
          </div>

          {/* Cash & Expense Management */}
          {activeDelivery && activeDelivery.status !== 'settled' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Cash & Expense Management</h3>

              {/* Cash Collections */}
              <div className="mb-6">
                <div className="flex items-center mb-2">
                  <h4 className="text-md font-semibold flex items-center mb-0 text-green-700">Cash Collections</h4>
                </div>
                {cashCollections.length === 0 ? (
                  <p className="text-gray-500">No cash collections recorded.</p>
                ) : (
                  <div className="overflow-x-auto mb-2">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-green-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-green-700 uppercase">Date</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-green-700 uppercase">Amount</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-green-700 uppercase">Method</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-green-700 uppercase">Settlement</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-green-700 uppercase">Notes</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {cashCollections.map((collection: any) => (
                          <tr key={collection.id}>
                            <td className="px-4 py-2 text-sm">{new Date(collection.collection_date).toLocaleDateString()}</td>
                            <td className="px-4 py-2 text-sm font-medium text-green-600">+LKR {Number(collection.amount_collected).toFixed(2)}</td>
                            <td className="px-4 py-2 text-sm">{collection.collection_method.replace('_', ' ')}</td>
                            <td className="px-4 py-2 text-sm">{collection.settlement_number}</td>
                            <td className="px-4 py-2 text-sm">{collection.collection_notes || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Expenses */}
              <div className="mb-6">
                <div className="flex items-center mb-2">
                  <h4 className="text-md font-semibold flex items-center mb-0 text-red-700">Expenses</h4>
                </div>
                {expenses.length === 0 ? (
                  <p className="text-gray-500">No expenses recorded for this delivery.</p>
                ) : (
                  <div className="overflow-x-auto mb-2">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Ref ID</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                          {isOwner && <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {expenses.map((exp: any) => (
                          <tr key={exp.id} className={exp.is_settled ? 'bg-gray-50 opacity-75' : ''}>
                            <td className="px-4 py-2 text-sm">{expenseCategories.find(c => c.value === exp.category)?.label || exp.category}</td>
                            <td className="px-4 py-2 text-sm">
                              <span className={exp.is_settled ? 'line-through text-gray-500' : ''}>
                                LKR {Number(exp.amount).toFixed(2)}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-sm">
                              {exp.is_settled ? (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Settled
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                  Pending
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-sm">{exp.ref_id || '-'}</td>
                            <td className="px-4 py-2 text-sm">{exp.notes || '-'}</td>
                            {isOwner && <td className="px-4 py-2 text-sm">
                              {!exp.is_settled && (
                                <>
                                  <button className="btn btn-xs btn-outline mr-2" onClick={() => handleOpenEditExpense(exp)}>Edit</button>
                                  <button className="btn btn-xs btn-danger" onClick={() => handleDeleteExpense(exp.id)}>Delete</button>
                                </>
                              )}
                              {exp.is_settled && (
                                <span className="text-xs text-gray-500">Settled</span>
                              )}
                            </td>}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Settlement Balance Summary */}
              <div className="bg-gray-50 rounded-lg p-4 mt-4">
                <h5 className="font-semibold text-gray-800 mb-3">Settlement Balance Summary</h5>
                <div className={`rounded-lg p-3 mb-3 ${currentBalance >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="flex justify-between items-center">
                    <span className={`text-sm font-medium ${currentBalance >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                      Balance Before Expenses
                    </span>
                    <span className={`text-lg font-bold ${currentBalance >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                      LKR {currentBalance.toFixed(2)}
                    </span>
                  </div>
                </div>

                {totalExpenses > 0 && (
                  <div className="bg-red-50 rounded-lg p-3 mb-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-red-800">
                        Pending Expenses
                      </span>
                      <span className="text-lg font-bold text-red-900">
                        -LKR {totalExpenses.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}

                <div className={`rounded-lg p-3 border-2 ${adjustedBalance >= 0 ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'}`}>
                  <div className="flex justify-between items-center">
                    <span className={`text-sm font-bold ${adjustedBalance >= 0 ? 'text-green-800' : 'text-red-800'}`}>
                      Net Balance After Expenses
                    </span>
                    <span className={`text-xl font-bold ${adjustedBalance >= 0 ? 'text-green-900' : 'text-red-900'}`}>
                      LKR {adjustedBalance.toFixed(2)}
                    </span>
                  </div>
                  <p className={`text-xs mt-1 ${adjustedBalance >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {adjustedBalance >= 0 ? 'Salesman owes owner' : 'Owner owes salesman'}
                  </p>
                </div>

                {adjustedNetCashPosition > 0 && (
                  <div className="bg-blue-50 rounded-lg p-3 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-blue-800">
                        Available to Collect
                      </span>
                      <span className="text-lg font-bold text-blue-900">
                        LKR {adjustedNetCashPosition.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                {isOwner && (
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <h5 className="font-semibold text-gray-800 mb-3">Actions</h5>
                    <div className="grid grid-cols-1 gap-3">
                      {/* Collect Cash Button */}
                      {adjustedNetCashPosition > 0 && (
                        <button
                          className="btn btn-outline bg-green-50 text-green-700 border-green-300 hover:bg-green-100 flex items-center justify-center space-x-2"
                          onClick={handleOpenAddCashCollection}
                        >
                          <DollarSign className="w-4 h-4" />
                          <span>Collect Cash (LKR {adjustedNetCashPosition.toFixed(2)})</span>
                        </button>
                      )}

                      {/* Add Expense Button */}
                      <button
                        className="btn btn-outline bg-red-50 text-red-700 border-red-300 hover:bg-red-100 flex items-center justify-center space-x-2"
                        onClick={handleOpenAddExpense}
                      >
                        <Plus className="w-4 h-4" />
                        <span>Add Expense</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Settlement Actions */}
          {activeDelivery && activeDelivery.status !== 'settled' && isOwner && (
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => setShowSettlementConfirmation(true)}
                className="btn btn-primary flex items-center space-x-2"
                disabled={!!isSettling}
              >
                {isSettling ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Calculator className="w-4 h-4" />
                )}
                <span>Settle Delivery</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add Expense Modal */}
      {isExpenseModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-md mx-4">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {editingExpense ? 'Edit Expense' : 'Add Expense'}
              </h3>
              <p className="text-sm text-gray-600">
                Add an expense for this delivery
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  ref={categoryRef}
                  name="category"
                  value={expenseForm.category}
                  onChange={handleExpenseFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select category</option>
                  {expenseCategories.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount (LKR)</label>
                <input
                  type="number"
                  name="amount"
                  value={expenseForm.amount}
                  onChange={handleExpenseFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reference ID (Optional)</label>
                <input
                  type="text"
                  name="ref_id"
                  value={expenseForm.ref_id}
                  onChange={handleExpenseFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Receipt number, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                <textarea
                  name="notes"
                  value={expenseForm.notes}
                  onChange={handleExpenseFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Additional details about this expense"
                />
              </div>

              {expenseError && <div className="text-red-600 text-sm">{expenseError}</div>}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button className="btn btn-outline" onClick={handleCloseExpenseModal}>Cancel</button>
              <button
                className="btn btn-primary"
                onClick={handleSaveExpense}
                disabled={isSavingExpense}
              >
                {isSavingExpense ? 'Saving...' : (editingExpense ? 'Update' : 'Add')} Expense
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cash Collection Modal */}
      {isCashCollectionModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-md mx-4">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Collect Physical Cash
              </h3>
              <p className="text-sm text-gray-600">
                Record cash collection from {salesman?.salesman?.name}
              </p>
            </div>

            <div className="space-y-4">
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="text-sm text-blue-800">
                  <p className="font-medium">Available to Collect:</p>
                  <p className="text-lg font-bold">LKR {adjustedNetCashPosition.toFixed(2)}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount to Collect (LKR)</label>
                <input
                  type="number"
                  name="amount"
                  value={cashCollectionForm.amount}
                  onChange={handleCashCollectionFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  max={adjustedNetCashPosition}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Collection Notes (Optional)</label>
                <textarea
                  name="collection_notes"
                  value={cashCollectionForm.collection_notes}
                  onChange={handleCashCollectionFormChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Optional notes about this cash collection"
                />
              </div>

              {cashCollectionError && <div className="text-red-600 text-sm">{cashCollectionError}</div>}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button className="btn btn-outline" onClick={handleCloseCashCollectionModal}>Cancel</button>
              <button className="btn btn-primary bg-green-600 hover:bg-green-700" onClick={handleSaveCashCollection}>
                Collect Cash
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Settlement Confirmation Modal */}
      {showSettlementConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-md mx-4">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Confirm Settlement
              </h3>
              <p className="text-sm text-gray-600">
                Please verify the settlement details for {salesman?.salesman?.name}
              </p>
            </div>

            <div className="space-y-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-800 mb-3">Settlement Summary</h4>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Delivery Value:</span>
                    <span className="font-medium">LKR {deliveryTotal.toFixed(2)}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Expenses:</span>
                    <span className="font-medium text-red-600">-LKR {totalExpenses.toFixed(2)}</span>
                  </div>

                  <div className="border-t border-gray-200 pt-2 mt-2">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-700">Net Balance After Expenses:</span>
                      <span className={`font-bold ${adjustedBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        LKR {adjustedBalance.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {adjustedNetCashPosition > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Available to Collect:</span>
                      <span className="font-medium text-blue-600">LKR {adjustedNetCashPosition.toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium">Settlement Action:</p>
                    <p>
                      {adjustedBalance >= 0
                        ? `Salesman owes LKR ${adjustedBalance.toFixed(2)} to owner`
                        : `Owner owes LKR ${Math.abs(adjustedBalance).toFixed(2)} to salesman`
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                className="btn btn-outline"
                onClick={() => setShowSettlementConfirmation(false)}
                disabled={!!isSettling}
              >
                Cancel
              </button>
              <button
                className="btn btn-primary flex items-center space-x-2"
                onClick={() => {
                  onSettle(salesman.salesman.id, '', activeDelivery.id, netCash);
                  setShowSettlementConfirmation(false);
                }}
                disabled={!!isSettling}
              >
                {isSettling ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Calculator className="w-4 h-4" />
                )}
                <span>Confirm Settlement</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};