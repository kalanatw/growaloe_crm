import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { X, Plus, Minus, Package } from 'lucide-react';
import { productService } from '../services/apiServices';
import { Product, Salesman, CreateDeliveryData } from '../types';
import toast from 'react-hot-toast';

interface CreateDeliveryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreateDeliveryData) => void;
  salesmen: Salesman[];
}

interface DeliveryFormData {
  salesman: number;
  delivery_date: string;
  notes: string;
  items: {
    product: number;
    quantity: number;
    notes: string;
  }[];
}

export const CreateDeliveryModal: React.FC<CreateDeliveryModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  salesmen,
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoadingProducts, setIsLoadingProducts] = useState(false);

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

  useEffect(() => {
    if (isOpen) {
      loadProducts();
    }
  }, [isOpen]);

  const loadProducts = async () => {
    try {
      setIsLoadingProducts(true);
      const productsData = await productService.getProducts();
      setProducts(productsData.results.filter(p => p.is_active));
    } catch (error) {
      console.error('Error loading products:', error);
      toast.error('Failed to load products');
    } finally {
      setIsLoadingProducts(false);
    }
  };

  const handleFormSubmit = (data: DeliveryFormData) => {
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
        notes: item.notes || undefined,
      })),
    };

    onSubmit(deliveryData);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const getProductName = (productId: number) => {
    const product = products.find(p => p.id === productId);
    return product ? `${product.name} (${product.sku})` : 'Select Product';
  };

  const getAvailableStock = (productId: number) => {
    const product = products.find(p => p.id === productId);
    return product ? product.stock_quantity : 0;
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
                    {salesman.name}
                  </option>
                ))}
              </select>
              {errors.salesman && (
                <p className="text-red-500 text-sm mt-1">{errors.salesman.message}</p>
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
                onClick={() => append({ product: 0, quantity: 1, notes: '' })}
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

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                            {product.name} ({product.sku}) - Stock: {product.stock_quantity}
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
      </div>
    </div>
  );
};
