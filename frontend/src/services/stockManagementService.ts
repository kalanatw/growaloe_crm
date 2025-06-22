import { apiClient } from './api';

export interface StockAddition {
  quantity: number;
  notes?: string;
  batch_number?: string;
  expiry_date?: string;
  cost_per_unit?: number;
}

export interface StockReduction {
  quantity: number;
  notes?: string;
  reason?: 'adjustment' | 'damage' | 'return';
}

export interface StockStatus {
  owner_stock: number;
  total_allocated: number;
  total_available: number;
  low_stock_alert: boolean;
  salesman_allocations: Array<{
    salesman_name: string;
    allocated: number;
    available: number;
    sold: number;
  }>;
}

export interface StockOperationResult {
  success: boolean;
  message: string;
  old_quantity: number;
  new_quantity: number;
  added_quantity?: number;
  reduced_quantity?: number;
  batch_id?: number;
  batch_number?: string;
}

class StockManagementService {
  /**
   * Add stock to a product
   */
  async addStock(productId: number, data: StockAddition): Promise<StockOperationResult> {
    try {
      console.log('Adding stock:', { productId, data });
      const response = await apiClient.post(`/products/products/${productId}/add_stock/`, data);
      console.log('Add stock response:', response);
      return response as StockOperationResult;
    } catch (error) {
      console.error('Add stock error:', error);
      throw error;
    }
  }

  /**
   * Reduce stock from a product
   */
  async reduceStock(productId: number, data: StockReduction): Promise<StockOperationResult> {
    const response = await apiClient.post(`/products/products/${productId}/reduce_stock/`, data);
    return (response as any).data;
  }

  /**
   * Get real-time stock status for a product (batch-based)
   */
  async getStockStatus(productId: number): Promise<StockStatus> {
    const response = await apiClient.get(`/products/products/${productId}/batch_stock_status/`);
    return response as StockStatus;
  }

  /**
   * Get stock status for multiple products
   */
  async getMultipleStockStatus(productIds: number[]): Promise<Record<number, StockStatus>> {
    const promises = productIds.map(id => 
      this.getStockStatus(id).then(status => ({ id, status }))
    );
    
    const results = await Promise.all(promises);
    return results.reduce((acc, { id, status }) => {
      acc[id] = status;
      return acc;
    }, {} as Record<number, StockStatus>);
  }

  /**
   * Validate stock availability for invoice creation (batch-based)
   */
  async validateStockForInvoice(
    salesmanId: number, 
    items: Array<{ productId: number; quantity: number }>
  ): Promise<{ valid: boolean; errors: string[] }> {
    try {
      // Get salesman available products for validation
      const salesmanProductsResponse = await apiClient.get('/products/products/salesman-available-products/');
      const salesmanProducts = salesmanProductsResponse as any[];
      
      const errors: string[] = [];
      
      for (const item of items) {
        const product = salesmanProducts.find((p: any) => p.product_id === item.productId);
        
        if (!product) {
          errors.push(`No stock allocation found for product ID ${item.productId}`);
          continue;
        }
        
        if (product.total_available_quantity < item.quantity) {
          errors.push(
            `Insufficient stock for ${product.product_name}. ` +
            `Available: ${product.total_available_quantity}, Required: ${item.quantity}`
          );
        }
      }
      
      return {
        valid: errors.length === 0,
        errors
      };
    } catch (error) {
      console.error('Error validating stock:', error);
      return {
        valid: false,
        errors: ['Failed to validate stock availability']
      };
    }
  }

  /**
   * Get low stock alerts (batch-based)
   */
  async getLowStockAlerts(): Promise<Array<{
    product_id: number;
    product_name: string;
    current_stock: number;
    min_stock_level: number;
    shortage: number;
  }>> {
    try {
      const response = await apiClient.get('/products/products/stock_summary/');
      const stockSummary = (response as any).results || (response as any);
      
      return stockSummary
        .filter((item: any) => item.total_quantity <= item.min_stock_level)
        .map((item: any) => ({
          product_id: item.product_id,
          product_name: item.product_name,
          current_stock: item.total_quantity,
          min_stock_level: item.min_stock_level,
          shortage: item.min_stock_level - item.total_quantity
        }));
    } catch (error) {
      console.error('Error getting low stock alerts:', error);
      return [];
    }
  }
}

export const stockManagementService = new StockManagementService();
