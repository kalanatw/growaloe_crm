import React, { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Plus, Minus, Save, ArrowLeft } from 'lucide-react';
import { shopService, productService, invoiceService } from '../services/apiServices';
import { Shop, SalesmanStock, CreateInvoiceData } from '../types';
import { PAYMENT_METHODS } from '../config/constants';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';

interface InvoiceFormData {
  shop: number;
  due_date: string;
  tax_amount: number;
  discount_amount: number;
  notes: string;
  terms_conditions: string;
  items: {
    product: number;
    quantity: number;
    unit_price: number;
    salesman_margin: number;
    shop_margin: number;
  }[];
}

export const CreateInvoicePage: React.FC = () => {
  const navigate = useNavigate();
  const [shops, setShops] = useState<Shop[]>([]);
  const [stockData, setStockData] = useState<SalesmanStock[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<InvoiceFormData>({
    defaultValues: {
      items: [{ product: 0, quantity: 1, unit_price: 0, salesman_margin: 0, shop_margin: 0 }],
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
      const [shopsData, stockDataResponse] = await Promise.all([
        shopService.getShops(),
        productService.getMySalesmanStock(),
      ]);

      setShops(shopsData.results);
      setStockData(stockDataResponse.stocks);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load data');
    } finally {
      setIsLoading(false);
    }
  };

  const getProductStock = (productId: number) => {
    return stockData.find(stock => stock.product === productId);
  };

  const calculateItemTotal = (item: any) => {
    const quantity = item.quantity || 0;
    const unitPrice = item.unit_price || 0;
    const salesmanMargin = item.salesman_margin || 0;
    const shopMargin = item.shop_margin || 0;
    
    let price = unitPrice;
    if (salesmanMargin > 0) {
      price += (price * salesmanMargin / 100);
    }
    if (shopMargin > 0) {
      price += (price * shopMargin / 100);
    }
    
    return quantity * price;
  };

  const calculateSubtotal = () => {
    return watchedItems.reduce((sum, item) => sum + calculateItemTotal(item), 0);
  };

  const calculateTotal = () => {
    const subtotal = calculateSubtotal();
    return subtotal + watchedTax - watchedDiscount;
  };

  const onSubmit = async (data: InvoiceFormData) => {
    try {
      setIsSubmitting(true);
      
      // Validate items
      if (data.items.length === 0) {
        toast.error('Please add at least one item');
        return;
      }

      // Check stock availability
      for (const item of data.items) {
        const stock = getProductStock(item.product);
        if (!stock) {
          toast.error('Selected product is not available');
          return;
        }
        if (item.quantity > stock.available_quantity) {
          toast.error(`Insufficient stock for ${stock.product_name}. Available: ${stock.available_quantity}`);
          return;
        }
      }

      const invoiceData: CreateInvoiceData = {
        shop: data.shop,
        due_date: data.due_date || undefined,
        tax_amount: data.tax_amount || 0,
        discount_amount: data.discount_amount || 0,
        notes: data.notes || '',
        terms_conditions: data.terms_conditions || '',
        items: data.items.map(item => ({
          product: item.product,
          quantity: item.quantity,
          unit_price: item.unit_price,
          salesman_margin: item.salesman_margin || 0,
          shop_margin: item.shop_margin || 0,
        })),
      };

      const invoice = await invoiceService.createInvoice(invoiceData);
      toast.success('Invoice created successfully!');
      navigate(`/invoices/${invoice.id}`);
    } catch (error: any) {
      console.error('Error creating invoice:', error);
      toast.error(error.response?.data?.detail || 'Failed to create invoice');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Create Invoice">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Create Invoice">
      <div className="max-w-4xl mx-auto">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/invoices')}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <ArrowLeft className="h-5 w-5" />
              </button>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Create New Invoice
              </h2>
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
                  onClick={() => append({ product: 0, quantity: 1, unit_price: 0, salesman_margin: 0, shop_margin: 0 })}
                  className="btn-primary"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </button>
              </div>

              <div className="space-y-4">
                {fields.map((field, index) => {
                  const selectedProductId = watchedItems[index]?.product;
                  const stock = selectedProductId ? getProductStock(selectedProductId) : null;

                  return (
                    <div key={field.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                        <div className="md:col-span-2">
                          <label className="label">Product *</label>
                          <select
                            {...register(`items.${index}.product`, { 
                              required: 'Product is required',
                              valueAsNumber: true,
                            })}
                            className="input"
                            onChange={(e) => {
                              const productId = parseInt(e.target.value);
                              const selectedStock = getProductStock(productId);
                              if (selectedStock) {
                                // Auto-fill unit price with base price (you might want to get this from products API)
                                setValue(`items.${index}.unit_price`, 10); // Default price
                              }
                            }}
                          >
                            <option value="">Select product</option>
                            {stockData.map((stock) => (
                              <option key={stock.product} value={stock.product}>
                                {stock.product_name} ({stock.available_quantity} available)
                              </option>
                            ))}
                          </select>
                          {stock && (
                            <p className="text-xs text-gray-500 mt-1">
                              Available: {stock.available_quantity} | SKU: {stock.product_sku}
                            </p>
                          )}
                        </div>

                        <div>
                          <label className="label">Quantity *</label>
                          <input
                            {...register(`items.${index}.quantity`, { 
                              required: 'Quantity is required',
                              valueAsNumber: true,
                              min: { value: 1, message: 'Minimum quantity is 1' },
                              max: stock ? { value: stock.available_quantity, message: `Maximum available: ${stock.available_quantity}` } : undefined,
                            })}
                            type="number"
                            min="1"
                            max={stock?.available_quantity}
                            className="input"
                          />
                        </div>

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
                        </div>

                        <div>
                          <label className="label">Margin %</label>
                          <input
                            {...register(`items.${index}.salesman_margin`, { valueAsNumber: true })}
                            type="number"
                            step="0.1"
                            min="0"
                            max="100"
                            className="input"
                            placeholder="0"
                          />
                        </div>

                        <div className="flex items-end">
                          <div className="flex-1">
                            <label className="label">Total</label>
                            <div className="input bg-gray-50 dark:bg-gray-700">
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
