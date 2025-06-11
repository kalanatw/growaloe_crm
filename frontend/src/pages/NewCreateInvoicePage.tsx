import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { 
  Plus, 
  Save, 
  ArrowLeft, 
  Search, 
  X, 
  ShoppingCart,
  FileText,
  Building2,
  Package
} from 'lucide-react';
import { shopService, productService, invoiceService } from '../services/apiServices';
import { Shop, SalesmanStock, CreateInvoiceData } from '../types';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';

interface InvoiceItem {
  id: string;
  product: SalesmanStock;
  quantity: number;
  unit_price: number;
  salesman_margin: number;
  shop_margin: number;
  total: number;
}

export const NewCreateInvoicePage: React.FC = () => {
  const navigate = useNavigate();
  
  // State management
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);
  const [invoiceItems, setInvoiceItems] = useState<InvoiceItem[]>([]);
  const [shops, setShops] = useState<Shop[]>([]);
  const [stockData, setStockData] = useState<SalesmanStock[]>([]);
  
  // Modal states
  const [isShopModalOpen, setIsShopModalOpen] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Search states
  const [shopSearchTerm, setShopSearchTerm] = useState('');
  const [productSearchTerm, setProductSearchTerm] = useState('');
  
  // Invoice details
  const [invoiceDetails, setInvoiceDetails] = useState({
    due_date: '',
    tax_amount: 0,
    discount_amount: 0,
    notes: '',
    terms_conditions: ''
  });

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

  // Filter functions
  const filteredShops = shops.filter(shop =>
    shop.name.toLowerCase().includes(shopSearchTerm.toLowerCase()) ||
    shop.contact_person.toLowerCase().includes(shopSearchTerm.toLowerCase())
  );

  const filteredProducts = stockData.filter(stock =>
    stock.product_name.toLowerCase().includes(productSearchTerm.toLowerCase()) ||
    stock.product_sku.toLowerCase().includes(productSearchTerm.toLowerCase())
  );

  // Shop selection
  const handleSelectShop = (shop: Shop) => {
    setSelectedShop(shop);
    setIsShopModalOpen(false);
    setShopSearchTerm('');
  };

  // Product selection
  const handleAddProduct = (product: SalesmanStock) => {
    const existingItem = invoiceItems.find(item => item.product.product === product.product);
    
    if (existingItem) {
      toast.error('Product already added to invoice');
      return;
    }

    const basePrice = product.product_base_price || 0;
    const shopMargin = selectedShop?.shop_margin || 0;
    
    // Calculate initial price with shop margin
    let finalPrice = basePrice;
    if (shopMargin > 0) {
      finalPrice += (basePrice * shopMargin / 100);
    }

    const newItem: InvoiceItem = {
      id: Math.random().toString(36).substr(2, 9),
      product,
      quantity: 1,
      unit_price: basePrice,
      salesman_margin: 0,
      shop_margin: shopMargin,
      total: finalPrice * 1 // quantity = 1
    };

    setInvoiceItems(prev => [...prev, newItem]);
    setIsProductModalOpen(false);
    setProductSearchTerm('');
    toast.success(`${product.product_name} added to invoice`);
  };

  // Update item
  const updateInvoiceItem = (id: string, updates: Partial<InvoiceItem>) => {
    setInvoiceItems(prev => prev.map(item => {
      if (item.id === id) {
        const updatedItem = { ...item, ...updates };
        
        // Recalculate total when quantity, price, or margins change
        if ('quantity' in updates || 'unit_price' in updates || 'salesman_margin' in updates || 'shop_margin' in updates) {
          let price = updatedItem.unit_price;
          
          // Apply salesman margin
          if (updatedItem.salesman_margin > 0) {
            price += (price * updatedItem.salesman_margin / 100);
          }
          
          // Apply shop margin
          if (updatedItem.shop_margin > 0) {
            price += (price * updatedItem.shop_margin / 100);
          }
          
          updatedItem.total = updatedItem.quantity * price;
        }
        
        return updatedItem;
      }
      return item;
    }));
  };

  // Remove item
  const removeInvoiceItem = (id: string) => {
    setInvoiceItems(prev => prev.filter(item => item.id !== id));
  };

  // Calculate totals
  const subtotal = invoiceItems.reduce((sum, item) => sum + item.total, 0);
  const total = subtotal + invoiceDetails.tax_amount - invoiceDetails.discount_amount;

  // Submit invoice
  const handleSubmitInvoice = async () => {
    if (!selectedShop) {
      toast.error('Please select a shop');
      return;
    }

    if (invoiceItems.length === 0) {
      toast.error('Please add at least one product');
      return;
    }

    // Validate stock availability
    for (const item of invoiceItems) {
      if (item.quantity > item.product.available_quantity) {
        toast.error(`Insufficient stock for ${item.product.product_name}. Available: ${item.product.available_quantity}`);
        return;
      }
    }

    try {
      setIsSubmitting(true);

      const invoiceData: CreateInvoiceData = {
        shop: selectedShop.id,
        due_date: invoiceDetails.due_date || undefined,
        tax_amount: invoiceDetails.tax_amount,
        discount_amount: invoiceDetails.discount_amount,
        notes: invoiceDetails.notes,
        terms_conditions: invoiceDetails.terms_conditions,
        items: invoiceItems.map(item => ({
          product: item.product.product,
          quantity: item.quantity,
          unit_price: item.unit_price,
          salesman_margin: item.salesman_margin,
          shop_margin: item.shop_margin,
        })),
      };

      const invoice = await invoiceService.createInvoice(invoiceData);
      toast.success('Invoice created successfully!');

      // Automatically download PDF
      try {
        await invoiceService.generateInvoicePDF(invoice.id);
        toast.success('Invoice PDF downloaded!');
      } catch (pdfError) {
        console.error('PDF generation error:', pdfError);
        toast.error('Invoice created but PDF download failed');
      }

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
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/invoices')}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Create New Invoice
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Select shop, add products, and generate invoice
              </p>
            </div>
          </div>
        </div>

        {/* Shop Selection */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Building2 className="h-5 w-5 mr-2" />
              Shop Selection
            </h2>
            {!selectedShop && (
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="btn-primary"
              >
                Select Shop
              </button>
            )}
          </div>

          {selectedShop ? (
            <div className="flex items-center justify-between p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div>
                <h3 className="font-medium text-gray-900 dark:text-white">{selectedShop.name}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Contact: {selectedShop.contact_person} • Phone: {selectedShop.phone}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Shop Margin: {selectedShop.shop_margin}%
                </p>
              </div>
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm"
              >
                Change Shop
              </button>
            </div>
          ) : (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">
                No shop selected. Please select a shop to continue.
              </p>
            </div>
          )}
        </div>

        {/* Products Section */}
        {selectedShop && (
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <Package className="h-5 w-5 mr-2" />
                Invoice Items ({invoiceItems.length})
              </h2>
              <button
                onClick={() => setIsProductModalOpen(true)}
                className="btn-primary flex items-center space-x-2"
              >
                <Plus className="h-4 w-4" />
                <span>Add Product</span>
              </button>
            </div>

            {invoiceItems.length > 0 ? (
              <div className="space-y-4">
                {/* Items Table */}
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Unit Price
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Salesman %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Shop %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Total
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      {invoiceItems.map((item) => (
                        <tr key={item.id}>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {item.product.product_name}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                SKU: {item.product.product_sku}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                Available: {item.product.available_quantity}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <input
                              type="number"
                              min="1"
                              max={item.product.available_quantity}
                              value={item.quantity}
                              onChange={(e) => updateInvoiceItem(item.id, { 
                                quantity: Math.max(1, Math.min(item.product.available_quantity, parseInt(e.target.value) || 1))
                              })}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={item.unit_price}
                              onChange={(e) => updateInvoiceItem(item.id, { 
                                unit_price: parseFloat(e.target.value) || 0
                              })}
                              className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              max="100"
                              value={item.salesman_margin}
                              onChange={(e) => updateInvoiceItem(item.id, { 
                                salesman_margin: parseFloat(e.target.value) || 0
                              })}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <input
                              type="number"
                              step="0.1"
                              min="0"
                              max="100"
                              value={item.shop_margin}
                              onChange={(e) => updateInvoiceItem(item.id, { 
                                shop_margin: parseFloat(e.target.value) || 0
                              })}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                            {formatCurrency(item.total)}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <button
                              onClick={() => removeInvoiceItem(item.id)}
                              className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Invoice Summary */}
                <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Invoice Details */}
                    <div className="space-y-4">
                      <div>
                        <label className="label">Due Date</label>
                        <input
                          type="date"
                          value={invoiceDetails.due_date}
                          onChange={(e) => setInvoiceDetails(prev => ({ ...prev, due_date: e.target.value }))}
                          className="input"
                        />
                      </div>
                      <div>
                        <label className="label">Tax Amount</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={invoiceDetails.tax_amount}
                          onChange={(e) => setInvoiceDetails(prev => ({ ...prev, tax_amount: parseFloat(e.target.value) || 0 }))}
                          className="input"
                          placeholder="0.00"
                        />
                      </div>
                      <div>
                        <label className="label">Discount Amount</label>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={invoiceDetails.discount_amount}
                          onChange={(e) => setInvoiceDetails(prev => ({ ...prev, discount_amount: parseFloat(e.target.value) || 0 }))}
                          className="input"
                          placeholder="0.00"
                        />
                      </div>
                      <div>
                        <label className="label">Notes</label>
                        <textarea
                          rows={3}
                          value={invoiceDetails.notes}
                          onChange={(e) => setInvoiceDetails(prev => ({ ...prev, notes: e.target.value }))}
                          className="input resize-none"
                          placeholder="Additional notes..."
                        />
                      </div>
                    </div>

                    {/* Totals */}
                    <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
                      <h3 className="font-medium text-gray-900 dark:text-white mb-3">
                        Invoice Summary
                      </h3>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Subtotal:</span>
                          <span className="font-medium">{formatCurrency(subtotal)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Tax:</span>
                          <span className="font-medium">{formatCurrency(invoiceDetails.tax_amount)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Discount:</span>
                          <span className="font-medium">-{formatCurrency(invoiceDetails.discount_amount)}</span>
                        </div>
                        <hr className="border-gray-200 dark:border-gray-600" />
                        <div className="flex justify-between text-lg font-semibold">
                          <span>Total:</span>
                          <span>{formatCurrency(total)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    onClick={() => navigate('/invoices')}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmitInvoice}
                    disabled={isSubmitting}
                    className="btn-primary flex items-center space-x-2"
                  >
                    {isSubmitting ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    <span>{isSubmitting ? 'Creating...' : 'Create & Download Invoice'}</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <ShoppingCart className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  No products added. Click "Add Product" to start building your invoice.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Shop Selection Modal */}
        {isShopModalOpen && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Select Shop
                    </h3>
                    <button
                      onClick={() => setIsShopModalOpen(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Search */}
                  <div className="mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search shops..."
                        value={shopSearchTerm}
                        onChange={(e) => setShopSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>

                  {/* Shop List */}
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {filteredShops.map((shop) => (
                      <div
                        key={shop.id}
                        onClick={() => handleSelectShop(shop)}
                        className="p-3 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className="font-medium text-gray-900 dark:text-white">{shop.name}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Contact: {shop.contact_person}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          Phone: {shop.phone} • Margin: {shop.shop_margin}%
                        </div>
                      </div>
                    ))}
                  </div>

                  {filteredShops.length === 0 && (
                    <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                      No shops found
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Product Selection Modal */}
        {isProductModalOpen && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Select Product
                    </h3>
                    <button
                      onClick={() => setIsProductModalOpen(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  {/* Search */}
                  <div className="mb-4">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search products..."
                        value={productSearchTerm}
                        onChange={(e) => setProductSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>

                  {/* Product List */}
                  <div className="max-h-96 overflow-y-auto">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {filteredProducts.map((stock) => (
                        <div
                          key={stock.id}
                          onClick={() => handleAddProduct(stock)}
                          className="p-4 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                          <div className="font-medium text-gray-900 dark:text-white">
                            {stock.product_name}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            SKU: {stock.product_sku}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            Available: {stock.available_quantity}
                          </div>
                          <div className="text-sm font-medium text-green-600 dark:text-green-400">
                            {formatCurrency(stock.product_base_price || 0)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {filteredProducts.length === 0 && (
                    <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                      No products found
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
