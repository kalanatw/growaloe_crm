import { apiClient } from './api';
import {
  User,
  Shop,
  Product,
  Category,
  SalesmanStock,
  Invoice,
  Transaction,
  Salesman,
  CreateInvoiceData,
  CreateShopData,
  CreateTransactionData,
  CreateSalesmanData,
  CreateProductData,
  SalesAnalytics,
  MonthlyTrend,
  TopProduct,
  AnalyticsData,
  CompanySettings,
  UpdateCompanySettingsData,
} from '../types';

export const authService = {
  login: async (username: string, password: string) => {
    return apiClient.post<{ access: string; refresh: string }>('/auth/login/', {
      username,
      password,
    });
  },

  getProfile: async (): Promise<User> => {
    return apiClient.get<User>('/auth/profile/');
  },

  refreshToken: async (refresh: string) => {
    return apiClient.post<{ access: string }>('/auth/refresh/', { refresh });
  },
};

export const shopService = {
  getShops: async (): Promise<{ results: Shop[] }> => {
    return apiClient.get<{ results: Shop[] }>('/auth/shops/');
  },

  getShop: async (id: number): Promise<Shop> => {
    return apiClient.get<Shop>(`/auth/shops/${id}/`);
  },

  createShop: async (data: CreateShopData): Promise<Shop> => {
    return apiClient.post<Shop>('/auth/shops/', data);
  },

  updateShop: async (id: number, data: Partial<CreateShopData>): Promise<Shop> => {
    return apiClient.patch<Shop>(`/auth/shops/${id}/`, data);
  },

  getShopSummary: async (): Promise<Shop[]> => {
    return apiClient.get<Shop[]>('/auth/shops/summary/');
  },

  getShopBalanceHistory: async (shopId: number) => {
    return apiClient.get(`/auth/shops/${shopId}/balance_history/`);
  },
};

export const productService = {
  getProducts: async (): Promise<{ results: Product[] }> => {
    return apiClient.get<{ results: Product[] }>('/products/products/');
  },

  getProduct: async (id: number): Promise<Product> => {
    return apiClient.get<Product>(`/products/products/${id}/`);
  },

  createProduct: async (data: CreateProductData): Promise<Product> => {
    return apiClient.post<Product>('/products/products/', data);
  },

  updateProduct: async (id: number, data: Partial<CreateProductData>): Promise<Product> => {
    return apiClient.patch<Product>(`/products/products/${id}/`, data);
  },

  deleteProduct: async (id: number): Promise<void> => {
    return apiClient.delete(`/products/products/${id}/`);
  },

  getProductStockSummary: async (): Promise<{ results: any[] }> => {
    return apiClient.get('/products/products/stock_summary/');
  },

  getSalesmanStock: async (): Promise<{ results: SalesmanStock[] }> => {
    return apiClient.get<{ results: SalesmanStock[] }>('/products/salesman-stock/');
  },

  getMySalesmanStock: async (): Promise<{
    stocks: SalesmanStock[];
    summary: {
      total_products: number;
      total_stock_value: number;
    };
  }> => {
    return apiClient.get('/products/salesman-stock/my_stock/');
  },

  getCategories: async (): Promise<{ results: Category[] }> => {
    return apiClient.get<{ results: Category[] }>('/products/categories/');
  },
};

