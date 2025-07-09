import { apiClient } from './api';

const API_BASE_URL = '/core';

export interface FinanceTransaction {
  id: number;
  description: string;
  amount: number;
  category: {
    id: number;
    name: string;
    transaction_type: 'income' | 'expense';
  };
  transaction_date: string;
  reference_number?: string;
  notes?: string;
  created_by: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface TransactionCategory {
  id: number;
  name: string;
  transaction_type: 'income' | 'expense';
  description?: string;
  is_active: boolean;
}

export interface ProfitSummary {
  date: string;
  realized_profit: number;
  unrealized_profit: number;
  spendable_profit: number;
  collection_efficiency: number;
  calculation_time: string;
}

export interface FinancialDashboardData {
  realized_profit: number;
  unrealized_profit: number;
  spendable_profit: number;
  recent_transactions: FinanceTransaction[];
  pending_commissions: number;
  last_updated: string;
  total_income: number;
  total_expenses: number;
  net_profit: number;
  unsettled_invoices_amount: number;
  collection_efficiency: number;
}

export interface CreateTransactionData {
  description: string;
  amount: number;
  category: number;
  transaction_date: string;
  reference_number?: string;
  notes?: string;
}

export interface CommissionRecord {
  id: number;
  invoice: {
    id: number;
    invoice_number: string;
  };
  salesman: {
    id: number;
    user: {
      first_name: string;
      last_name: string;
    };
  };
  commission_amount: number;
  status: 'calculated' | 'pending' | 'paid' | 'cancelled';
  payment_date?: string;
}

// Enhanced interfaces for detailed breakdowns
export interface RealizedProfitBreakdown {
  cash_from_settlements: {
    total: number;
    details: Array<{
      settlement_id: number;
      invoice_number: string;
      shop_name: string;
      settlement_date: string;
      amount: number;
      profit_portion: number;
    }>;
  };
  commissions_paid: {
    total: number;
    details: Array<{
      commission_id: number;
      salesman_name: string;
      invoice_number: string;
      amount: number;
      payment_date: string;
    }>;
  };
  additional_income: {
    total: number;
    details: Array<{
      transaction_id: number;
      description: string;
      category: string;
      amount: number;
      date: string;
    }>;
  };
  expenses: {
    total: number;
    details: Array<{
      transaction_id: number;
      description: string;
      category: string;
      amount: number;
      date: string;
    }>;
  };
  realized_profit: number;
  calculation_date: string;
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface UnrealizedProfitBreakdown {
  outstanding_invoices: {
    total: number;
    count: number;
    details: Array<{
      invoice_id: number;
      invoice_number: string;
      shop_name: string;
      invoice_date: string;
      amount_due: number;
      days_outstanding: number;
      estimated_profit: number;
    }>;
  };
  estimated_commissions: {
    total: number;
    details: Array<{
      commission_id: number | null;
      salesman_name: string;
      invoice_number: string;
      estimated_amount: number;
      status: string;
    }>;
  };
  unrealized_profit: number;
  collection_efficiency: number;
  expected_collections: number;
  potential_bad_debt: number;
  calculation_date: string;
  period: {
    start_date: string;
    end_date: string;
  };
}

export interface SpendableProfitData {
  realized_profit: number;
  outstanding_invoice_risk: number;
  spendable_profit: number;
  risk_adjusted_spendable: number;
  risk_assessment: {
    level: string;
    high_risk_invoices: number;
    medium_risk_invoices: number;
    low_risk_invoices: number;
  };
  recommended_cash_reserve: number;
  safe_to_spend_amount: number;
  calculation_date: string;
}

export interface ProfitBreakdown {
  type: 'realized' | 'unrealized' | 'spendable';
  amount: number;
  components: {
    sales_revenue?: number;
    collection_amount?: number;
    outstanding_invoices?: number;
    pending_commissions?: number;
    recent_collections?: number;
    calculation_details?: string;
  };
  date_range: {
    start_date: string;
    end_date: string;
  };
  last_updated: string;
}

export interface DetailedProfitAnalysis {
  realized: ProfitBreakdown;
  unrealized: ProfitBreakdown;
  spendable: ProfitBreakdown;
  summary: {
    total_sales: number;
    total_collections: number;
    total_outstanding: number;
    collection_efficiency: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

// Finance Service
export const financeService = {
  // Transaction Categories
  getCategories: async (): Promise<TransactionCategory[]> => {
    return await apiClient.get(`${API_BASE_URL}/categories/`);
  },

  // Financial Transactions
  getTransactions: async (params: {
    category?: number;
    start_date?: string;
    end_date?: string;
    transaction_type?: 'income' | 'expense';
    search?: string;
    page?: number;
  } = {}): Promise<{ results: FinanceTransaction[]; count: number }> => {
    return await apiClient.get(`${API_BASE_URL}/transactions/`, params);
  },

  createTransaction: async (data: CreateTransactionData): Promise<FinanceTransaction> => {
    return await apiClient.post(`${API_BASE_URL}/transactions/`, data);
  },

  updateTransaction: async (id: number, data: Partial<CreateTransactionData>): Promise<FinanceTransaction> => {
    return await apiClient.patch(`${API_BASE_URL}/transactions/${id}/`, data);
  },

  deleteTransaction: async (id: number): Promise<void> => {
    await apiClient.delete(`${API_BASE_URL}/transactions/${id}/`);
  },

  // Transaction Summary
  getTransactionSummary: async (params: {
    start_date?: string;
    end_date?: string;
    type?: 'income' | 'expense';
  } = {}) => {
    return await apiClient.get(`${API_BASE_URL}/transactions/summary/`, params);
  },

  // Profit Calculations
  getRealizedProfit: async (date?: string): Promise<ProfitSummary> => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/profits/realized/`, params);
  },

  getUnrealizedProfit: async (date?: string): Promise<ProfitSummary> => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/profits/unrealized/`, params);
  },

