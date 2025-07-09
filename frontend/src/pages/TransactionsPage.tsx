import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard, LoadingSpinner } from '../components/LoadingSpinner';
import { 
  PlusIcon, 
  MagnifyingGlassIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CurrencyDollarIcon,
  BanknotesIcon,
  CalendarIcon,
  FunnelIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { 
  financialTransactionService, 
  financialDashboardService 
} from '../services/financialServices';
import financeService, { DetailedProfitAnalysis, ProfitBreakdown } from '../services/financeService';
import { 
  FinancialTransaction, 
  CreateFinancialTransactionData,
  FinancialDashboard,
  BankBookEntry
} from '../types';
import { formatCurrency } from '../utils/currency';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { useForm } from 'react-hook-form';

export const TransactionsPage: React.FC = () => {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<FinancialDashboard | null>(null);
  const [bankBook, setBankBook] = useState<BankBookEntry[]>([]);
  const [transactions, setTransactions] = useState<FinancialTransaction[]>([]);
  const [profitAnalysis, setProfitAnalysis] = useState<DetailedProfitAnalysis | null>(null);
  const [selectedProfitView, setSelectedProfitView] = useState<'overview' | 'realized' | 'unrealized' | 'spendable'>('overview');
  const [loading, setLoading] = useState(true);
  const [showAddTransaction, setShowAddTransaction] = useState(false);
  const [transactionType, setTransactionType] = useState<'credit' | 'debit'>('credit');
  const [dateRange, setDateRange] = useState({
    date_from: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    date_to: new Date().toISOString().split('T')[0]
  });
  const [view, setView] = useState<'dashboard' | 'bankbook' | 'transactions' | 'profits'>('dashboard');

  // Date range presets
  const setDatePreset = (preset: 'today' | 'week' | 'month' | 'quarter') => {
    const today = new Date();
    let startDate: Date;
    
    switch (preset) {
      case 'today':
        startDate = new Date(today);
        break;
      case 'week':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 7);
        break;
      case 'month':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 30);
        break;
      case 'quarter':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 90);
        break;
      default:
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
    }
    
    setDateRange({
      date_from: startDate.toISOString().split('T')[0],
      date_to: today.toISOString().split('T')[0]
    });
  };

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors }
  } = useForm<CreateFinancialTransactionData>();

  const watchTransactionType = watch('transaction_type', 'credit');

  useEffect(() => {
    loadFinancialData();
    if (view === 'profits') {
      loadProfitAnalysis();
    }
  }, [dateRange, view]);

  const loadFinancialData = async () => {
    try {
      setLoading(true);
      
      const [dashboardData, bankBookData] = await Promise.all([
        financialDashboardService.getDashboard(dateRange.date_from, dateRange.date_to),
        financialDashboardService.getBankBook(dateRange.date_from, dateRange.date_to)
      ]);
      
      setDashboard(dashboardData);
      setBankBook(bankBookData.entries);
    } catch (error) {
      console.error('Error loading financial data:', error);
      toast.error('Failed to load financial data');
    } finally {
      setLoading(false);
    }
  };

  const loadTransactions = async () => {
    try {
      const data: any = await financialTransactionService.getTransactions({
        date_from: dateRange.date_from,
        date_to: dateRange.date_to
      });
      setTransactions(data.results || data);
    } catch (error) {
      console.error('Error loading transactions:', error);
      toast.error('Failed to load transactions');
    }
  };

  const loadProfitAnalysis = async () => {
    try {
      const data = await financeService.getProfitBreakdown(dateRange.date_from, dateRange.date_to);
      setProfitAnalysis(data);
    } catch (error) {
      console.error('Error loading profit analysis:', error);
      toast.error('Failed to load profit analysis');
    }
  };

  const handleCreateTransaction = async (data: CreateFinancialTransactionData) => {
    try {
      await financialTransactionService.createTransaction(data);
      toast.success(`${data.transaction_type === 'credit' ? 'Income' : 'Expense'} transaction added successfully!`);
      setShowAddTransaction(false);
      reset();
      loadFinancialData();
      if (view === 'transactions') {
        loadTransactions();
      }
    } catch (error: any) {
      console.error('Error creating transaction:', error);
      toast.error(error.response?.data?.detail || 'Failed to create transaction');
    }
  };

  const categories = financialTransactionService.getCategories();

  if (loading) {
    return (
      <Layout title="Financial Transactions">
        <LoadingCard title="Loading financial data..." />
      </Layout>
    );
  }

  return (
    <Layout title="Financial Transactions">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-3">
            <BanknotesIcon className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Financial Transactions
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Track your business income, expenses, and cash flow
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                setTransactionType('credit');
                reset({ transaction_type: 'credit' });
                setShowAddTransaction(true);
              }}
              className="btn-primary flex items-center space-x-2"
            >
              <ArrowUpIcon className="h-4 w-4" />
              <span>Add Income</span>
            </button>
            <button
              onClick={() => {
                setTransactionType('debit');
                reset({ transaction_type: 'debit' });
                setShowAddTransaction(true);
              }}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
            >
              <ArrowDownIcon className="h-4 w-4" />
              <span>Add Expense</span>
            </button>
          </div>
        </div>

        {/* Date Range and View Controls */}
        <div className="card p-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex flex-col space-y-4">
              <div className="flex items-center space-x-4">
                <div>
                  <label className="label">From</label>
                  <input
                    type="date"
                    value={dateRange.date_from}
                    onChange={(e) => setDateRange(prev => ({ ...prev, date_from: e.target.value }))}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">To</label>
                  <input
                    type="date"
                    value={dateRange.date_to}
                    onChange={(e) => setDateRange(prev => ({ ...prev, date_to: e.target.value }))}
                    className="input"
                  />
                </div>
              </div>
              
              {/* Date Presets */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setDatePreset('today')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
                >
                  Today
                </button>
                <button
                  onClick={() => setDatePreset('week')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
                >
                  Past 7 Days
                </button>
                <button
                  onClick={() => setDatePreset('month')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
                >
                  Past Month
                </button>
                <button
                  onClick={() => setDatePreset('quarter')}
                  className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
                >
                  Past Quarter
                </button>
              </div>
            </div>

            <div className="flex space-x-1">
              <button
                onClick={() => setView('dashboard')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  view === 'dashboard'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => {
                  setView('profits');
                  loadProfitAnalysis();
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  view === 'profits'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Profit Analysis
              </button>
              <button
                onClick={() => setView('bankbook')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  view === 'bankbook'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Bank Book
              </button>
              <button
                onClick={() => {
                  setView('transactions');
                  loadTransactions();
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  view === 'transactions'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                Transactions
              </button>
            </div>
          </div>
        </div>

        {/* Dashboard View */}
        {view === 'dashboard' && dashboard && (
          <>
            {/* Financial Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="card p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
                    <ArrowUpIcon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Total Income
                    </p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(dashboard.transactions.total_credits)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 p-3 rounded-lg bg-red-500">
                    <ArrowDownIcon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Total Expenses
                    </p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(dashboard.transactions.total_debits)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                    <CurrencyDollarIcon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Cash Flow
                    </p>
                    <p className={`text-2xl font-semibold ${
                      dashboard.cash_flow.net_cash_flow >= 0 
                        ? 'text-green-600 dark:text-green-400' 
                        : 'text-red-600 dark:text-red-400'
                    }`}>
                      {formatCurrency(dashboard.cash_flow.net_cash_flow)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0 p-3 rounded-lg bg-purple-500">
                    <DocumentTextIcon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      Outstanding
                    </p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {formatCurrency(dashboard.invoices.total_outstanding)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Accounting Equation */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Business Financial Position (Assets = Equity + Liabilities)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Assets</p>
                  <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                    {formatCurrency(dashboard.summary.outstanding_receivables)}
                  </p>
                  <p className="text-xs text-gray-500">Cash + Outstanding Invoices</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Equity</p>
                  <p className="text-xl font-bold text-green-600 dark:text-green-400">
                    {formatCurrency(dashboard.summary.profit)}
                  </p>
                  <p className="text-xs text-gray-500">Net Worth</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Liabilities</p>
                  <p className="text-xl font-bold text-red-600 dark:text-red-400">
                    {formatCurrency(dashboard.transactions.total_debits)}
                  </p>
                  <p className="text-xs text-gray-500">Total Expenses</p>
                </div>
              </div>
            </div>

            {/* Invoice vs Cash Flow */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Invoice Management
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Invoiced:</span>
                    <span className="font-semibold">{formatCurrency(dashboard.invoices.total_invoiced)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Collected:</span>
                    <span className="font-semibold text-green-600">{formatCurrency(dashboard.invoices.total_collected)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-900 dark:text-white font-semibold">Net Invoice Balance:</span>
                    <span className="font-bold">{formatCurrency(dashboard.invoices.net_invoice_balance)}</span>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Actual Cash Flow
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Income Transactions:</span>
                    <span className="font-semibold text-green-600">{formatCurrency(dashboard.transactions.total_credits)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Invoice Collections:</span>
                    <span className="font-semibold text-green-600">{formatCurrency(dashboard.invoices.total_collected)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Expenses:</span>
                    <span className="font-semibold text-red-600">{formatCurrency(dashboard.transactions.total_debits)}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-gray-900 dark:text-white font-semibold">Net Cash Flow:</span>
                    <span className={`font-bold ${
                      dashboard.cash_flow.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(dashboard.cash_flow.net_cash_flow)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Bank Book View */}
        {view === 'bankbook' && (
          <div className="card">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Bank Book - Money In & Money Out
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Track all actual money movements in your business
              </p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Reference
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Money In
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Money Out
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Balance
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {bankBook.map((entry, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {new Date(entry.date).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                        <div>
                          {entry.description}
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {entry.category}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {entry.reference || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        {entry.credit > 0 ? (
                          <span className="text-green-600 font-semibold">
                            {formatCurrency(entry.credit)}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        {entry.debit > 0 ? (
                          <span className="text-red-600 font-semibold">
                            {formatCurrency(entry.debit)}
                          </span>
                        ) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-semibold">
                        <span className={entry.balance >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(entry.balance)}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {bankBook.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                        No transactions found for the selected period
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Profit Analysis View */}
        {view === 'profits' && profitAnalysis && (
          <>
            {/* Profit Analysis Navigation */}
            <div className="card p-4">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedProfitView('overview')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedProfitView === 'overview'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => setSelectedProfitView('realized')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedProfitView === 'realized'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Realized Profit
                </button>
                <button
                  onClick={() => setSelectedProfitView('unrealized')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedProfitView === 'unrealized'
                      ? 'bg-yellow-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Unrealized Profit
                </button>
                <button
                  onClick={() => setSelectedProfitView('spendable')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedProfitView === 'spendable'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                  }`}
                >
                  Spendable Profit
                </button>
              </div>
            </div>

            {/* Overview */}
            {selectedProfitView === 'overview' && (
              <>
                {/* Profit Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="card p-6 border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Realized Profit
                        </p>
                        <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                          {formatCurrency(profitAnalysis.realized.amount)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Money already collected
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900">
                        <CurrencyDollarIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
                      </div>
                    </div>
                  </div>

                  <div className="card p-6 border-l-4 border-yellow-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Unrealized Profit
                        </p>
                        <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                          {formatCurrency(profitAnalysis.unrealized.amount)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Outstanding invoices
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-yellow-100 dark:bg-yellow-900">
                        <DocumentTextIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                      </div>
                    </div>
                  </div>

                  <div className="card p-6 border-l-4 border-blue-500">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                          Spendable Profit
                        </p>
                        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {formatCurrency(profitAnalysis.spendable.amount)}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Available to spend
                        </p>
                      </div>
                      <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
                        <BanknotesIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Business Performance Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Sales Performance
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Total Sales:</span>
                        <span className="font-semibold">{formatCurrency(profitAnalysis.summary.total_sales)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Total Collections:</span>
                        <span className="font-semibold text-green-600">{formatCurrency(profitAnalysis.summary.total_collections)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Outstanding:</span>
                        <span className="font-semibold text-yellow-600">{formatCurrency(profitAnalysis.summary.total_outstanding)}</span>
                      </div>
                      <div className="flex justify-between border-t pt-2">
                        <span className="text-gray-900 dark:text-white font-semibold">Collection Efficiency:</span>
                        <span className={`font-bold ${profitAnalysis.summary.collection_efficiency >= 0.8 ? 'text-green-600' : 'text-yellow-600'}`}>
                          {(profitAnalysis.summary.collection_efficiency * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="card p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Profit Breakdown Formula
                    </h3>
                    <div className="space-y-3 text-sm">
                      <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                        <p className="font-medium text-green-800 dark:text-green-200">Realized Profit</p>
                        <p className="text-green-700 dark:text-green-300">= Invoice Collections - Commission Paid</p>
                      </div>
                      <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                        <p className="font-medium text-yellow-800 dark:text-yellow-200">Unrealized Profit</p>
                        <p className="text-yellow-700 dark:text-yellow-300">= Outstanding Invoices - Pending Commissions</p>
                      </div>
                      <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                        <p className="font-medium text-blue-800 dark:text-blue-200">Spendable Profit</p>
                        <p className="text-blue-700 dark:text-blue-300">= Recent Collections - Commission Reserve</p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Detailed Breakdown Views */}
            {selectedProfitView === 'realized' && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Realized Profit Breakdown
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Profit from collected invoices (money already in hand)
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(profitAnalysis.realized.amount)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Last updated: {new Date(profitAnalysis.realized.last_updated).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Components:</h4>
                    {profitAnalysis.realized.components.collection_amount && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Invoice Collections:</span>
                        <span className="font-semibold text-green-600">
                          +{formatCurrency(profitAnalysis.realized.components.collection_amount)}
                        </span>
                      </div>
                    )}
                    {profitAnalysis.realized.components.pending_commissions && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Commission Paid:</span>
                        <span className="font-semibold text-red-600">
                          -{formatCurrency(profitAnalysis.realized.components.pending_commissions)}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">Calculation Details:</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {profitAnalysis.realized.components.calculation_details || 
                       "This represents the actual profit you've earned from invoices that have been paid, minus any commissions already disbursed to salespeople."}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {selectedProfitView === 'unrealized' && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Unrealized Profit Breakdown
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Potential profit from outstanding invoices
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {formatCurrency(profitAnalysis.unrealized.amount)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Last updated: {new Date(profitAnalysis.unrealized.last_updated).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Components:</h4>
                    {profitAnalysis.unrealized.components.outstanding_invoices && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Outstanding Invoices:</span>
                        <span className="font-semibold text-yellow-600">
                          +{formatCurrency(profitAnalysis.unrealized.components.outstanding_invoices)}
                        </span>
                      </div>
                    )}
                    {profitAnalysis.unrealized.components.pending_commissions && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Pending Commissions:</span>
                        <span className="font-semibold text-red-600">
                          -{formatCurrency(profitAnalysis.unrealized.components.pending_commissions)}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">Calculation Details:</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {profitAnalysis.unrealized.components.calculation_details || 
                       "This represents profit that will be realized when outstanding invoices are collected, minus the commissions that will need to be paid to salespeople."}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {selectedProfitView === 'spendable' && (
              <div className="card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Spendable Profit Breakdown
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Cash available for business expenses and owner withdrawal
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {formatCurrency(profitAnalysis.spendable.amount)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Last updated: {new Date(profitAnalysis.spendable.last_updated).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium text-gray-900 dark:text-white">Components:</h4>
                    {profitAnalysis.spendable.components.recent_collections && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Recent Collections:</span>
                        <span className="font-semibold text-blue-600">
                          +{formatCurrency(profitAnalysis.spendable.components.recent_collections)}
                        </span>
                      </div>
                    )}
                    {profitAnalysis.spendable.components.pending_commissions && (
                      <div className="flex justify-between py-2 border-b border-gray-200 dark:border-gray-700">
                        <span className="text-gray-600 dark:text-gray-400">Commission Reserve:</span>
                        <span className="font-semibold text-red-600">
                          -{formatCurrency(profitAnalysis.spendable.components.pending_commissions)}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">Calculation Details:</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {profitAnalysis.spendable.components.calculation_details || 
                       "This represents the cash you can safely spend on business operations or personal withdrawals, after setting aside money for pending commission payments."}
                    </p>
                    <div className="mt-3 p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                        💡 Recommendation: This amount is safe to spend without affecting your ability to pay commissions.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Loading state for profits */}
        {view === 'profits' && !profitAnalysis && (
          <LoadingCard title="Loading profit analysis..." />
        )}

        {/* Transaction Modal */}
        {showAddTransaction && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <form onSubmit={handleSubmit(handleCreateTransaction)}>
                  <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        Add {watchTransactionType === 'credit' ? 'Income' : 'Expense'} Transaction
                      </h3>
                      <button
                        type="button"
                        onClick={() => {
                          setShowAddTransaction(false);
                          reset();
                        }}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        ×
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="label">Transaction Type</label>
                        <select
                          {...register('transaction_type', { required: 'Transaction type is required' })}
                          className="input"
                        >
                          <option value="income">Income</option>
                          <option value="expense">Expense</option>
                        </select>
                      </div>

                      <div>
                        <label className="label">Date *</label>
                        <input
                          {...register('date', { required: 'Date is required' })}
                          type="date"
                          className="input"
                          defaultValue={new Date().toISOString().split('T')[0]}
                        />
                        {errors.date && (
                          <p className="mt-1 text-sm text-red-600">{errors.date.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="label">Description *</label>
                        <input
                          {...register('description', { required: 'Description is required' })}
                          type="text"
                          className="input"
                          placeholder="Enter transaction description"
                        />
                        {errors.description && (
                          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="label">Amount *</label>
                        <input
                          {...register('amount', { 
                            required: 'Amount is required',
                            min: { value: 0.01, message: 'Amount must be greater than 0' }
                          })}
                          type="number"
                          step="0.01"
                          min="0.01"
                          className="input"
                          placeholder="0.00"
                        />
                        {errors.amount && (
                          <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="label">Category *</label>
                        <select
                          {...register('category', { required: 'Category is required' })}
                          className="input"
                        >
                          <option value="">Select category</option>
                          {(watchTransactionType === 'credit' ? categories.credit : categories.debit).map((cat) => (
                            <option key={cat.value} value={cat.value}>
                              {cat.label}
                            </option>
                          ))}
                        </select>
                        {errors.category && (
                          <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="label">Reference Number</label>
                        <input
                          {...register('reference_number')}
                          type="text"
                          className="input"
                          placeholder="Invoice #, Receipt #, etc."
                        />
                      </div>

                      <div>
                        <label className="label">Notes</label>
                        <textarea
                          {...register('notes')}
                          rows={3}
                          className="input resize-none"
                          placeholder="Additional notes (optional)"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="submit"
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                    >
                      Add Transaction
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowAddTransaction(false);
                        reset();
                      }}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-600 dark:text-gray-200 dark:border-gray-500 dark:hover:bg-gray-700"
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
