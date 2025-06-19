import { apiClient } from './api';

export interface StockAddition {
  quantity: number;
  notes?: string;
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
   * Get real-time stock status for a product
   */
  async getStockStatus(productId: number): Promise<StockStatus> {
    const response = await apiClient.get(`/products/products/${productId}/stock_status/`);
    return (response as any).data;
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
   * Validate stock availability for invoice creation
   */
  async validateStockForInvoice(
    salesmanId: number, 
    items: Array<{ productId: number; quantity: number }>
  ): Promise<{ valid: boolean; errors: string[] }> {
    try {
      // Get salesman stock for validation
      const salesmanStockResponse = await apiClient.get(`/products/salesman-stock/?salesman=${salesmanId}`);
      const salesmanStock = (salesmanStockResponse as any).data.results || (salesmanStockResponse as any).data;
      
      const errors: string[] = [];
      
      for (const item of items) {
        const stock = salesmanStock.find((s: any) => s.product === item.productId);
        
        if (!stock) {
          errors.push(`No stock allocation found for product ID ${item.productId}`);
          continue;
        }
        
        if (stock.available_quantity < item.quantity) {
          errors.push(
            `Insufficient stock for ${stock.product_name}. ` +
            `Available: ${stock.available_quantity}, Required: ${item.quantity}`
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
   * Get low stock alerts
   */
  async getLowStockAlerts(): Promise<Array<{
    product_id: number;
    product_name: string;
    current_stock: number;
    min_stock_level: number;
    shortage: number;
  }>> {
    try {
      const response = await apiClient.get('/products/products/');
      const products = (response as any).data.results || (response as any).data;
      
      return products
        .filter((product: any) => product.stock_quantity <= product.min_stock_level)
        .map((product: any) => ({
          product_id: product.id,
          product_name: product.name,
          current_stock: product.stock_quantity,
          min_stock_level: product.min_stock_level,
          shortage: product.min_stock_level - product.stock_quantity
        }));
    } catch (error) {
      console.error('Error getting low stock alerts:', error);
      return [];
    }
  }
}

export const stockManagementService = new StockManagementService();
