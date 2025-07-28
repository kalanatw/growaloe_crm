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
  CompanySettings,
  AvailableBatch,
  CreateBatchInvoiceData,
  SalesmanAvailableProduct,
  CreateSimplifiedInvoiceData,
  UpdateCompanySettingsData,
  Delivery,
  CreateDeliveryData,
} from '../types';

// Type alias for invoice service response to maintain compatibility
export type InvoiceServiceResponse = {
  id: number;
  invoice_number: string;
  shop_name: string;
  invoice_date: string;
  net_total: number;
  paid_amount: number;
  balance_due: number;
  status: string;
  due_date?: string;
  salesman?: any;
  salesman_name?: string;
  shop?: any;
  subtotal?: number;
  tax_amount?: number;
  discount_amount?: number;
  shop_margin?: number;
  notes?: string;
  terms_conditions?: string;
  created_by?: any;
  created_at?: string;
  updated_at?: string;
};

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

  // Legacy methods for backward compatibility - will use batch data under the hood
  getSalesmanStock: async (): Promise<{ results: SalesmanStock[] }> => {
    // This method is deprecated but kept for backward compatibility
    return apiClient.get<{ results: SalesmanStock[] }>('/products/salesman-stock/');
  },

  getMySalesmanStock: async (): Promise<{
    stocks: SalesmanStock[];
    summary: {
      total_products: number;
      total_stock_value: number;
    };
  }> => {
    // This method is deprecated but kept for backward compatibility
    return apiClient.get('/products/salesman-stock/my_stock/');
  },

  getAllAvailableStock: async (): Promise<{
    stocks: SalesmanStock[];
    summary: {
      total_products: number;
      total_available_quantity: number;
    };
  }> => {
    // This method is deprecated but kept for backward compatibility
    return apiClient.get('/products/salesman-stock/all_available_stock/');
  },

  // New method for owners to get products for invoice creation
  getProductsForInvoice: async (): Promise<{
    stocks: SalesmanStock[];
    summary: {
      total_products: number;
      total_available_quantity: number;
    };
  }> => {
    return apiClient.get('/products/products/for_invoice_creation/');
  },

  getCategories: async (): Promise<{ results: Category[] }> => {
    return apiClient.get<{ results: Category[] }>('/products/categories/');
  },

  // Add new method for fetching available products with total quantities for salesmen
  getSalesmanAvailableProducts: async (): Promise<SalesmanAvailableProduct[]> => {
    return apiClient.get<SalesmanAvailableProduct[]>('/products/products/salesman-available-products/');
  },

  // Add new method for fetching available batches for salesmen
  getSalesmanAvailableBatches: async (salesmanId?: number): Promise<AvailableBatch[]> => {
    const params = salesmanId ? `?salesman_id=${salesmanId}` : '';
    return apiClient.get<AvailableBatch[]>(`/products/batches/salesman-available-batches/${params}`);
  },
};

