import { apiClient } from './api';

export interface BatchSearchResult {
  id: number;
  batch_number: string;
  product_name: string;
  product_id: number;
  product_sku: string;
  current_quantity: number;
  sold_quantity_in_invoice: number;
  expiry_date: string;
  manufacturing_date: string;
  unit_cost: number;
  base_price: number;
  cost_price: number;
  quality_status: string;
}

export interface InvoiceBatchInfo {
  id: number;
  batch_number: string;
  product_id: number;
  product_name: string;
  product_sku: string;
  sold_quantity: number;
  already_returned: number;
  max_returnable_quantity: number;
  unit_price: number;
  total_amount: number;
  manufacturing_date: string;
  expiry_date: string;
  quality_status: string;
  can_return: boolean;
}

export interface InvoiceBatchesResponse {
  invoice_id: number;
  invoice_number: string;
  shop_name: string;
  batches: InvoiceBatchInfo[];
  total_batches: number;
}

export interface QuickReturnCalculation {
  unit_return_amount: number;
  base_return_amount: number;
  quality_deduction: number;
  total_return_amount: number;
  original_unit_price: number;
  original_cost_price?: number;
  shop_margin_percentage?: number;
  shop_margin_amount?: number;
  max_returnable_quantity: number;
  already_returned: number;
  calculation_valid: boolean;
  batch_quality_status: string;
  margin_source?: string;
  return_quantity?: number; // Added field to include the return quantity
  calculation_details: {
    base_calculation: string;
    quality_impact: string;
    final_amount: number;
    margin_calculation?: string;
  };
}

export interface BatchSearchParams {
  batch_number?: string;
  product_id?: number;
  salesman_id?: number;
}

export interface BatchInfo {
  batch_id: number;
  batch_number: string;
  product_name: string;
  product_sku: string;
  manufacturing_date: string;
  expiry_date: string;
  initial_quantity: number;
  current_quantity: number;
  total_sold: number;
  total_returned: number;
  return_rate: number;
  quality_status: string;
  shops_sold_to: any[];
}

export interface BatchReturn {
  id: number;
  return_number: string;
  invoice_number: string;
  product_name: string;
  product_sku: string;
  batch_number: string;
  batch_expiry_date: string;
  quantity: number;
  reason: string;
  return_amount: number;
  approved: boolean;
  shop_name: string;
  salesman_name: string;
  created_at: string;
  notes?: string;
}

export interface ReturnCreateData {
  original_invoice: number;
  product: number;
  batch: number;  // Make batch required for batch-centric returns
  batch_number?: string;  // For display purposes
  product_name?: string;  // For display purposes
  quantity: number;
  reason: string;
  return_amount: number;
  notes?: string;
}

export interface InvoiceSettlementWithReturns {
  invoice_id: number;
  returns?: ReturnCreateData[];
  payments?: Array<{
    payment_method: string;
    amount: number;
    reference_number?: string;
    bank_name?: string;
    cheque_date?: string;
    notes?: string;
  }>;
  settlement_notes?: string;
}

export interface BatchTraceability {
  batch_id: number;
  batch_number: string;
  product_name: string;
  product_sku: string;
  manufacturing_date: string;
  expiry_date: string;
  initial_quantity: number;
  current_quantity: number;
  total_sold: number;
  total_returned: number;
  shops_sold_to: Array<{
    shop_id: number;
    shop_name: string;
    invoice_id: number;
    invoice_number: string;
    quantity_sold: number;
    unit_price: number;
    salesman_name: string;
    sale_date: string;
  }>;
  shops_returned_from: Array<{
    shop_id: number;
    shop_name: string;
    return_id: number;
    return_number: string;
    quantity_returned: number;
    return_amount: number;
    reason: string;
    return_date: string;
  }>;
  salesmen_assigned: Array<{
    salesman_id: number;
    salesman_name: string;
    assigned_quantity: number;
    delivered_quantity: number;
    returned_quantity: number;
    outstanding_quantity: number;
    assignment_date: string;
    status: string;
  }>;
  quality_status: string;
  return_rate: number;
  is_expired: boolean;
}

