import { apiClient } from './api';
import { 
  FinancialTransaction, 
  CreateFinancialTransactionData, 
  FinancialDashboard,
  BankBook,
  InvoiceSettlement
} from '../types';

const API_BASE_URL = '/core';

// Financial Transaction Service
export const financialTransactionService = {
  // Get all financial transactions with filtering
  getTransactions: async (params: {
    transaction_type?: string;
    category?: string;
    date_from?: string;
    date_to?: string;
    search?: string;
    page?: number;
  } = {}) => {
    return await apiClient.get(`${API_BASE_URL}/financial-transactions/`, params);
  },

  // Create a new financial transaction
  createTransaction: async (data: CreateFinancialTransactionData): Promise<FinancialTransaction> => {
    return await apiClient.post(`${API_BASE_URL}/financial-transactions/`, data);
  },

  // Update a financial transaction
  updateTransaction: async (id: number, data: Partial<CreateFinancialTransactionData>): Promise<FinancialTransaction> => {
    return await apiClient.patch(`${API_BASE_URL}/financial-transactions/${id}/`, data);
  },

  // Delete a financial transaction
  deleteTransaction: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_BASE_URL}/financial-transactions/${id}/`);
  },

  // Get financial transactions summary
  getSummary: async (date_from?: string, date_to?: string) => {
    const params: any = {};
    if (date_from) params.date_from = date_from;
    if (date_to) params.date_to = date_to;
    
    return await apiClient.get(`${API_BASE_URL}/financial-transactions/summary/`, params);
  },

  // Get categories for dropdowns
  getCategories: () => {
    return {
      credit: [
        { value: 'invoice_settlement', label: 'Invoice Settlement' },
        { value: 'cash_sale', label: 'Cash Sale' },
        { value: 'other_income', label: 'Other Income' },
        { value: 'loan_received', label: 'Loan Received' },
        { value: 'capital_injection', label: 'Capital Injection' },
        { value: 'refund_received', label: 'Refund Received' },
      ],
      debit: [
        { value: 'invoice_created', label: 'Invoice Created' },
        { value: 'purchase', label: 'Purchase' },
        { value: 'rent', label: 'Rent' },
        { value: 'utilities', label: 'Utilities' },
        { value: 'salaries', label: 'Salaries' },
        { value: 'transport', label: 'Transport' },
        { value: 'marketing', label: 'Marketing' },
        { value: 'office_expenses', label: 'Office Expenses' },
        { value: 'agency_payment', label: 'Agency Payment' },
        { value: 'loan_payment', label: 'Loan Payment' },
        { value: 'tax_payment', label: 'Tax Payment' },
        { value: 'bank_charges', label: 'Bank Charges' },
        { value: 'other_expense', label: 'Other Expense' },
      ]
    };
  }
};

// Invoice Settlement Service
export const invoiceSettlementService = {
  // Get all invoice settlements
  getSettlements: async (params: {
    invoice_id?: number;
    payment_method?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
  } = {}) => {
    return await apiClient.get(`${API_BASE_URL}/invoice-settlements/`, params);
  },

  // Create a new settlement
  createSettlement: async (data: {
    invoice: number;
    settlement_date: string;
    amount: number;
    payment_method: string;
    reference_number?: string;
    bank_name?: string;
    cheque_date?: string;
    notes?: string;
  }): Promise<InvoiceSettlement> => {
    return await apiClient.post(`${API_BASE_URL}/invoice-settlements/`, data);
  },

  // Update a settlement
  updateSettlement: async (id: number, data: any): Promise<InvoiceSettlement> => {
    return await apiClient.patch(`${API_BASE_URL}/invoice-settlements/${id}/`, data);
  },

  // Delete a settlement
  deleteSettlement: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_BASE_URL}/invoice-settlements/${id}/`);
  },

  // Get settlement summary
  getSummary: async (date_from?: string, date_to?: string) => {
    const params: any = {};
    if (date_from) params.date_from = date_from;
    if (date_to) params.date_to = date_to;
    
    return await apiClient.get(`${API_BASE_URL}/invoice-settlements/summary/`, params);
  }
};

// Financial Dashboard Service
export const financialDashboardService = {
  // Get comprehensive financial dashboard
  getDashboard: async (date_from?: string, date_to?: string): Promise<FinancialDashboard> => {
    const params: any = {};
    if (date_from) params.date_from = date_from;
    if (date_to) params.date_to = date_to;
    
    return await apiClient.get(`${API_BASE_URL}/financial-dashboard/dashboard/`, params);
  },

  // Get bank book view
  getBankBook: async (date_from?: string, date_to?: string): Promise<BankBook> => {
    const params: any = {};
    if (date_from) params.date_from = date_from;
    if (date_to) params.date_to = date_to;
    
    return await apiClient.get(`${API_BASE_URL}/financial-dashboard/bank_book/`, params);
  }
};