  getSpendableProfit: async (date?: string): Promise<ProfitSummary> => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/profits/spendable/`, params);
  },

  getProfitSummary: async (date?: string): Promise<ProfitSummary> => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/profits/summary/`, params);
  },

  // Financial Dashboard
  getDashboard: async (): Promise<FinancialDashboardData> => {
    return await apiClient.get(`${API_BASE_URL}/dashboard/`);
  },

  // Enhanced profit calculations with detailed breakdowns
  getRealizedProfitDetailed: async (start_date?: string, end_date?: string) => {
    const params: any = {};
    if (start_date) params.start_date = start_date;
    if (end_date) params.end_date = end_date;
    return await apiClient.get(`${API_BASE_URL}/transactions/realized_breakdown/`, params);
  },
  
  getUnrealizedProfitDetailed: async (start_date?: string, end_date?: string) => {
    const params: any = {};
    if (start_date) params.start_date = start_date;
    if (end_date) params.end_date = end_date;
    return await apiClient.get(`${API_BASE_URL}/transactions/unrealized_breakdown/`, params);
  },
  
  getSpendableProfitAnalysis: async () => {
    return await apiClient.get(`${API_BASE_URL}/transactions/spendable_analysis/`);
  },

  getCashFlowProjection: async (days: number = 30) => {
    return await apiClient.get(`${API_BASE_URL}/reports/cash-flow-projection/`, { days });
  },
  
  getCommissionStatus: async () => {
    return await apiClient.get(`${API_BASE_URL}/commissions/summary/`);
  },

  // Reports
  getDailyReport: async (date?: string) => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/reports/daily/`, params);
  },

  getWeeklyReport: async (date?: string) => {
    const params = date ? { date } : {};
    return await apiClient.get(`${API_BASE_URL}/reports/weekly/`, params);
  },

  getMonthlyReport: async (year?: number, month?: number) => {
    const params: any = {};
    if (year) params.year = year;
    if (month) params.month = month;
    return await apiClient.get(`${API_BASE_URL}/reports/monthly/`, params);
  },

  // Commission Management
  getCommissions: async (params: {
    status?: string;
    salesperson?: number;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<{ results: CommissionRecord[]; count: number }> => {
    return await apiClient.get(`${API_BASE_URL}/commissions/`, params);
  },

  getCommissionSummary: async (params: {
    status?: string;
    salesperson?: number;
    start_date?: string;
    end_date?: string;
  } = {}) => {
    return await apiClient.get(`${API_BASE_URL}/commissions/summary/`, params);
  },

  // Collection Efficiency
  getCollectionEfficiency: async (start_date: string, end_date: string) => {
    return await apiClient.get(`${API_BASE_URL}/reports/collection-efficiency/`, {
      start_date,
      end_date
    });
  },

  // Description Suggestions
  getDescriptionSuggestions: async (query?: string, category?: number, limit: number = 10) => {
    const params: any = { limit };
    if (query) params.q = query;
    if (category) params.category = category;
    return await apiClient.get(`${API_BASE_URL}/transactions/suggestions/`, params);
  },

  // Profit Analysis
  getProfitBreakdown: async (start_date: string, end_date: string): Promise<DetailedProfitAnalysis> => {
    return await apiClient.get(`${API_BASE_URL}/reports/profit_breakdown/`, {
      start_date,
      end_date
    });
  },

  getRealizedProfitBreakdown: async (start_date: string, end_date: string): Promise<ProfitBreakdown> => {
    const result: DetailedProfitAnalysis = await apiClient.get(`${API_BASE_URL}/reports/profit_breakdown/`, {
      start_date,
      end_date
    });
    return result.realized;
  },

  getUnrealizedProfitBreakdown: async (start_date: string, end_date: string): Promise<ProfitBreakdown> => {
    const result: DetailedProfitAnalysis = await apiClient.get(`${API_BASE_URL}/reports/profit_breakdown/`, {
      start_date,
      end_date
    });
    return result.unrealized;
  },

  getSpendableProfitBreakdown: async (start_date: string, end_date: string): Promise<ProfitBreakdown> => {
    const result: DetailedProfitAnalysis = await apiClient.get(`${API_BASE_URL}/reports/profit_breakdown/`, {
      start_date,
      end_date
    });
    return result.spendable;
  }
};

export default financeService;
