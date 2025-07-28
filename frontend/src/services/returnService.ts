import { apiClient } from './api';

export interface ProductReturn {
  id: number;
  batch_assignment: number;
  return_quantity: number;
  return_reason: string;
  return_notes: string;
  status: 'pending' | 'approved' | 'disposed';
  return_date: string;
  processed_date?: string;
  processed_by_name?: string;
  processing_notes?: string;
  created_by_name: string;
  product_name: string;
  product_sku: string;
  batch_number: string;
  salesman_name: string;
  delivery_number: string;
}

export interface CreateProductReturn {
  batch_assignment: number;
  return_quantity: number;
  return_reason: string;
  return_notes?: string;
}

export interface PendingReturnsSummary {
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
}

export interface ProcessReturnRequest {
  action: 'approve' | 'dispose';
  processing_notes?: string;
}

export interface BulkProcessRequest {
  return_ids: number[];
  action: 'approve' | 'dispose';
  processing_notes?: string;
}

export const returnService = {
  // Get all returns with optional filters
  getReturns: async (params?: {
    status?: string;
    return_reason?: string;
    salesman?: number;
    product?: number;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<{ results: ProductReturn[]; count: number; next?: string; previous?: string }> => {
    const queryParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const url = `/products/returns/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(url);
  },

  // Get a specific return by ID
  getReturn: async (id: number): Promise<ProductReturn> => {
    return apiClient.get(`/products/returns/${id}/`);
  },

  // Create a new return
  createReturn: async (data: CreateProductReturn): Promise<ProductReturn> => {
    return apiClient.post('/products/returns/', data);
  },

  // Approve a return
  approveReturn: async (id: number, processing_notes?: string): Promise<{ message: string; return_id: number; status: string; processed_date: string }> => {
    return apiClient.post(`/products/returns/${id}/approve_return/`, {
      action: 'approve',
      processing_notes: processing_notes || ''
    });
  },

  // Dispose a return
  disposeReturn: async (id: number, processing_notes?: string): Promise<{ message: string; return_id: number; status: string; processed_date: string }> => {
    return apiClient.post(`/products/returns/${id}/dispose_return/`, {
      action: 'dispose',
      processing_notes: processing_notes || ''
    });
  },

  // Get pending returns summary
  getPendingReturnsSummary: async (): Promise<PendingReturnsSummary> => {
    return apiClient.get('/products/returns/pending_summary/');
  },

  // Bulk process returns
  bulkProcessReturns: async (data: BulkProcessRequest): Promise<{
    message: string;
    processed_count: number;
    total_requested: number;
    errors?: string[];
  }> => {
    return apiClient.post('/products/returns/bulk_process/', data);
  },

  // Get stock overview for a product
  getStockOverview: async (productId: number): Promise<{
    product_id: number;
    product_name: string;
    product_sku: string;
    total_stock: number;
    allocated_stock: number;
    available_stock: number;
    pending_returns: number;
    approved_returns_today: number;
    disposed_returns_today: number;
    sales_today: number;
    salesmen_count: number;
    low_stock_alert: boolean;
    salesman_breakdown: Array<{
      salesman_id: number;
      salesman_name: string;
      outstanding_quantity: number;
      pending_returns: number;
    }>;
  }> => {
    return apiClient.get(`/products/products/${productId}/stock_overview/`);
  }
};

export default returnService;