export interface ReturnsAnalytics {
  period: string;
  total_returns: number;
  total_return_amount: number;
  returns_by_reason: Array<{
    reason: string;
    count: number;
    amount: number;
  }>;
  daily_trends: Array<{
    date: string;
    count: number;
    amount: number;
  }>;
  top_returned_products: Array<{
    product__name: string;
    product__sku: string;
    count: number;
    amount: number;
  }>;
  batch_analysis: Array<{
    batch__batch_number: string;
    batch__product__name: string;
    count: number;
    amount: number;
  }>;
}

class BatchReturnService {
  private baseURL = 'sales/batch-returns';

  async getReturns(params?: any): Promise<{ results: BatchReturn[]; count: number }> {
    return apiClient.get<{ results: BatchReturn[]; count: number }>(this.baseURL + '/', params);
  }

  async getReturn(id: number): Promise<BatchReturn> {
    return apiClient.get<BatchReturn>(`${this.baseURL}/${id}/`);
  }

  async createReturn(data: ReturnCreateData): Promise<BatchReturn> {
    return apiClient.post<BatchReturn>(this.baseURL + '/', data);
  }

  async updateReturn(id: number, data: Partial<ReturnCreateData>): Promise<BatchReturn> {
    return apiClient.patch<BatchReturn>(`${this.baseURL}/${id}/`, data);
  }

  async deleteReturn(id: number): Promise<void> {
    return apiClient.delete(`${this.baseURL}/${id}/`);
  }

  async approveReturn(id: number): Promise<{ success: boolean; message: string }> {
    return apiClient.post<{ success: boolean; message: string }>(`${this.baseURL}/${id}/approve/`);
  }

  async searchBatches(params: BatchSearchParams): Promise<{ batches: BatchInfo[]; total_found: number }> {
    return apiClient.get<{ batches: BatchInfo[]; total_found: number }>(`${this.baseURL}/search_batches/`, params);
  }

  async searchBatchesForSettlement(query: string, invoiceId?: number): Promise<BatchSearchResult[]> {
    const params: any = { q: query };
    if (invoiceId) {
      params.invoice_id = invoiceId;
    }
    return apiClient.get<BatchSearchResult[]>(`${this.baseURL}/batch_search/`, params);
  }

  async calculateReturnAmount(data: {
    batch_id: number;
    quantity: number;
    original_invoice_id: number;
  }): Promise<QuickReturnCalculation> {
    return apiClient.post<QuickReturnCalculation>(`${this.baseURL}/calculate_return_amount/`, data);
  }

  async getInvoiceBatches(invoiceId: number): Promise<InvoiceBatchesResponse> {
    return apiClient.get<InvoiceBatchesResponse>(`${this.baseURL}/invoice_batches/`, {
      invoice_id: invoiceId
    });
  }

  async quickReturnCalculation(data: {
    invoice_id: number;
    batch_id: number;
    return_quantity: number;
  }): Promise<QuickReturnCalculation> {
    return apiClient.post<QuickReturnCalculation>(`${this.baseURL}/quick_return_calculation/`, data);
  }

  async getBatchTraceability(batchId: number): Promise<BatchTraceability> {
    return apiClient.get<BatchTraceability>(`${this.baseURL}/batch_traceability/`, {
      batch_id: batchId
    });
  }

  async processSettlementWithReturns(data: InvoiceSettlementWithReturns): Promise<{
    success: boolean;
    settlement_id: number;
    returns_created: number;
    total_return_amount: number;
    settlement_amount: number;
    message: string;
  }> {
    return apiClient.post<{
      success: boolean;
      settlement_id: number;
      returns_created: number;
      total_return_amount: number;
      settlement_amount: number;
      message: string;
    }>(`${this.baseURL}/process_settlement_with_returns/`, data);
  }

  async getReturnsAnalytics(params?: {
    days?: number;
    shop_id?: number;
    salesman_id?: number;
  }): Promise<ReturnsAnalytics> {
    return apiClient.get<ReturnsAnalytics>(`${this.baseURL}/analytics/`, params);
  }
}

export const batchReturnService = new BatchReturnService();