export const invoiceService = {
  getInvoices: async (params?: any): Promise<{ results: Invoice[] }> => {
    return apiClient.get<{ results: Invoice[] }>('/sales/invoices/', params);
  },

  getInvoice: async (id: number): Promise<Invoice> => {
    return apiClient.get<Invoice>(`/sales/invoices/${id}/`);
  },

  createInvoice: async (data: CreateInvoiceData): Promise<Invoice> => {
    return apiClient.post<Invoice>('/sales/invoices/', data);
  },

  updateInvoice: async (id: number, data: Partial<Invoice>): Promise<Invoice> => {
    return apiClient.patch<Invoice>(`/sales/invoices/${id}/`, data);
  },

  generateInvoicePDF: async (id: number) => {
    const blob = await apiClient.downloadFile(`/sales/invoices/${id}/generate_pdf/`);
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `invoice_${id}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    return blob;
  },

  updateInvoiceStatus: async (id: number, status: string) => {
    return apiClient.patch(`/sales/invoices/${id}/update_status/`, { status });
  },
};

export const transactionService = {
  getTransactions: async (params?: any): Promise<{ results: Transaction[]; count: number }> => {
    return apiClient.get<{ results: Transaction[]; count: number }>('/sales/transactions/', params);
  },

  createTransaction: async (data: CreateTransactionData): Promise<Transaction> => {
    return apiClient.post<Transaction>('/sales/transactions/', data);
  },

  getTransactionSummary: async () => {
    return apiClient.get('/sales/transactions/summary/');
  },

  getOutstandingInvoices: async (shopId: number): Promise<{
    shop: { id: number; name: string; contact_person: string };
    invoices: Array<{
      id: number;
      invoice_number: string;
      invoice_date: string;
      net_total: number;
      paid_amount: number;
      balance_due: number;
      status: string;
      due_date?: string;
    }>;
    total_outstanding: number;
  }> => {
    return apiClient.get(`/sales/transactions/outstanding_invoices/?shop_id=${shopId}`);
  },

  getTotalDebits: async (): Promise<{
    total_debits: number;
    invoices_count: number;
    by_status: { pending: number; partial: number; overdue: number };
    by_shop: Array<{
      shop__id: number;
      shop__name: string;
      outstanding_amount: number;
      invoices_count: number;
    }>;
  }> => {
    return apiClient.get('/sales/transactions/total_debits/');
  },

  settleInvoice: async (data: {
    invoice_id: number;
    amount: number;
    payment_method: string;
    reference_number?: string;
    notes?: string;
  }): Promise<{
    transaction_id: number;
    invoice: {
      id: number;
      invoice_number: string;
      previous_balance: number;
      payment_amount: number;
      new_balance: number;
      status: string;
    };
    message: string;
  }> => {
    return apiClient.post('/sales/transactions/settle_invoice/', data);
  },

  settleInvoiceMultiPayment: async (data: {
    invoice_id: number;
    payments: Array<{
      payment_method: string;
      amount: number;
      reference_number?: string;
      bank_name?: string;
      cheque_date?: string;
      notes?: string;
    }>;
    notes?: string;
  }): Promise<{
    settlement_id: number;
    invoice: {
      id: number;
      invoice_number: string;
      previous_balance: number;
      total_payment_amount: number;
      new_balance: number;
      status: string;
    };
    payments: Array<{
      payment_method: string;
      amount: number;
      reference_number: string;
    }>;
    message: string;
  }> => {
    return apiClient.post('/sales/transactions/settle_invoice_multi_payment/', data);
  },
};

export const analyticsService = {
  getSalesPerformance: async (): Promise<SalesAnalytics[]> => {
    return apiClient.get<SalesAnalytics[]>('/sales/analytics/sales_performance/');
  },

  getMonthlyTrends: async (): Promise<MonthlyTrend[]> => {
    return apiClient.get<MonthlyTrend[]>('/sales/analytics/monthly_trends/');
  },

  getTopProducts: async (): Promise<TopProduct[]> => {
    return apiClient.get<TopProduct[]>('/sales/analytics/top_products/');
  },

  getAnalytics: async (params?: { period?: string }): Promise<AnalyticsData> => {
    return apiClient.get<AnalyticsData>('/sales/analytics/dashboard/', params);
  },
};

export const salesmanService = {
  getSalesmen: async (): Promise<{ results: Salesman[] }> => {
    return apiClient.get<{ results: Salesman[] }>('/auth/salesmen/');
  },

  getSalesman: async (id: number): Promise<Salesman> => {
    return apiClient.get<Salesman>(`/auth/salesmen/${id}/`);
  },

  createSalesman: async (data: CreateSalesmanData): Promise<Salesman> => {
    return apiClient.post<Salesman>('/auth/salesmen/', data);
  },

  updateSalesman: async (id: number, data: Partial<CreateSalesmanData>): Promise<Salesman> => {
    return apiClient.patch<Salesman>(`/auth/salesmen/${id}/`, data);
  },

  deleteSalesman: async (id: number): Promise<void> => {
    return apiClient.delete(`/auth/salesmen/${id}/`);
  },

  toggleSalesmanStatus: async (id: number, is_active: boolean): Promise<Salesman> => {
    return apiClient.patch<Salesman>(`/auth/salesmen/${id}/`, { is_active });
  },
};

export const companySettingsService = {
  getSettings: async (): Promise<CompanySettings> => {
    return apiClient.get<CompanySettings>('/core/settings/');
  },

  updateSettings: async (data: UpdateCompanySettingsData): Promise<CompanySettings> => {
    return apiClient.patch<CompanySettings>('/core/settings/1/', data);
  },

  resetToDefaults: async (): Promise<CompanySettings> => {
    return apiClient.post<CompanySettings>('/core/settings/reset_defaults/');
  },

  getTemplatePreview: async (): Promise<any> => {
    return apiClient.get('/core/settings/template_preview/');
  },
};
