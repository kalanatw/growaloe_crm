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
import { shopService, transactionService, invoiceService } from '../services/apiServices';
import { batchReturnService, ReturnCreateData, BatchSearchResult, InvoiceBatchInfo, QuickReturnCalculation } from '../services/batchReturnService';
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
  
  // Returns related state
  const [invoiceItems, setInvoiceItems] = useState<any[]>([]);
  const [invoiceBatches, setInvoiceBatches] = useState<InvoiceBatchInfo[]>([]);
  const [batchSearchResults, setBatchSearchResults] = useState<BatchSearchResult[]>([]);
  const [batchSearchLoading, setBatchSearchLoading] = useState(false);
  const [returnSearchTerms, setReturnSearchTerms] = useState<{ [key: number]: string }>({});
  const [showBatchResults, setShowBatchResults] = useState<{ [key: number]: boolean }>({});
  const [activeReturnTab, setActiveReturnTab] = useState<'invoice-batches' | 'search'>('invoice-batches');
  // Settlement form - now supports multiple payments and returns
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
    returns: [] as ReturnCreateData[],
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

  const loadInvoiceBatches = async (invoiceId: number) => {
    try {
      const response = await batchReturnService.getInvoiceBatches(invoiceId);
      setInvoiceBatches(response.batches);
    } catch (error) {
      console.error('Error loading invoice batches:', error);
      toast.error('Failed to load invoice batches');
      setInvoiceBatches([]);
    }
  };

  const handleSelectShop = async (shop: Shop) => {
    setSelectedShop(shop);
    setIsShopModalOpen(false);
    setShopSearchTerm('');
    await loadOutstandingInvoices(shop);
  };

  const handleSelectInvoice = async (invoice: OutstandingInvoice) => {
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
      returns: [],
      notes: ''
    });
    
    // Load invoice items for returns
    try {
      const items = await invoiceService.getInvoiceItems(invoice.id);
      if (Array.isArray(items)) {
        setInvoiceItems(items);
      } else if (items && (items as any).results) {
        setInvoiceItems((items as any).results);
      } else {
        setInvoiceItems([]);
      }
    } catch (error) {
      console.error('Error loading invoice items:', error);
      setInvoiceItems([]);
    }
    
    // Load invoice batches
    await loadInvoiceBatches(invoice.id);
    
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

  const getTotalReturnAmount = (): number => {
    return settlementForm.returns.reduce((total, returnItem) => {
      return total + (returnItem.return_amount || 0);
    }, 0);
  };

  const addReturn = () => {
    const newReturn: ReturnCreateData = {
      original_invoice: selectedInvoice!.id,
      product: 0,
      batch: 0,
      batch_number: '',
      product_name: '',
      quantity: 1,
      reason: 'DEFECTIVE',
      return_amount: 0,
      notes: ''
    };

    setSettlementForm(prev => ({
      ...prev,
      returns: [...prev.returns, newReturn]
    }));
  };

  const removeReturn = (index: number) => {
    // Clean up search state for this return
    setReturnSearchTerms(prev => {
      const newTerms = { ...prev };
      delete newTerms[index];
      return newTerms;
    });
    
    setShowBatchResults(prev => {
      const newShow = { ...prev };
      delete newShow[index];
      return newShow;
    });

    setSettlementForm(prev => {
      // Calculate new returns list without the removed item
      const newReturns = prev.returns.filter((_, i) => i !== index);
      
      // Calculate total return amount after removal
      const totalReturnAmount = newReturns.reduce((total, item) => total + item.return_amount, 0);
      
      // Calculate remaining balance
      const remainingBalance = selectedInvoice ? selectedInvoice.balance_due - totalReturnAmount : 0;
      
      // Update payment amount to match remaining balance
      const updatedPayments = prev.payments.map((payment, i) => {
        if (i === 0) { // Update only the first payment method
          return {
            ...payment,
            amount: Math.max(0, remainingBalance).toFixed(2)
          };
        }
        return payment;
      });
      
      return {
        ...prev,
        returns: newReturns,
        payments: updatedPayments
      };
    });
  };

  const updateReturn = (index: number, field: string, value: any) => {
    setSettlementForm(prev => ({
      ...prev,
      returns: prev.returns.map((returnItem, i) => 
        i === index ? { ...returnItem, [field]: value } : returnItem
      )
    }));
  };

  const searchBatches = async (query: string, returnIndex: number) => {
    if (query.length < 2) {
      setBatchSearchResults([]);
      setShowBatchResults(prev => ({ ...prev, [returnIndex]: false }));
      return;
    }

    setBatchSearchLoading(true);
    try {
      const results = await batchReturnService.searchBatchesForSettlement(query, selectedInvoice?.id);
      setBatchSearchResults(results);
      setShowBatchResults(prev => ({ ...prev, [returnIndex]: true }));
    } catch (error) {
      console.error('Error searching batches:', error);
      toast.error('Failed to search batches');
    } finally {
      setBatchSearchLoading(false);
    }
  };

  const selectBatch = (batch: BatchSearchResult, returnIndex: number) => {
    // Update the return with batch information
    updateReturn(returnIndex, 'batch', batch.id);
    updateReturn(returnIndex, 'product', batch.product_id);
    updateReturn(returnIndex, 'batch_number', batch.batch_number);
    updateReturn(returnIndex, 'product_name', batch.product_name);
    
    // Set the search term to the selected batch
    setReturnSearchTerms(prev => ({ ...prev, [returnIndex]: batch.batch_number }));
    setShowBatchResults(prev => ({ ...prev, [returnIndex]: false }));
  };

  const calculateReturnAmount = async (returnIndex: number, quantity: number) => {
    // Check if return item exists at this index
    if (returnIndex < 0 || returnIndex >= settlementForm.returns.length) {
      console.error('Invalid return index:', returnIndex);
      return 0;
    }
    
    const returnItem = settlementForm.returns[returnIndex];
    
    // Safety checks - ensure all required values exist
    if (!returnItem || !returnItem.batch || !quantity || !selectedInvoice) {
      console.error('Missing data for return calculation', { returnItem, quantity, selectedInvoice });
      return 0;
    }

    try {
      const calculation = await batchReturnService.quickReturnCalculation({
        batch_id: returnItem.batch,
        return_quantity: quantity,
        invoice_id: selectedInvoice.id
      });
      
      // Update the return amount and other return details
      updateReturn(returnIndex, 'return_amount', calculation.total_return_amount);
      
      // Log shop margin info for debugging
      console.log('Return calculation with shop margin:', {
        original_unit_price: calculation.original_unit_price,
        cost_price: calculation.original_cost_price,
        shop_margin_percentage: calculation.shop_margin_percentage,
        shop_margin_amount: calculation.shop_margin_amount,
        quality_deduction: calculation.quality_deduction,
        final_amount: calculation.total_return_amount
      });
      
      // Show shop margin info in toast for transparency
      if (calculation.shop_margin_percentage && calculation.shop_margin_percentage > 0) {
        const marginSource = calculation.margin_source ? ` (from ${calculation.margin_source})` : '';
        toast.success(
          `Return calculated with ${calculation.shop_margin_percentage.toFixed(2)}% shop margin${marginSource}. 
          Original price: ₹${calculation.original_unit_price.toFixed(2)}, 
          Return value: ₹${calculation.original_cost_price?.toFixed(2) || 'N/A'} per unit`,
          { duration: 4000 }
        );
        
        // Show detailed calculation to help users understand the math
        console.log('Return calculation details:', {
          original_price: calculation.original_unit_price,
          shop_margin_percentage: calculation.shop_margin_percentage,
          calculation_formula: `${calculation.original_unit_price} × (1 - ${calculation.shop_margin_percentage}%)`,
          cost_price_after_margin_removal: calculation.original_cost_price,
          quantity: calculation.return_quantity || returnItem.quantity,
          total_return_amount: calculation.total_return_amount,
          margin_calculation: calculation.calculation_details?.margin_calculation
        });
      }
      
      return calculation.total_return_amount;
    } catch (error) {
      console.error('Error calculating return amount:', error);
      toast.error('Failed to calculate return amount');
      return 0;
    }
  };

  const handleBatchSearchChange = (query: string, returnIndex: number) => {
    setReturnSearchTerms(prev => ({ ...prev, [returnIndex]: query }));
    searchBatches(query, returnIndex);
  };

  const handleQuantityChange = async (returnIndex: number, quantity: number) => {
    // Update quantity first
    updateReturn(returnIndex, 'quantity', quantity);
    
    // Calculate and update the return amount
    const returnAmount = await calculateReturnAmount(returnIndex, quantity);
    
    if (returnAmount && selectedInvoice) {
      // Update total returns and recalculate payment amount
      setSettlementForm(prev => {
        const updatedReturns = [...prev.returns];
        updatedReturns[returnIndex] = {
          ...updatedReturns[returnIndex],
          quantity: quantity,
          return_amount: returnAmount
        };
        
        // Recalculate total return amount
        const totalReturnAmount = updatedReturns.reduce((total, item) => total + (item.return_amount || 0), 0);
        
        // Calculate remaining balance
        const remainingBalance = selectedInvoice.balance_due - totalReturnAmount;
        
        // Update payment amount to match remaining balance
        const updatedPayments = prev.payments.map((payment, i) => {
          if (i === 0) { // Update only the first payment method
            return {
              ...payment,
              amount: Math.max(0, remainingBalance).toFixed(2)
            };
          }
          return payment;
        });
        
        return {
          ...prev,
          returns: updatedReturns,
          payments: updatedPayments
        };
      });
    }
  };

  const addReturnFromInvoiceBatch = async (batchInfo: InvoiceBatchInfo) => {
    if (!selectedInvoice) {
      toast.error('No invoice selected');
      return;
    }
    
    try {
      // First, calculate the return amount
      const calculation = await batchReturnService.quickReturnCalculation({
        batch_id: batchInfo.id,
        return_quantity: 1,  // Start with quantity 1
        invoice_id: selectedInvoice.id
      });
      
      if (!calculation.calculation_valid) {
        toast.error(`This batch cannot be returned: ${calculation.max_returnable_quantity === 0 ? 
          'All units have already been returned' : 'Unknown reason'}`);
        return;
      }
      
      // Show shop margin info in toast for transparency
      if (calculation.shop_margin_percentage && calculation.shop_margin_percentage > 0) {
        const marginSource = calculation.margin_source ? ` (from ${calculation.margin_source})` : '';
        toast.success(
          `Return calculated with ${calculation.shop_margin_percentage.toFixed(2)}% shop margin${marginSource}. Return value: ₹${calculation.total_return_amount.toFixed(2)}`,
          { duration: 3000 }
        );
        
        // Log calculation details for debugging
        console.log('Batch return calculation:', {
          original_price: calculation.original_unit_price,
          cost_price_after_margin: calculation.original_cost_price,
          margin_percentage: calculation.shop_margin_percentage,
          margin_formula: `${calculation.original_unit_price} × (1 - ${calculation.shop_margin_percentage}%)`,
          quantity: calculation.return_quantity || 1,
          total: calculation.total_return_amount
        });
      }
      
      // Create the return with the calculated amount
      const newReturn: ReturnCreateData = {
        original_invoice: selectedInvoice.id,
        product: batchInfo.product_id,
        batch: batchInfo.id,
        batch_number: batchInfo.batch_number,
        product_name: batchInfo.product_name,
        quantity: 1,
        reason: 'DEFECTIVE',
        return_amount: calculation.total_return_amount,
        notes: ''
      };

      // Add to returns array and update payment amount
      setSettlementForm(prev => {
        const newReturns = [...prev.returns, newReturn];
        const totalReturnAmount = newReturns.reduce((total, item) => total + item.return_amount, 0);
        const remainingBalance = selectedInvoice.balance_due - totalReturnAmount;
        
        // Update payment amount to match remaining balance
        const updatedPayments = prev.payments.map((payment, index) => {
          if (index === 0) {  // Update only the first payment method
            return {
              ...payment,
              amount: Math.max(0, remainingBalance).toFixed(2)
            };
          }
          return payment;
        });
        
        return {
          ...prev,
          returns: newReturns,
          payments: updatedPayments
        };
      });
      
      toast.success('Return added successfully');
    } catch (error) {
      console.error('Error adding return from batch:', error);
      toast.error('Failed to add return');
    }
  };

  const handleSettleInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedInvoice) return;
    
    const totalPaymentAmount = getTotalPaymentAmount();
    const totalReturnAmount = getTotalReturnAmount();
    const totalSettlement = totalPaymentAmount + totalReturnAmount;
    
    if (totalSettlement <= 0) {
      toast.error('Please enter valid payment amounts or returns');
      return;
    }
    
    if (totalSettlement > selectedInvoice.balance_due) {
      toast.error('Total settlement amount cannot exceed outstanding balance');
      return;
    }

    // Validate that all payment rows have amounts
    const invalidPayments = settlementForm.payments.filter(p => !p.amount || parseFloat(p.amount) <= 0);
    if (invalidPayments.length > 0) {
      toast.error('Please enter valid amounts for all payment methods');
      return;
    }

    // Validate returns
    for (const returnItem of settlementForm.returns) {
      if (!returnItem.batch || !returnItem.product || !returnItem.quantity || returnItem.quantity <= 0) {
        toast.error('Please complete all return details including batch selection');
        return;
      }
      if (returnItem.return_amount <= 0) {
        toast.error('Return amount must be greater than 0');
        return;
      }
    }

    try {
      setIsSettling(true);
      
      // If we have returns, use the batch return service for settlement with returns
      if (settlementForm.returns.length > 0) {
        const paymentData = settlementForm.payments.map(payment => ({
          payment_method: payment.payment_method,
          amount: parseFloat(payment.amount),
          reference_number: payment.reference_number,
          bank_name: payment.bank_name,
          cheque_date: payment.cheque_date || undefined,
          notes: payment.notes
        }));

        // Format returns properly with only the required fields
        const formattedReturns = settlementForm.returns.map(returnItem => ({
          original_invoice: selectedInvoice.id,
          product: returnItem.product,
          batch: returnItem.batch,
          quantity: returnItem.quantity,
          reason: returnItem.reason,
          return_amount: returnItem.return_amount,
          notes: returnItem.notes || ''
        }));
        
        const settlementData = {
          invoice_id: selectedInvoice.id,
          returns: formattedReturns,
          payments: paymentData,
          settlement_notes: settlementForm.notes
        };

        const response = await batchReturnService.processSettlementWithReturns(settlementData);
        toast.success(response.message);
      } else {
        // Use regular settlement if no returns
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
      }

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

  const handleQuickReturn = async (batch: InvoiceBatchInfo, quantity: number) => {
    if (!selectedInvoice) return;

    try {
      const calculation = await batchReturnService.quickReturnCalculation({
        invoice_id: selectedInvoice.id,
        batch_id: batch.id,
        return_quantity: quantity
      });

      if (!calculation.calculation_valid) {
        toast.error(`Cannot return ${quantity} items. Maximum returnable: ${calculation.max_returnable_quantity}`);
        return;
      }
      
      // Show shop margin info in toast for transparency
      if (calculation.shop_margin_percentage && calculation.shop_margin_percentage > 0) {
        const marginSource = calculation.margin_source ? ` (from ${calculation.margin_source})` : '';
        toast.success(
          `Return calculated with ${calculation.shop_margin_percentage.toFixed(2)}% shop margin${marginSource}. Return value: ₹${calculation.total_return_amount.toFixed(2)}`,
          { duration: 3000 }
        );
        
        // Log calculation details for debugging
        console.log('Quick return calculation:', {
          original_price: calculation.original_unit_price,
          cost_price_after_margin: calculation.original_cost_price,
          margin_percentage: calculation.shop_margin_percentage,
          margin_formula: `${calculation.original_unit_price} × (1 - ${calculation.shop_margin_percentage}%)`,
          quantity: calculation.return_quantity || quantity,
          total: calculation.total_return_amount
        });
      }

      const newReturn: ReturnCreateData = {
        original_invoice: selectedInvoice.id,
        product: batch.product_id,
        batch: batch.id,
        batch_number: batch.batch_number,
        product_name: batch.product_name,
        quantity: quantity,
        reason: 'DEFECTIVE',
        return_amount: calculation.total_return_amount,
        notes: ''
      };

      setSettlementForm(prev => ({
        ...prev,
        returns: [...prev.returns, newReturn]
      }));

      toast.success('Return added successfully');
    } catch (error) {
      console.error('Error adding return:', error);
      toast.error('Failed to add return');
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
                      {/* Returns Section */}
                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Product Returns
                          </label>
                          <div className="flex space-x-2">
                            <button
                              type="button"
                              onClick={() => setActiveReturnTab('invoice-batches')}
                              className={`px-3 py-1 text-xs rounded-md ${
                                activeReturnTab === 'invoice-batches'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                              }`}
                            >
                              Invoice Batches ({invoiceBatches.length})
                            </button>
                            <button
                              type="button"
                              onClick={() => setActiveReturnTab('search')}
                              className={`px-3 py-1 text-xs rounded-md ${
                                activeReturnTab === 'search'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                              }`}
                            >
                              Search Batches
                            </button>
                          </div>
                        </div>

                        {/* Tab Content */}
                        <div className="mb-4">
                          {activeReturnTab === 'invoice-batches' && (
                            <div className="space-y-2">
                              {invoiceBatches.length > 0 ? (
                                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                                    Select batches from this invoice to process returns:
                                  </p>
                                  <div className="space-y-2 max-h-48 overflow-y-auto">
                                    {invoiceBatches.map((batch) => (
                                      <div
                                        key={batch.id}
                                        className="flex items-center justify-between p-2 bg-white dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600"
                                      >
                                        <div className="flex-1">
                                          <div className="font-medium text-gray-900 dark:text-white text-sm">
                                            {batch.batch_number}
                                          </div>
                                          <div className="text-xs text-gray-600 dark:text-gray-400">
                                            {batch.product_name} (SKU: {batch.product_sku})
                                          </div>
                                          <div className="text-xs text-gray-500 dark:text-gray-500">
                                            Sold: {batch.sold_quantity} | Returned: {batch.already_returned} | Max returnable: {batch.max_returnable_quantity}
                                          </div>
                                          {batch.quality_status !== 'GOOD' && (
                                            <div className="text-xs text-orange-600 dark:text-orange-400">
                                              Quality: {batch.quality_status}
                                            </div>
                                          )}
                                        </div>
                                        <div className="flex items-center space-x-2">
                                          <div className="text-right">
                                            <div className="text-sm font-medium text-green-600">
                                              {formatCurrency(batch.unit_price)}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                              per unit
                                            </div>
                                          </div>
                                          <button
                                            type="button"
                                            onClick={() => addReturnFromInvoiceBatch(batch)}
                                            disabled={!batch.can_return || batch.max_returnable_quantity <= 0}
                                            className={`px-2 py-1 text-xs rounded-md ${
                                              batch.can_return && batch.max_returnable_quantity > 0
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800'
                                                : 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:text-gray-500'
                                            }`}
                                          >
                                            <PlusIcon className="h-3 w-3" />
                                          </button>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ) : (
                                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                                  <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                                    No batches found for this invoice.
                                  </p>
                                </div>
                              )}
                            </div>
                          )}

                          {activeReturnTab === 'search' && (
                            <div className="space-y-2">
                              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                                  Search for any batch to process returns:
                                </p>
                                <button
                                  type="button"
                                  onClick={addReturn}
                                  className="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800"
                                >
                                  <PlusIcon className="h-4 w-4 mr-1" />
                                  Add Return
                                </button>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Active Returns Display */}
                        {settlementForm.returns.length > 0 && (
                          <div className="space-y-3">
                            <div className="border-t pt-3">
                              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                Active Returns ({settlementForm.returns.length})
                              </h4>
                              {settlementForm.returns.map((returnItem, index) => (
                                <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-3">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                      Return {index + 1}
                                    </span>
                                    <button
                                      type="button"
                                      onClick={() => removeReturn(index)}
                                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                    >
                                      <TrashIcon className="h-4 w-4" />
                                    </button>
                                  </div>
                                  
                                  {/* Show search only for search-based returns */}
                                  {(!returnItem.batch_number || returnItem.batch_number === '') && (
                                    <div className="mb-3">
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Search Batch <span className="text-red-500">*</span>
                                      </label>
                                      <div className="relative">
                                        <div className="relative">
                                          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                          <input
                                            type="text"
                                            value={returnSearchTerms[index] || ''}
                                            onChange={(e) => handleBatchSearchChange(e.target.value, index)}
                                            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                            placeholder="Enter batch number or product name..."
                                          />
                                          {batchSearchLoading && (
                                            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                              <LoadingSpinner size="sm" />
                                            </div>
                                          )}
                                        </div>
                                        
                                        {/* Batch Search Results */}
                                        {showBatchResults[index] && batchSearchResults.length > 0 && (
                                          <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-lg max-h-48 overflow-y-auto">
                                            {batchSearchResults.map((batch) => (
                                              <div
                                                key={batch.id}
                                                onClick={() => selectBatch(batch, index)}
                                                className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-200 dark:border-gray-600 last:border-b-0"
                                              >
                                                <div className="flex justify-between items-start">
                                                  <div className="flex-1">
                                                    <div className="font-medium text-gray-900 dark:text-white">
                                                      {batch.batch_number}
                                                    </div>
                                                    <div className="text-sm text-gray-600 dark:text-gray-400">
                                                      {batch.product_name} (SKU: {batch.product_sku})
                                                    </div>
                                                    <div className="text-xs text-gray-500 dark:text-gray-500">
                                                      Sold in invoice: {batch.sold_quantity_in_invoice} | Available: {batch.current_quantity}
                                                    </div>
                                                    {batch.quality_status !== 'GOOD' && (
                                                      <div className="text-xs text-orange-600 dark:text-orange-400">
                                                        Quality: {batch.quality_status}
                                                      </div>
                                                    )}
                                                  </div>
                                                  <div className="text-right">
                                                    <div className="text-sm font-medium text-green-600">
                                                      {formatCurrency(batch.base_price)}
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                      per unit
                                                    </div>
                                                  </div>
                                                </div>
                                              </div>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )}

                                  {/* Selected Batch Display */}
                                  {returnItem.batch > 0 && (
                                    <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900 rounded-md">
                                      <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                                        Selected: {returnItem.batch_number}
                                      </div>
                                      <div className="text-xs text-blue-700 dark:text-blue-300">
                                        {returnItem.product_name}
                                      </div>
                                    </div>
                                  )}

                                  <div className="grid grid-cols-2 gap-3">
                                    <div>
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Quantity <span className="text-red-500">*</span>
                                      </label>
                                      <input
                                        type="number"
                                        min="1"
                                        max={(() => {
                                          const batch = batchSearchResults.find(b => b.id === returnItem.batch);
                                          return batch?.sold_quantity_in_invoice || 999;
                                        })()}
                                        value={returnItem.quantity}
                                        onChange={(e) => handleQuantityChange(index, parseInt(e.target.value) || 0)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                        placeholder="0"
                                        disabled={!returnItem.batch}
                                      />
                                      {returnItem.batch > 0 && (() => {
                                        const batch = batchSearchResults.find(b => b.id === returnItem.batch);
                                        const invoiceBatch = invoiceBatches.find(ib => ib.id === returnItem.batch);
                                        const maxReturnable = batch?.sold_quantity_in_invoice || invoiceBatch?.max_returnable_quantity || 0;
                                        return maxReturnable > 0 ? (
                                          <div className="text-xs text-gray-500 mt-1">
                                            Max returnable: {maxReturnable}
                                          </div>
                                        ) : null;
                                      })()}
                                    </div>

                                    <div>
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Return Amount
                                      </label>
                                      <input
                                        type="number"
                                        step="0.01"
                                        min="0.01"
                                        value={returnItem.return_amount}
                                        onChange={(e) => updateReturn(index, 'return_amount', parseFloat(e.target.value) || 0)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white"
                                        placeholder="0.00"
                                        readOnly
                                      />
                                    </div>
                                  </div>

                                  <div className="grid grid-cols-1 gap-3 mt-3">
                                    <div>
                                      <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                        Reason
                                      </label>
                                      <select
                                        value={returnItem.reason}
                                        onChange={(e) => updateReturn(index, 'reason', e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                      >
                                        <option value="DEFECTIVE">Defective</option>
                                        <option value="EXPIRED">Expired</option>
                                        <option value="DAMAGED">Damaged</option>
                                        <option value="WRONG_PRODUCT">Wrong Product</option>
                                        <option value="CUSTOMER_REQUEST">Customer Request</option>
                                        <option value="OTHER">Other</option>
                                      </select>
                                    </div>
                                  </div>

                                  <div className="mt-3">
                                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                                      Notes (Optional)
                                    </label>
                                    <input
                                      type="text"
                                      value={returnItem.notes || ''}
                                      onChange={(e) => updateReturn(index, 'notes', e.target.value)}
                                      className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                                      placeholder="Return notes..."
                                    />
                                  </div>
                                </div>
                              ))}
                              
                              {/* Total Return Amount */}
                              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900 rounded-lg">
                                <div className="flex justify-between items-center">
                                  <span className="text-sm font-medium text-green-700 dark:text-green-300">
                                    Total Return Amount:
                                  </span>
                                  <span className="text-lg font-bold text-green-600 dark:text-green-400">
                                    {formatCurrency(getTotalReturnAmount())}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Empty State */}
                        {settlementForm.returns.length === 0 && (
                          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                            <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                              No returns added yet.
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-500 text-center mt-1">
                              Use the tabs above to add returns from invoice batches or search for other batches.
                            </p>
                          </div>
                        )}
                      </div>

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

                        {/* Settlement Summary */}
                        <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                              Total Payment Amount:
                            </span>
                            <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                              {formatCurrency(getTotalPaymentAmount())}
                            </span>
                          </div>
                          
                          {getTotalReturnAmount() > 0 && (
                            <div className="flex justify-between items-center mt-1">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Total Return Amount:
                              </span>
                              <span className="text-lg font-bold text-green-600 dark:text-green-400">
                                {formatCurrency(getTotalReturnAmount())}
                              </span>
                            </div>
                          )}
                          
                          <div className="border-t border-gray-200 dark:border-gray-600 pt-2 mt-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Total Settlement:
                              </span>
                              <span className="text-xl font-bold text-purple-600 dark:text-purple-400">
                                {formatCurrency(getTotalPaymentAmount() + getTotalReturnAmount())}
                              </span>
                            </div>
                          </div>
                          
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-sm text-gray-600 dark:text-gray-400">
                              Remaining Balance:
                            </span>
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {formatCurrency(selectedInvoice.balance_due - (getTotalPaymentAmount() + getTotalReturnAmount()))}
                            </span>
                          </div>
                          
                          {(getTotalPaymentAmount() + getTotalReturnAmount()) > selectedInvoice.balance_due && (
                            <div className="mt-2 text-sm text-red-600 dark:text-red-400">
                              ⚠️ Settlement amount exceeds outstanding balance
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
                            Settle {formatCurrency(getTotalPaymentAmount() + getTotalReturnAmount())}
                            {(settlementForm.payments.length > 1 || settlementForm.returns.length > 0) && 
                              ` (${settlementForm.payments.length + settlementForm.returns.length} items)`}
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
