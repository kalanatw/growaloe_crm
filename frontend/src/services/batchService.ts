import { apiClient as api } from './api';
import {
  Batch,
  BatchDefect,
  BatchAllocation,
  BatchMovement,
  BatchReturn,
  BatchQualityCheck,
  BatchAnalytics,
  BatchRecall,
  CreateBatchData,
  BatchFormErrors,
  BatchValidationResponse,
} from '../types';

export interface BatchFilters {
  product?: number;
  status?: string;
  quality_status?: string;
  salesman?: number;
  date_from?: string;
  date_to?: string;
  expiry_soon?: boolean;
  low_stock?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface UpdateBatchData {
  status?: string;
  quality_status?: string;
  quality_notes?: string;
  location?: string;
  notes?: string;
}

export interface BatchReturnData {
  batch: number;
  invoice?: number;
  shop?: number;
  quantity: number;
  reason: string;
  condition: string;
  description?: string;
  action_taken?: string;
  refund_amount?: number;
  replacement_batch?: number;
  notes?: string;
}

export interface BatchDefectData {
  batch: number;
  defect_type: string;
  severity: string;
  description: string;
  detected_date: string;
  action_taken?: string;
}

export interface BatchQualityCheckData {
  batch: number;
  check_type: string;
  status: string;
  checked_date: string;
  checked_by: string;
  parameters_checked: string[];
  results: Record<string, any>;
  notes?: string;
  next_check_date?: string;
}

export interface BatchRecallData {
  batch_numbers: string[];
  product: number;
  recall_reason: string;
  severity: string;
  notes?: string;
  regulatory_notification?: boolean;
  media_notification?: boolean;
}

class BatchService {
  // Batch CRUD operations
  async getAllBatches(filters?: BatchFilters) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    return api.get<{ results: Batch[]; count: number; next?: string; previous?: string }>(`/products/batches/?${params.toString()}`);
  }

  async getBatch(id: number): Promise<Batch> {
    return api.get<Batch>(`/products/batches/${id}/`);
  }

  async createBatch(data: CreateBatchData): Promise<Batch> {
    // Ensure current_quantity equals initial_quantity for new batches
    const batchData = {
      ...data,
      current_quantity: data.current_quantity || data.initial_quantity,
      quality_status: data.quality_status || 'GOOD',
      is_active: data.is_active !== undefined ? data.is_active : true
    };
    return api.post<Batch>('/products/batches/', batchData);
  }

  // Batch number validation
  async validateBatchNumber(batchNumber: string): Promise<{ isValid: boolean; message?: string }> {
    try {
      const response = await api.get<{ is_available: boolean; message: string }>(
        `/products/batches/validate-batch-number/?batch_number=${encodeURIComponent(batchNumber)}`
      );
      return { 
        isValid: response.is_available, 
        message: response.message 
      };
    } catch (error: any) {
      return { 
        isValid: false, 
        message: error.response?.data?.message || 'Batch number validation failed' 
      };
    }
  }

  async updateBatch(id: number, data: UpdateBatchData): Promise<Batch> {
    return api.patch<Batch>(`/products/batches/${id}/`, data);
  }

  async deleteBatch(id: number): Promise<void> {
    return api.delete<void>(`/products/batches/${id}/`);
  }

