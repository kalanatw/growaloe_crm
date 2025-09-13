import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { X, Plus, Minus, Package } from 'lucide-react';
import { productService, deliveryService } from '../services/apiServices';
import { Product, Salesman, CreateDeliveryData, Delivery } from '../types';
import toast from 'react-hot-toast';

interface CreateDeliveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateDeliveryData) => Promise<any>;
  salesmen: Salesman[];
}

interface DeliveryFormData {
  salesman: number;
  delivery_date: string;
  notes: string;
  salesman_type?: 'employee' | 'agent'; // Add salesman type
  items: {
    product: number;
    quantity: number;
    unit_price: number; // Add unit price
    notes: string;
  }[];
}

interface StockSummaryItem {
  product_id: number;
  product_name: string;
  product_sku: string;
  total_stock: number;
  allocated_stock: number;
  available_stock: number;
  pending_returns: number;
  salesmen_count: number;
}

export const CreateDeliveryModal: React.FC<CreateDeliveryModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  salesmen,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [stockSummary, setStockSummary] = useState<StockSummaryItem[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);
  const [selectedSalesmanType, setSelectedSalesmanType] = useState<'employee' | 'agent' | null>(null);
  
  // Agent delivery specific state
  const [isAgentDelivery, setIsAgentDelivery] = useState(false);
  const [showReceiptDownload, setShowReceiptDownload] = useState(false);
  const [createdDelivery, setCreatedDelivery] = useState<any>(null);

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
    watch,
  } = useForm<DeliveryFormData>({
    defaultValues: {
      salesman: 0,
      delivery_date: new Date().toISOString().split('T')[0],
      notes: '',
      items: [{ product: 0, quantity: 1, notes: '' }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const watchedSalesman = watch('salesman');

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen]);

  // Update selected salesman type when salesman changes
  useEffect(() => {
    if (watchedSalesman && watchedSalesman > 0) {
      const selectedSalesman = salesmen.find(s => s.id === watchedSalesman);
      if (selectedSalesman) {
        setSelectedSalesmanType(selectedSalesman.salesman_type as 'employee' | 'agent');
        setIsAgentDelivery(selectedSalesman.salesman_type === 'agent');
      }
    } else {
      setSelectedSalesmanType(null);
      setIsAgentDelivery(false);
    }
  }, [watchedSalesman, salesmen]);

  const loadProducts = async () => {
    try {
      setIsLoadingProducts(true);
      const [productsData, stockData] = await Promise.all([
        productService.getProducts(),
        productService.getProductStockSummary()
      ]);

      setProducts(productsData.results.filter(p => p.is_active));
      setStockSummary(stockData.results || stockData);
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Failed to load products');
    } finally {
      setIsLoadingProducts(false);
    }
  };

  const handleFormSubmit = async (data: DeliveryFormData) => {
    // Validate that at least one item is selected
    const validItems = data.items.filter(item => item.product > 0 && item.quantity > 0);

    if (validItems.length === 0) {
      toast.error('Please add at least one product to the delivery');
      return;
    }

    if (data.salesman === 0) {
      toast.error('Please select a salesman');
      return;
    }

    const deliveryData: CreateDeliveryData = {
      salesman: data.salesman,
      delivery_date: data.delivery_date,
      notes: data.notes || undefined,
      items: validItems.map(item => ({
        product: item.product,
        quantity: item.quantity,
        unit_price: item.unit_price, // include unit price
        notes: item.notes || undefined,
      })),
    };

    try {
      // Call the parent's onSubmit function and wait for the result
      const result = await onSubmit(deliveryData);
      
      // If this is an agent delivery, show receipt download option
      if (isAgentDelivery && result) {
        setCreatedDelivery(result);
        setShowReceiptDownload(true);
        toast.success('Agent delivery created successfully! Receipt is ready for download.');
      }
    } catch (error) {
      console.error('Error creating delivery:', error);
      toast.error('Failed to create delivery');
    }
  };

  // Add receipt download function
  const downloadAgentReceipt = async (deliveryId: number) => {
    try {
      const blob = await deliveryService.downloadAgentDeliveryReceipt(deliveryId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agent_delivery_receipt_${deliveryId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Receipt downloaded successfully!');
    } catch (error) {
      console.error('Error downloading receipt:', error);
      toast.error('Failed to download receipt');
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const getAvailableStock = (productId: number) => {
    const stockItem = stockSummary.find(s => s.product_id === productId);
    return stockItem ? stockItem.available_stock : 0;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Package className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Create Delivery</h2>
              <p className="text-gray-600">Allocate products to salesman</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
          {/* Basic Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Salesman *
              </label>
              <select
                {...register('salesman', {
                  required: 'Salesman is required',
                  valueAsNumber: true,
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={0}>Select Salesman</option>
                {salesmen.map((salesman) => (
                  <option key={salesman.id} value={salesman.id}>
                    {salesman.name} {salesman.salesman_type === 'agent' ? '(Agent)' : '(Employee)'}
                  </option>
                ))}
              </select>
              {errors.salesman && (
                <p className="text-red-500 text-sm mt-1">{errors.salesman.message}</p>
              )}
              
              {/* Show delivery type indicator */}
              {selectedSalesmanType && (
                <div className={`mt-2 p-3 rounded-lg ${
                  selectedSalesmanType === 'agent' 
                    ? 'bg-orange-50 border border-orange-200' 
                    : 'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      selectedSalesmanType === 'agent' ? 'bg-orange-500' : 'bg-blue-500'
                    }`}></div>
                    <span className={`text-sm font-medium ${
                      selectedSalesmanType === 'agent' ? 'text-orange-800' : 'text-blue-800'
                    }`}>
                      {selectedSalesmanType === 'agent' ? 'Agent Delivery' : 'Employee Delivery'}
                    </span>
                  </div>
                  <p className={`text-xs mt-1 ${
                    selectedSalesmanType === 'agent' ? 'text-orange-600' : 'text-blue-600'
                  }`}>
                    {selectedSalesmanType === 'agent' 
                      ? 'Agent purchases products directly. Payment required immediately upon delivery.'
                      : 'Products allocated to employee on consignment basis. Settlement after sales.'
                    }
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Delivery Date *
              </label>
              <input
                type="date"
                {...register('delivery_date', { required: 'Delivery date is required' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.delivery_date && (
                <p className="text-red-500 text-sm mt-1">{errors.delivery_date.message}</p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Notes
            </label>
            <textarea
              {...register('notes')}
              rows={3}
              placeholder="Any special instructions or notes for this delivery..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Products Section */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Products</h3>
              <button
                type="button"
                onClick={() => append({ product: 0, quantity: 1, unit_price: 0.01, notes: '' })}
                className="btn btn-outline btn-sm flex items-center space-x-1"
              >
                <Plus className="w-4 h-4" />
                <span>Add Product</span>
              </button>
            </div>

            <div className="space-y-4">
              {fields.map((field, index) => (
                <div key={field.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-medium text-gray-900">Item #{index + 1}</h4>
                    {fields.length > 1 && (
                      <button
                        type="button"
                        onClick={() => remove(index)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Product *
                      </label>
                      <select
                        {...register(`items.${index}.product`, {
                          required: 'Product is required',
                          valueAsNumber: true,
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={isLoadingProducts}
                      >
                        <option value={0}>
                          {isLoadingProducts ? 'Loading...' : 'Select Product'}
                        </option>
                        {products.map((product) => (
                          <option key={product.id} value={product.id}>
                            {product.name} ({product.sku}) - Stock: {getAvailableStock(product.id)}
                          </option>
                        ))}
                      </select>
                      {errors.items?.[index]?.product && (
                        <p className="text-red-500 text-sm mt-1">
                          {errors.items[index]?.product?.message}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity *
                      </label>
                      <input
                        type="number"
                        min="1"
                        max={getAvailableStock(watch(`items.${index}.product`) || 0)}
                        {...register(`items.${index}.quantity`, {
                          required: 'Quantity is required',
                          min: { value: 1, message: 'Quantity must be at least 1' },
                          max: {
                            value: getAvailableStock(watch(`items.${index}.product`) || 0),
                            message: `Quantity cannot exceed available stock (${getAvailableStock(watch(`items.${index}.product`) || 0)})`
                          },
                          valueAsNumber: true,
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {errors.items?.[index]?.quantity && (
                        <p className="text-red-500 text-sm mt-1">
                          {errors.items[index]?.quantity?.message}
                        </p>
                      )}
                      {watch(`items.${index}.product`) > 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          Available: {getAvailableStock(watch(`items.${index}.product`))}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Notes
                      </label>
                      <input
                        type="text"
                        {...register(`items.${index}.notes`)}
                        placeholder="Optional notes for this item"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Unit Price *
                      </label>
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        {...register(`items.${index}.unit_price`, {
                          required: 'Unit price is required',
                          min: { value: 0.01, message: 'Unit price must be positive' },
                          valueAsNumber: true,
                        })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {errors.items?.[index]?.unit_price && (
                        <p className="text-red-500 text-sm mt-1">
                          {errors.items[index]?.unit_price?.message}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={handleClose}
              className="btn btn-outline"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'Create Delivery'}
            </button>
          </div>
        </form>

        {/* Receipt download section for agent deliveries */}
        {showReceiptDownload && createdDelivery && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="text-sm font-medium text-green-800 mb-2">Agent Delivery Created Successfully!</h4>
            <p className="text-sm text-green-600 mb-3">
              The agent's balance has been updated and an invoice has been generated.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={() => downloadAgentReceipt(createdDelivery.id)}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 text-sm"
              >
                Download Receipt
              </button>
              <button
                onClick={handleClose}
                className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 text-sm"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
