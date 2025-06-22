import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Plus, Minus, Save, ArrowLeft, Package, Calendar, Clock } from 'lucide-react';
import { shopService, productService, invoiceService } from '../services/apiServices';
import { Shop, AvailableBatch, CreateBatchInvoiceData } from '../types';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';
import { format } from 'date-fns';

interface BatchInvoiceFormData {
  shop: number;
  due_date: string;
  tax_amount: number;
  discount_amount: number;
  notes: string;
  terms_conditions: string;
  items: {
    product: number;
    batch: number;
    quantity: number;
    unit_price: number;
  }[];
}

export const CreateBatchInvoicePage: React.FC = () => {
  const navigate = useNavigate();
  const [shops, setShops] = useState<Shop[]>([]);
  const [availableBatches, setAvailableBatches] = useState<AvailableBatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<BatchInvoiceFormData>({
    defaultValues: {
      items: [{ product: 0, batch: 0, quantity: 1, unit_price: 0 }],
      tax_amount: 0,
      discount_amount: 0,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const watchedItems = watch('items');
  const watchedDiscount = watch('discount_amount') || 0;
  const watchedTax = watch('tax_amount') || 0;

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      const [shopsData, batchesData] = await Promise.all([
        shopService.getShops(),
        productService.getSalesmanAvailableBatches(), // This will get batches for the current salesman
      ]);

      console.log('Loaded shops:', shopsData.results);
      console.log('Loaded batches:', batchesData);
      
      setShops(shopsData.results);
      setAvailableBatches(batchesData);
      
      // Log unique products for debugging
      const uniqueProducts = batchesData.reduce((acc: any[], batch: any) => {
        if (!acc.some(p => p.id === batch.product_id)) {
          acc.push({
            id: batch.product_id,
            name: batch.product_name,
            sku: batch.product_sku,
          });
        }
        return acc;
      }, []);
      console.log('Unique products:', uniqueProducts);
      
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const getBatchesForProduct = (productId: number) => {
    const productBatches = availableBatches.filter(batch => batch.product_id === productId);
    
    // Group by batch_id and aggregate quantities
    const batchMap = new Map();
    
    productBatches.forEach(batch => {
      const key = batch.batch_id;
      if (batchMap.has(key)) {
        const existing = batchMap.get(key);
        existing.available_quantity += batch.available_quantity;
        existing.assignments.push(batch);
      } else {
        batchMap.set(key, {
          ...batch,
          assignments: [batch], // Keep track of individual assignments
        });
      }
    });
    
    return Array.from(batchMap.values());
  };

  const getSelectedBatch = (batchId: number) => {
    const productBatches = availableBatches.filter(batch => batch.batch_id === batchId);
    if (productBatches.length === 0) return null;
    
    // Return aggregated batch info
    const totalAvailable = productBatches.reduce((sum, batch) => sum + batch.available_quantity, 0);
    return {
      ...productBatches[0],
      available_quantity: totalAvailable,
      assignments: productBatches, // Keep track of individual assignments
    };
  };

  const getUniqueProducts = () => {
    const products = availableBatches.reduce((acc, batch) => {
      if (!acc.some(p => p.id === batch.product_id)) {
        acc.push({
          id: batch.product_id,
          name: batch.product_name,
          sku: batch.product_sku,
        });
      }
      return acc;
    }, [] as { id: number; name: string; sku: string }[]);
    
    return products;
  };

  const calculateItemTotal = (item: any) => {
    const quantity = item.quantity || 0;
    const unitPrice = item.unit_price || 0;
    return quantity * unitPrice;
  };

  const calculateSubtotal = () => {
    return watchedItems.reduce((sum, item) => sum + calculateItemTotal(item), 0);
  };

  const calculateTotal = () => {
    const subtotal = calculateSubtotal();
    return subtotal + watchedTax - watchedDiscount;
  };

  const onSubmit = async (data: BatchInvoiceFormData) => {
    try {
      setIsSubmitting(true);
      
      // Validate items
      if (data.items.length === 0) {
        toast.error('Please add at least one item');
        return;
      }

      // Check batch availability
      for (const item of data.items) {
        const batch = getSelectedBatch(item.batch);
        if (!batch) {
          toast.error('Selected batch is not available');
          return;
        }
        if (item.quantity > batch.available_quantity) {
          toast.error(`Insufficient stock for ${batch.product_name}. Available: ${batch.available_quantity}`);
          return;
        }
      }

      const invoiceData: CreateBatchInvoiceData = {
        shop: data.shop,
        due_date: data.due_date || undefined,
        tax_amount: data.tax_amount || 0,
        discount_amount: data.discount_amount || 0,
        notes: data.notes || '',
        terms_conditions: data.terms_conditions || '',
        items: data.items.map(item => ({
          product: item.product,
          batch: item.batch,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
      };

      console.log('Sending invoice data:', invoiceData);
      console.log('Available batches for reference:', availableBatches);

      const invoice = await invoiceService.createBatchInvoice(invoiceData);
      toast.success('Invoice created successfully!');
      navigate(`/invoices/${invoice.id}`);
    } catch (error: any) {
      console.error('Error creating invoice:', error);
      
      // Enhanced error handling
      let errorMessage = 'Failed to create invoice';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.items) {
          // Handle item-specific errors
          const itemErrors = errorData.items;
          if (Array.isArray(itemErrors) && itemErrors.length > 0) {
            const firstItemError = itemErrors[0];
            if (firstItemError.non_field_errors?.[0]) {
              errorMessage = firstItemError.non_field_errors[0];
            } else {
              // Look for specific field errors
              const fieldErrors = Object.keys(firstItemError).filter(key => key !== 'non_field_errors');
              if (fieldErrors.length > 0) {
                errorMessage = `${fieldErrors[0]}: ${firstItemError[fieldErrors[0]]}`;
              }
            }
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.non_field_errors?.[0]) {
          errorMessage = errorData.non_field_errors[0];
        }
      }
      
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Create Batch Invoice">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  const uniqueProducts = getUniqueProducts();

  // Debug info
  console.log('Available batches count:', availableBatches.length);
  console.log('Unique products count:', uniqueProducts.length);
  console.log('Is loading:', isLoading);

  return (
    <Layout title="Create Batch Invoice">
      <div className="max-w-4xl mx-auto">
        {/* Debug information */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <h4 className="text-sm font-medium text-yellow-800 mb-2">Debug Info:</h4>
            <p className="text-xs text-yellow-700">Available batches: {availableBatches.length}</p>
            <p className="text-xs text-yellow-700">Unique products: {uniqueProducts.length}</p>
            <p className="text-xs text-yellow-700">Loading: {isLoading ? 'Yes' : 'No'}</p>
          </div>
        )}
        
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/invoices')}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Create Batch Invoice
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Create invoice from your assigned batches
                </p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Invoice Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">Shop *</label>
                <select
                  {...register('shop', { required: 'Shop is required', valueAsNumber: true })}
                  className="input"
                >
                  <option value="">Select a shop</option>
                  {shops.map((shop) => (
                    <option key={shop.id} value={shop.id}>
                      {shop.name} - {shop.contact_person}
                    </option>
                  ))}
                </select>
                {errors.shop && (
                  <p className="mt-1 text-sm text-red-600">{errors.shop.message}</p>
                )}
              </div>

              <div>
                <label className="label">Due Date</label>
                <input
                  {...register('due_date')}
                  type="date"
                  className="input"
                />
              </div>
            </div>

            {/* Invoice Items */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Invoice Items
                </h3>
                <button
                  type="button"
                  onClick={() => append({ product: 0, batch: 0, quantity: 1, unit_price: 0 })}
                  className="btn-primary"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </button>
              </div>

              <div className="space-y-4">
                {fields.map((field, index) => {
                  const selectedProductId = watchedItems[index]?.product;
                  const selectedBatchId = watchedItems[index]?.batch;
                  const productBatches = selectedProductId ? getBatchesForProduct(selectedProductId) : [];
                  const selectedBatch = selectedBatchId ? getSelectedBatch(selectedBatchId) : null;

                  return (
                    <div key={field.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                        {/* Product Selection */}
                        <div>
                          <label className="label">Product *</label>
                          <select
                            {...register(`items.${index}.product`, { 
                              required: 'Product is required',
                              valueAsNumber: true,
                            })}
                            className="input"
                            onChange={(e) => {
                              const productId = parseInt(e.target.value);
                              // Reset batch selection when product changes
                              setValue(`items.${index}.batch`, 0);
                              setValue(`items.${index}.unit_price`, 0);
                            }}
                          >
                            <option value="">Select product</option>
                            {uniqueProducts.map((product) => (
                              <option key={product.id} value={product.id}>
                                {product.name}
                              </option>
                            ))}
                          </select>
                          {errors.items?.[index]?.product && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.items[index]?.product?.message}
                            </p>
                          )}
                        </div>

                        {/* Batch Selection */}
                        <div>
                          <label className="label">Batch *</label>
                          <select
                            {...register(`items.${index}.batch`, { 
                              required: 'Batch is required',
                              valueAsNumber: true,
                            })}
                            className="input"
                            disabled={!selectedProductId}
                            onChange={(e) => {
                              const batchId = parseInt(e.target.value);
                              const batch = getSelectedBatch(batchId);
                              if (batch) {
                                // Auto-fill unit price with batch cost
                                setValue(`items.${index}.unit_price`, parseFloat(batch.unit_cost));
                              }
                            }}
                          >
                            <option value="">Select batch</option>
                            {productBatches.map((batch) => (
                              <option key={batch.batch_id} value={batch.batch_id}>
                                {batch.batch_number} ({batch.available_quantity} available)
                              </option>
                            ))}
                          </select>
                          {selectedBatch && (
                            <div className="text-xs text-gray-500 mt-1 space-y-1">
                              <div className="flex items-center space-x-2">
                                <Package className="h-3 w-3" />
                                <span>Available: {selectedBatch.available_quantity}</span>
                                {selectedBatch.assignments && selectedBatch.assignments.length > 1 && (
                                  <span className="text-blue-600">
                                    (from {selectedBatch.assignments.length} assignments)
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center space-x-2">
                                <Calendar className="h-3 w-3" />
                                <span>Expires: {format(new Date(selectedBatch.expiry_date), 'MMM dd, yyyy')}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <Clock className="h-3 w-3" />
                                <span className={selectedBatch.days_until_expiry <= 7 ? 'text-red-600' : 'text-gray-500'}>
                                  {selectedBatch.days_until_expiry} days left
                                </span>
                              </div>
                              {process.env.NODE_ENV === 'development' && selectedBatch.assignments && (
                                <div className="mt-2 p-2 bg-gray-100 rounded text-xs">
                                  <strong>Debug - Assignment breakdown:</strong>
                                  {selectedBatch.assignments.map((assignment: any, idx: number) => (
                                    <div key={idx}>
                                      Assignment {assignment.assignment_id}: {assignment.available_quantity} units
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                          {errors.items?.[index]?.batch && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.items[index]?.batch?.message}
                            </p>
                          )}
                        </div>

                        {/* Quantity */}
                        <div>
                          <label className="label">Quantity *</label>
                          <input
                            {...register(`items.${index}.quantity`, { 
                              required: 'Quantity is required',
                              valueAsNumber: true,
                              min: { value: 1, message: 'Minimum quantity is 1' },
                              max: selectedBatch ? { 
                                value: selectedBatch.available_quantity, 
                                message: `Maximum available: ${selectedBatch.available_quantity}` 
                              } : undefined,
                            })}
                            type="number"
                            min="1"
                            max={selectedBatch?.available_quantity}
                            className="input"
                          />
                          {errors.items?.[index]?.quantity && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.items[index]?.quantity?.message}
                            </p>
                          )}
                        </div>

                        {/* Unit Price */}
                        <div>
                          <label className="label">Unit Price *</label>
                          <input
                            {...register(`items.${index}.unit_price`, { 
                              required: 'Unit price is required',
                              valueAsNumber: true,
                              min: { value: 0.01, message: 'Price must be greater than 0' },
                            })}
                            type="number"
                            step="0.01"
                            min="0.01"
                            className="input"
                          />
                          {selectedBatch && (
                            <p className="text-xs text-gray-500 mt-1">
                              Cost: {formatCurrency(parseFloat(selectedBatch.unit_cost))}
                            </p>
                          )}
                          {errors.items?.[index]?.unit_price && (
                            <p className="text-xs text-red-600 mt-1">
                              {errors.items[index]?.unit_price?.message}
                            </p>
                          )}
                        </div>

                        {/* Total and Remove */}
                        <div className="flex items-end">
                          <div className="flex-1">
                            <label className="label">Total</label>
                            <div className="input bg-gray-50 dark:bg-gray-700 text-right">
                              {formatCurrency(calculateItemTotal(watchedItems[index]))}
                            </div>
                          </div>
                          {fields.length > 1 && (
                            <button
                              type="button"
                              onClick={() => remove(index)}
                              className="ml-2 p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                            >
                              <Minus className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Invoice Totals */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <label className="label">Tax Amount</label>
                  <input
                    {...register('tax_amount', { valueAsNumber: true })}
                    type="number"
                    step="0.01"
                    min="0"
                    className="input"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="label">Discount Amount</label>
                  <input
                    {...register('discount_amount', { valueAsNumber: true })}
                    type="number"
                    step="0.01"
                    min="0"
                    className="input"
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <label className="label">Notes</label>
                  <textarea
                    {...register('notes')}
                    rows={3}
                    className="input"
                    placeholder="Additional notes..."
                  />
                </div>
              </div>

              <div className="card p-4 bg-gray-50 dark:bg-gray-800">
                <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                  Invoice Summary
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Subtotal:</span>
                    <span className="font-medium">{formatCurrency(calculateSubtotal())}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Tax:</span>
                    <span className="font-medium">{formatCurrency(watchedTax)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Discount:</span>
                    <span className="font-medium">-{formatCurrency(watchedDiscount)}</span>
                  </div>
                  <hr className="border-gray-200 dark:border-gray-600" />
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total:</span>
                    <span>{formatCurrency(calculateTotal())}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => navigate('/invoices')}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
              >
                {isSubmitting ? (
                  <LoadingSpinner size="sm" className="mr-2" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                {isSubmitting ? 'Creating...' : 'Create Invoice'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};