  // Batch allocations
  async getBatchAllocations(batchId?: number): Promise<BatchAllocation[]> {
    const url = batchId ? `/batches/${batchId}/allocations/` : '/batch-allocations/';
    return api.get<{ results: BatchAllocation[] } | BatchAllocation[]>(url).then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  async createBatchAllocation(batchId: number, salesmanId: number, quantity: number, notes?: string): Promise<BatchAllocation> {
    return api.post<BatchAllocation>(`/batches/${batchId}/allocate/`, {
      salesman: salesmanId,
      quantity,
      notes
    });
  }

  async deallocateBatch(batchId: number, salesmanId: number, quantity: number): Promise<void> {
    return api.post<void>(`/batches/${batchId}/deallocate/`, {
      salesman: salesmanId,
      quantity
    });
  }

  // Batch movements and traceability
  async getBatchMovements(batchId: number): Promise<BatchMovement[]> {
    return api.get<{ results: BatchMovement[] } | BatchMovement[]>(`/batches/${batchId}/movements/`).then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  async getBatchTraceability(batchId: number) {
    return api.get<any>(`/batches/${batchId}/traceability/`);
  }

  // Batch returns
  async createBatchReturn(data: BatchReturnData): Promise<BatchReturn> {
    return api.post<BatchReturn>('/returns/', data);
  }

  async getBatchReturns(batchId?: number) {
    const url = batchId ? `/returns/by-batch/?batch=${batchId}` : '/returns/';
    return api.get<{ results: BatchReturn[] } | BatchReturn[]>(url);
  }

  async getReturnAnalytics(filters?: { 
    batch?: number; 
    product?: number; 
    date_from?: string; 
    date_to?: string; 
  }) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<any>(`/returns/analytics/?${params.toString()}`);
  }

  // Batch quality management
  async markBatchDefective(batchId: number, data: Omit<BatchDefectData, 'batch'>): Promise<BatchDefect> {
    return api.post<BatchDefect>(`/batches/${batchId}/mark-defective/`, data);
  }

  async getBatchDefects(batchId?: number): Promise<BatchDefect[]> {
    const url = batchId ? `/batches/${batchId}/defects/` : '/batch-defects/';
    return api.get<{ results: BatchDefect[] } | BatchDefect[]>(url).then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  async updateBatchDefect(defectId: number, data: Partial<BatchDefectData>): Promise<BatchDefect> {
    return api.patch<BatchDefect>(`/batch-defects/${defectId}/`, data);
  }

  async getBatchQualityAnalytics(batchId: number) {
    return api.get<any>(`/batches/${batchId}/quality-analytics/`);
  }

  async createQualityCheck(data: BatchQualityCheckData): Promise<BatchQualityCheck> {
    return api.post<BatchQualityCheck>('/quality-checks/', data);
  }

  async getQualityChecks(batchId?: number): Promise<BatchQualityCheck[]> {
    const url = batchId ? `/batches/${batchId}/quality-checks/` : '/quality-checks/';
    return api.get<{ results: BatchQualityCheck[] } | BatchQualityCheck[]>(url).then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  // Batch recalls
  async createBatchRecall(data: BatchRecallData): Promise<BatchRecall> {
    return api.post<BatchRecall>('/batch-recalls/', data);
  }

  async getBatchRecalls(): Promise<BatchRecall[]> {
    return api.get<{ results: BatchRecall[] } | BatchRecall[]>('/batch-recalls/').then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  async updateBatchRecall(recallId: number, data: Partial<BatchRecallData>): Promise<BatchRecall> {
    return api.patch<BatchRecall>(`/batch-recalls/${recallId}/`, data);
  }

  // Batch analytics and reporting
  async getBatchAnalytics(filters?: {
    batch?: number;
    product?: number;
    salesman?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<BatchAnalytics[]> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<{ results: BatchAnalytics[] } | BatchAnalytics[]>(`/batch-analytics/?${params.toString()}`).then(response => 
      Array.isArray(response) ? response : response.results || []
    );
  }

  async getBatchInventoryReport(filters?: {
    low_stock?: boolean;
    expiry_soon?: boolean;
    quality_issues?: boolean;
    date_from?: string;
    date_to?: string;
  }) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<any>(`/batch-inventory-report/?${params.toString()}`);
  }

  async getExpiryAlerts(daysAhead: number = 30) {
    return api.get<any>(`/products/batches/expiry-alerts/?days=${daysAhead}`);
  }

  async getLowStockAlerts(threshold?: number) {
    const params = threshold ? `?threshold=${threshold}` : '';
    return api.get<any>(`/products/batches/low-stock-alerts/${params}`);
  }

  async getQualityAlerts() {
    return api.get<any>('/products/batches/quality-alerts/');
  }

  // Batch search and filtering
  async searchBatches(query: string, filters?: Partial<BatchFilters>) {
    const params = new URLSearchParams({ search: query });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<{ results: Batch[]; count: number }>(`/products/batches/search/?${params.toString()}`);
  }

  async getBatchSuggestions(productId: number, quantity: number) {
    return api.get<Batch[]>(`/products/batches/fifo-suggestions/?product_id=${productId}&quantity=${quantity}`);
  }

  // Batch performance metrics
  async getBatchPerformanceMetrics(filters?: {
    date_from?: string;
    date_to?: string;
    product?: number;
    salesman?: number;
  }) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<any>(`/batch-performance/?${params.toString()}`);
  }

  async getBatchTurnoverReport(filters?: {
    date_from?: string;
    date_to?: string;
    product?: number;
  }) {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    return api.get<any>(`/batch-turnover-report/?${params.toString()}`);
  }
}

export const batchService = new BatchService();