export const invoiceService = {
  getInvoices: async (params?: any): Promise<{ results: Invoice[] }> => {
    return apiClient.get('/sales/invoices/', params);
  },

  getInvoice: async (id: number): Promise<Invoice> => {
    return apiClient.get<Invoice>(`/sales/invoices/${id}/`);
  },

  getInvoiceItems: async (invoiceId: number): Promise<any[]> => {
    return apiClient.get<any[]>(`/sales/invoice-items/?invoice=${invoiceId}`);
  },

  createInvoice: async (data: CreateInvoiceData): Promise<Invoice> => {
    return apiClient.post<Invoice>('/sales/invoices/', data);
  },

  // Add batch-aware invoice creation
  createBatchInvoice: async (data: CreateBatchInvoiceData): Promise<Invoice> => {
    return apiClient.post<Invoice>('/sales/invoices/', data);
  },

  createSimplifiedInvoice: async (data: CreateSimplifiedInvoiceData): Promise<Invoice> => {
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

  getAnalytics: async (params: { period: string }): Promise<any> => {
    // For now, return sales performance data as a fallback
    return apiClient.get('/sales/analytics/sales_performance/', { params });
  },

  getMonthlyTrends: async (): Promise<any[]> => {
    // For now, return sales performance data as monthly trends
    return apiClient.get('/sales/analytics/sales_performance/');
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

export const companyService = {
  getPublicSettings: async (): Promise<{
    company_name: string;
    company_address: string;
    company_phone: string;
    company_email: string;
    currency_symbol: string;
    default_currency: string;
    max_shop_margin_for_salesmen: number;
  }> => {
    return apiClient.get('/core/settings/public/');
  },
};

export const deliveryService = {
  // Legacy delivery methods (kept for backward compatibility)
  getDeliveries: async (): Promise<{ results: Delivery[] }> => {
    return apiClient.get<{ results: Delivery[] }>('/products/deliveries/');
  },

  getDelivery: async (id: number): Promise<Delivery> => {
    return apiClient.get<Delivery>(`/products/deliveries/${id}/`);
  },

  createDelivery: async (data: CreateDeliveryData): Promise<Delivery> => {
    return apiClient.post<Delivery>('/products/deliveries/', data);
  },

  updateDelivery: async (id: number, data: Partial<CreateDeliveryData>): Promise<Delivery> => {
    return apiClient.put<Delivery>(`/products/deliveries/${id}/`, data);
  },

  deleteDelivery: async (id: number): Promise<void> => {
    return apiClient.delete(`/products/deliveries/${id}/`);
  },

  markAsDelivered: async (id: number): Promise<Delivery> => {
    return apiClient.post<Delivery>(`/products/deliveries/${id}/mark_delivered/`);
  },

  // New salesman-centric delivery management methods
  getSalesmanOverview: async (): Promise<{
    salesmen_count: number;
    total_stock_value: number;
    total_products_distributed: number;
    salesmen: Array<{
      salesman_id: number;
      salesman_name: string;
      salesman_phone: string;
      total_products: number;
      total_stock_quantity: number;
      total_stock_value: number;
      stock_by_product: Array<{
        product_id: number;
        product_name: string;
        product_sku: string;
        unit_price: number;
        quantity: number;
        total_value: number;
      }>;
      today_sales_quantity: number;
      today_sales_revenue: number;
      pending_deliveries: number;
      last_delivery_date: string | null;
    }>;
  }> => {
    return apiClient.get('/products/salesman-deliveries/stock_overview/');
  },

  getSettlementQueue: async (): Promise<{
    salesmen_count: number;
    total_deliveries_pending: number;
    total_outstanding_value: number;
    salesmen: Array<{
      salesman_id: number;
      salesman_name: string;
      salesman_phone: string;
      deliveries: Array<{
        delivery_id: number;
        delivery_number: string;
        delivery_date: string;
        total_items: number;
        total_value: number;
        outstanding_quantity: number;
        outstanding_value: number;
        items: Array<{
          delivery_item_id: number;
          product_id: number;
          product_name: string;
          product_sku: string;
          delivered_quantity: number;
          sold_quantity: number;
          outstanding_quantity: number;
          unit_price: number;
          outstanding_value: number;
        }>;
      }>;
      total_deliveries: number;
      total_outstanding_value: number;
      oldest_delivery_date: string | null;
    }>;
  }> => {
    return apiClient.get('/products/salesman-deliveries/settlement_queue/');
  },

  getSalesmanBySummary: async (): Promise<{
    total_salesmen: number;
    salesmen_with_stock: number;
    total_outstanding_value: number;
    salesmen: Array<{
      salesman_id: number;
      salesman_name: string;
      salesman_phone: string;
      outstanding_value: number;
      outstanding_items: number;
      recent_deliveries: number;
      today_sales_revenue: number;
      status: 'has_stock' | 'no_stock';
      priority: 'high' | 'normal';
    }>;
  }> => {
    return apiClient.get('/products/deliveries/by-salesman/');
  },

  getSalesmanDeliveryDetails: async (salesmanId: number): Promise<{
    salesman: {
      id: number;
      name: string;
      phone: string;
      email: string;
      joined_date: string;
      is_active: boolean;
    };
    current_stock: {
      total_products: number;
      total_quantity: number;
      total_value: number;
      products: Array<{
        product_id: number;
        product_name: string;
        product_sku: string;
        quantity: number;
        unit_price: number;
        total_value: number;
      }>;
    };
    deliveries: {
      total_count: number;
      pending_count: number;
      delivered_count: number;
      settled_count: number;
      recent_deliveries: Delivery[];
    };
    sales_performance: {
      last_30_days: Array<{
        invoice__invoice_date__date: string;
        daily_revenue: number;
        daily_quantity: number;
      }>;
      total_revenue_30d: number;
      total_quantity_30d: number;
    };
    settlements: {
      recent_settlements: Array<any>;
      total_settlements: number;
    };
  }> => {
    return apiClient.get(`/products/deliveries/salesman/${salesmanId}/details/`);
  },

  settleSalesmanDeliveries: async (salesmanId: number, data: {
    settlement_notes?: string;
    return_all_stock?: boolean;
    create_settlement_record?: boolean;
    cash_settlement_amount?: number;
    settlement_method?: 'full_cash' | 'partial_cash' | 'balance_carry';
  }): Promise<{
    message: string;
    salesman_name: string;
    settlement_date: string;
    settled_deliveries: number;
    cash_flow: {
      total_collections: number;
      total_expenses: number;
      net_cash_available: number;
      current_balance: number;
      last_settlement_date: string | null;
    };
    cash_settlement_amount: number;
    remaining_balance: number;
    summary: {
      total_delivered_items: number;
      total_sold_items: number;
      total_returned_items: number;
      total_delivered_value: number;
      total_sold_value: number;
      total_returned_value: number;
      efficiency_rate: number;
    };
    settlement_record?: any;
  }> => {
    // Always include salesman_id in the payload
    return apiClient.post(`/products/deliveries/settle/${salesmanId}/`, {
      ...data,
      salesman_id: salesmanId,
    });
  },

  // New delivery settlement methods with cash management
  getDeliverySettlementPreview: async (salesmanId: number): Promise<{
    delivery: {
      id: number;
      delivery_number: string;
      salesman_name: string;
      delivery_date: string;
    };
    products: Array<{
      product_name: string;
      delivered_quantity: number;
      sold_quantity: number;
      returned_quantity: number;
      outstanding_quantity: number;
      unit_price: number;
      delivered_value: number;
      sold_value: number;
      outstanding_value: number;
    }>;
    cash_breakdown: {
      invoice_collections: number;
      delivery_expenses: number;
      return_value: number;
      net_cash_available: number;
      payment_methods: Array<{
        method: string;
        amount: number;
        reference?: string;
        bank?: string;
      }>;
    };
    salesman_balance: {
      current_balance: number;
      balance_after_settlement: number;
    };
  }> => {
    return apiClient.get(`/products/deliveries/settlement_preview/?salesman_id=${salesmanId}`);
  },

  processDeliverySettlement: async (data: {
    salesman_id: number;
    settlement_notes?: string;
    cash_settlement_amount: number;
    settlement_method: 'full_cash' | 'partial_cash' | 'balance_carry';
    return_all_stock?: boolean;
    create_settlement_record?: boolean;
  }): Promise<{
    success: boolean;
    message: string;
    settlement_id?: number;
    cash_transaction_id?: number;
    cash_collected: number;
    new_balance: number;
    delivery_status: string;
    delivery_id: number;
  }> => {
    return apiClient.post('/products/deliveries/process_settlement/', data);
  },

  // Get detailed invoice settlement breakdown for a delivery
  getDeliverySettlementBreakdown: async (deliveryId: number): Promise<{
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
  }> => {
    return apiClient.get(`/products/deliveries/${deliveryId}/settlement_breakdown/`);
  },

  getDailySummary: async (date?: string): Promise<{
    date: string;
    summary: {
      total_salesmen: number;
      total_deliveries: number;
      total_sales_revenue: number;
      total_outstanding_value: number;
      settlement_recommended: number;
      review_required: number;
    };
    salesmen: Array<{
      salesman_id: number;
      salesman_name: string;
      deliveries_count: number;
      deliveries_value: number;
      sales_quantity: number;
      sales_revenue: number;
      outstanding_items: number;
      outstanding_value: number;
      recommendation: 'no_action' | 'settle_recommended' | 'review_required';
      efficiency_rate: number;
    }>;
  }> => {
    const params = date ? `?date=${date}` : '';
    return apiClient.get(`/products/salesman-deliveries/daily_summary/${params}`);
  },

  // Legacy settlement methods (kept for backward compatibility)
  getSettlementData: async (id: number): Promise<{
    delivery_id: number;
    delivery_number: string;
    salesman_name: string;
    delivery_date: string;
    items: Array<{
      delivery_item_id: number;
      product_id: number;
      product_name: string;
      delivered_quantity: number;
      sold_quantity: number;
      remaining_quantity: number;
      margin_earned: number;
    }>;
  }> => {
    return apiClient.get(`/products/deliveries/${id}/settlement_data/`);
  },

  settleDelivery: async (id: number, data: {
    settlement_notes?: string;
    items: Array<{
      delivery_item_id: number;
      remaining_quantity: number;
      margin_earned: number;
    }>;
  }): Promise<{
    status: string;
    settlement_date: string;
    total_margin_earned: number;
    message: string;
  }> => {
    return apiClient.post(`/products/deliveries/${id}/settle/`, data);
  },

  getBatchAssignments: async (id: number): Promise<{
    delivery_id: number;
    delivery_number: string;
    salesman_name: string;
    delivery_date: string;
    status: string;
    items: Array<{
      delivery_item_id: number;
      product_id: number;
      product_name: string;
      product_sku: string;
      total_quantity: number;
      batch_assignments: Array<{
        batch_id: number;
        batch_number: string;
        quantity: number;
        delivered_quantity: number;
        expiry_date: string | null;
        manufacturing_date: string | null;
        unit_cost: number;
        status: string;
      }>;
    }>;
  }> => {
    return apiClient.get(`/products/deliveries/${id}/batch_assignments/`);
  },

  // Update sold quantities (called from invoice creation)
  updateSoldQuantities: async (data: {
    salesman_id: number;
    invoice_items: Array<{
      product_id: number;
      quantity: number;
      unit_price: number;
    }>;
  }): Promise<{
    message: string;
    salesman_name: string;
    updated_assignments: Array<any>;
    note: string;
  }> => {
    return apiClient.put('/products/deliveries/update-sold/', data);
  },

  getDeliveryExpenses: async (deliveryId: number, filters: any = {}) => {
    return apiClient.get('/products/delivery-expenses/', { delivery: deliveryId, ...filters });
  },

  createDeliveryExpense: async (data: {
    delivery: number;
    category: string;
    amount: number;
    ref_id?: string;
    notes?: string;
  }) => {
    return apiClient.post('/products/delivery-expenses/', data);
  },

  updateDeliveryExpense: async (id: number, data: {
    category?: string;
    amount?: number;
    ref_id?: string;
    notes?: string;
  }) => {
    return apiClient.patch(`/products/delivery-expenses/${id}/`, data);
  },

  deleteDeliveryExpense: async (id: number) => {
    return apiClient.delete(`/products/delivery-expenses/${id}/`);
  },

  // Add a method to get settlement history for a salesman
  getSettlementHistory: async (salesmanId: number) => {
    return apiClient.get('/products/delivery-settlements/', { salesman: salesmanId });
  },

  // Get salesman balance summary (uses the enhanced pending returns endpoint)
  getSalesmanBalanceSummary: async (): Promise<{
    pending_returns: {
      total_pending: number;
      total_quantity: number;
      by_reason: Record<string, { count: number; quantity: number }>;
      by_salesman: Array<{
        salesman_id: number;
        salesman_name: string;
        pending_count: number;
        pending_quantity: number;
      }>;
    };
    salesman_balances: Array<{
      salesman_id: number;
      salesman_name: string;
      current_balance: number;
      total_cash_collected: number;
      total_cash_settled: number;
      net_cash_position: number;
      last_settlement_date: string | null;
      pending_deliveries_value: number;
      outstanding_invoices_value: number;
    }>;
  }> => {
    return apiClient.get('/products/returns/pending_summary/');
  },

  // Mark cash as collected from salesman
  collectCashFromSalesman: async (data: {
    salesman_id: number;
    transaction_ids: number[];
    collected_amount: number;
    notes?: string;
  }): Promise<{
    message: string;
    salesman_name: string;
    collected_amount: number;
    transactions_updated: number;
    new_salesman_balance: number;
    total_cash_settled: number;
    collection_date: string;
  }> => {
    return apiClient.post('/products/deliveries/collect-cash/', data);
  },

  getDeliverySettlementSummary: async (deliveryId: number): Promise<{
    delivery_id: number;
    delivery_number: string;
    salesman_name: string;
    settlement_summary: {
      delivery_metrics: {
        delivery_value: number;
        delivery_date: string;
        delivery_status: string;
        total_items: number;
      };
      cash_flow: {
        total_cash_collected: number;
        cash_to_settle_to_owner: number;
        outstanding_from_customers: number;
        collection_rate_percentage: number;
      };
      product_tracking: {
        product_value_in_circulation: number;
        circulation_percentage: number;
        conversion_rate: number;
      };
      invoice_breakdown: {
        total_invoices: number;
        total_invoice_amount: number;
        paid_invoices: number;
        pending_invoices: number;
        partial_invoices: number;
      };
      daily_settlements: Array<{
        date: string;
        cash_collected: number;
        invoice_count: number;
        settlement_due: number;
      }>;
      payment_methods: Array<{
        method: string;
        amount: number;
        transaction_count: number;
        percentage: number;
      }>;
    };
  }> => {
    return apiClient.get(`/products/deliveries/${deliveryId}/settlement_summary/`);
  },

  collectPhysicalCash: async (data: {
    settlement_id: number;
    amount_collected: number;
    collection_method: 'full_amount' | 'partial_amount' | 'excess_returned';
    collection_notes?: string;
  }): Promise<{
    success: boolean;
    message: string;
    settlement_id: number;
    amount_collected: number;
    salesman_name: string;
    new_balance: number;
    collection_date: string;
    next_delivery_ready: boolean;
    collection_method: string;
    audit_trail: {
      collected_by: string;
      collection_notes: string;
      transaction_created: boolean;
    };
  }> => {
    return apiClient.post('/products/deliveries/collect_physical_cash/', data);
  },
};



// Cash Flow Management Services
export const cashFlowService = {
  getSalesmanCashSummary: async (salesmanId: number, days: number = 30): Promise<{
    total_collections: number;
    total_settlements: number;
    total_expenses: number;
    current_balance: number;
    net_cash_position: number;
    transaction_count: number;
    period_days: number;
  }> => {
    return apiClient.get(`/auth/salesmen/${salesmanId}/cash-summary/?days=${days}`);
  },

  recordCashCollection: async (data: {
    invoice_id: number;
    amount: number;
    notes?: string;
  }): Promise<{
    message: string;
    transaction_id: number;
    new_balance: number;
  }> => {
    return apiClient.post('/auth/cash-collection/', data);
  },

  getCashTransactionHistory: async (salesmanId: number, limit: number = 50): Promise<Array<{
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
  }>> => {
    return apiClient.get(`/auth/salesmen/${salesmanId}/cash-transactions/?limit=${limit}`);
  },

  getSettlementCashFlow: async (salesmanId: number): Promise<{
    total_collections: number;
    total_expenses: number;
    net_cash_available: number;
    current_balance: number;
    last_settlement_date: string | null;
  }> => {
    return apiClient.get(`/auth/salesmen/${salesmanId}/settlement-cash-flow/`);
  },

  recordAdvancePayment: async (salesmanId: number, data: {
    amount: number;
    notes?: string;
  }): Promise<{
    message: string;
    transaction_id: number;
    new_balance: number;
  }> => {
    return apiClient.post(`/auth/salesmen/${salesmanId}/advance-payment/`, data);
  },
};