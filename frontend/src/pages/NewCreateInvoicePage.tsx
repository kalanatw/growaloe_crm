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
import { shopService, productService, invoiceService, companyService } from '../services/apiServices';
import { Shop, SalesmanStock, CreateInvoiceData } from '../types';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';
import { useAuth } from '../contexts/AuthContext';

interface InvoiceItem {
  id: string;
  product: SalesmanStock;
  quantity: number;
  unit_price: number;
  total: number; // unit_price * quantity
}

interface ProductSelectionState {
  product: SalesmanStock | null;
  quantity: number;
  unit_price: number;
}

export const NewCreateInvoicePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // State management
  const [selectedShop, setSelectedShop] = useState<Shop | null>(null);
  const [invoiceItems, setInvoiceItems] = useState<InvoiceItem[]>([]);
  const [shops, setShops] = useState<Shop[]>([]);
  const [stockData, setStockData] = useState<SalesmanStock[]>([]);
  
  // Modal states
  const [isShopModalOpen, setIsShopModalOpen] = useState(false);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  
  // Product selection state for the modal
  const [productSelection, setProductSelection] = useState<ProductSelectionState>({
    product: null,
    quantity: 1,
    unit_price: 0,
  });
  
  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Search states
  const [shopSearchTerm, setShopSearchTerm] = useState('');
  const [productSearchTerm, setProductSearchTerm] = useState('');
  
  // Invoice details with shop margin
  const [invoiceDetails, setInvoiceDetails] = useState({
    due_date: '',
    tax_amount: 0,
    discount_amount: 0,
    shop_margin: 0, // This will be set when shop is selected
    notes: '',
    terms_conditions: ''
  });

  // Company settings
  const [maxShopMargin, setMaxShopMargin] = useState<number>(20); // Default to 20%
  const userRole = user?.role || 'salesman'; // Get role from auth context

  useEffect(() => {
    loadInitialData();
  }, []);

  // Auto-open shop modal if no shop is selected
  useEffect(() => {
    if (!isLoading && shops.length > 0 && !selectedShop) {
      setTimeout(() => setIsShopModalOpen(true), 500);
    }
  }, [isLoading, shops.length, selectedShop]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only handle shortcuts if no modal is open and not typing in an input
      if (isShopModalOpen || isProductModalOpen || 
          (e.target as HTMLElement).tagName === 'INPUT' || 
          (e.target as HTMLElement).tagName === 'TEXTAREA') {
        return;
      }

      switch (e.key) {
        case 's':
        case 'S':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (selectedShop && invoiceItems.length > 0) {
              handleSubmitInvoice();
            }
          } else {
            setIsShopModalOpen(true);
          }
          break;
        case 'p':
        case 'P':
          if (selectedShop) {
            setIsProductModalOpen(true);
          }
          break;
        case 'Escape':
          setIsShopModalOpen(false);
          setIsProductModalOpen(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isShopModalOpen, isProductModalOpen, selectedShop, invoiceItems.length]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      // Choose the appropriate stock endpoint based on user role
      const stockPromise = userRole === 'owner' || userRole === 'developer' 
        ? productService.getProductsForInvoice()
        : productService.getMySalesmanStock();
      
      const [shopsData, stockDataResponse, companySettings] = await Promise.all([
        shopService.getShops(),
        stockPromise,
        companyService.getPublicSettings(),
      ]);

      setShops(shopsData.results);
      setStockData(stockDataResponse.stocks);
      setMaxShopMargin(companySettings.max_shop_margin_for_salesmen);
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
    
    // Set the shop's default margin
    setInvoiceDetails(prev => ({
      ...prev,
      shop_margin: shop.shop_margin || 0
    }));
    
    // Auto-open product modal if no products added yet
    if (invoiceItems.length === 0) {
      setTimeout(() => setIsProductModalOpen(true), 300);
    }
  };

  // Product selection in modal
  const handleSelectProductInModal = (product: SalesmanStock) => {
    const existingItem = invoiceItems.find(item => item.product.product === product.product);
    
    if (existingItem) {
      toast.error('Product already added to invoice');
      return;
    }
    
    setProductSelection({
      product,
      quantity: 1,
      unit_price: product.product_base_price || 0,
    });
  };

  // Calculate preview total in modal (simple unit price * quantity)
  const calculatePreviewTotal = () => {
    if (!productSelection.product) return 0;
    return productSelection.quantity * productSelection.unit_price;
  };

  // Add product from modal
  const handleAddProductFromModal = () => {
    if (!productSelection.product) {
      toast.error('Please select a product');
      return;
    }

    if (productSelection.quantity > productSelection.product.available_quantity) {
      toast.error(`Insufficient stock. Available: ${productSelection.product.available_quantity}`);
      return;
    }

    const newItem: InvoiceItem = {
      id: Math.random().toString(36).substr(2, 9),
      product: productSelection.product,
      quantity: productSelection.quantity,
      unit_price: productSelection.unit_price,
      total: productSelection.quantity * productSelection.unit_price,
    };

    setInvoiceItems(prev => [...prev, newItem]);
    
    // Reset selection
    setProductSelection({
      product: null,
      quantity: 1,
      unit_price: 0,
    });
    
    setProductSearchTerm('');
    toast.success(`${newItem.product.product_name} added to invoice`);
    
    // Keep modal open for quick addition of more products
  };

  // Quick add product (for experienced users)
  const handleQuickAddProduct = (product: SalesmanStock) => {
    const existingItem = invoiceItems.find(item => item.product.product === product.product);
    
    if (existingItem) {
      toast.error('Product already added to invoice');
      return;
    }

    const newItem: InvoiceItem = {
      id: Math.random().toString(36).substr(2, 9),
      product,
      quantity: 1,
      unit_price: product.product_base_price || 0,
      total: 1 * (product.product_base_price || 0),
    };

    setInvoiceItems(prev => [...prev, newItem]);
    toast.success(`${product.product_name} added to invoice`);
  };

  // Update item (simplified - only quantity and unit price)
  const updateInvoiceItem = (id: string, updates: Partial<InvoiceItem>) => {
    setInvoiceItems(prev => prev.map(item => {
      if (item.id === id) {
        const updatedItem = { ...item, ...updates };
        
        // Recalculate total when quantity or unit_price changes
        if ('quantity' in updates || 'unit_price' in updates) {
          updatedItem.total = updatedItem.quantity * updatedItem.unit_price;
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

  // Calculate totals with shop margin applied at invoice level
  const subtotal = invoiceItems.reduce((sum, item) => sum + item.total, 0);
  const shopMarginAmount = subtotal * (invoiceDetails.shop_margin / 100);
  const discountedTotal = subtotal - shopMarginAmount;
  const finalTotal = discountedTotal + invoiceDetails.tax_amount - invoiceDetails.discount_amount;

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

    // Validate shop margin for salesmen
    if (userRole === 'salesman' && invoiceDetails.shop_margin > maxShopMargin) {
      toast.error(`Shop margin cannot exceed ${maxShopMargin}% for salesmen`);
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
        shop_margin: invoiceDetails.shop_margin,
        notes: invoiceDetails.notes,
        terms_conditions: invoiceDetails.terms_conditions,
        items: invoiceItems.map(item => ({
          product: item.product.product,
          quantity: item.quantity,
          unit_price: item.unit_price,
          salesman_margin: 0, // No individual salesman margins
          shop_margin: 0, // Shop margin applied at invoice level now
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
          
          {/* Quick Summary */}
          {selectedShop && invoiceItems.length > 0 && (
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                {invoiceItems.length} items • {formatCurrency(finalTotal)}
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-300">
                {selectedShop.name}
              </div>
            </div>
          )}

          {/* Keyboard Shortcuts Help */}
          <div className="hidden sm:block">
            <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
              <div>Quick Keys: <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">S</kbd> Shop • <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">P</kbd> Products</div>
              {selectedShop && invoiceItems.length > 0 && (
                <div><kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">Ctrl+S</kbd> Create Invoice</div>
              )}
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 ${selectedShop ? 'text-green-600' : 'text-blue-600'}`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
              selectedShop ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
            }`}>
              {selectedShop ? '✓' : '1'}
            </div>
            <span className="text-sm font-medium">Select Shop</span>
          </div>
          <div className={`w-8 h-0.5 ${selectedShop ? 'bg-green-200' : 'bg-gray-200'}`}></div>
          <div className={`flex items-center space-x-2 ${
            selectedShop && invoiceItems.length > 0 ? 'text-green-600' : 
            selectedShop ? 'text-blue-600' : 'text-gray-400'
          }`}>
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
              selectedShop && invoiceItems.length > 0 ? 'bg-green-100 text-green-800' :
              selectedShop ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-500'
            }`}>
              {selectedShop && invoiceItems.length > 0 ? '✓' : '2'}
            </div>
            <span className="text-sm font-medium">Add Products</span>
          </div>
          <div className={`w-8 h-0.5 ${selectedShop && invoiceItems.length > 0 ? 'bg-green-200' : 'bg-gray-200'}`}></div>
          <div className={`flex items-center space-x-2 text-gray-400`}>
            <div className="w-6 h-6 rounded-full bg-gray-100 text-gray-500 flex items-center justify-center text-xs font-medium">
              3
            </div>
            <span className="text-sm font-medium">Create Invoice</span>
          </div>
        </div>

        {/* Shop Selection */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Building2 className="h-5 w-5 mr-2" />
              Shop Selection
            </h2>
            {!selectedShop ? (
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="btn-primary flex items-center space-x-2"
              >
                <Building2 className="h-4 w-4" />
                <span>Select Shop</span>
              </button>
            ) : (
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium"
              >
                Change Shop
              </button>
            )}
          </div>

          {selectedShop ? (
            <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h3 className="font-medium text-gray-900 dark:text-white">{selectedShop.name}</h3>
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">Selected</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Contact: {selectedShop.contact_person} • Phone: {selectedShop.phone}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Shop Margin: {selectedShop.shop_margin}% • {stockData.length} products available
                </p>
              </div>
              {invoiceItems.length === 0 && (
                <button
                  onClick={() => setIsProductModalOpen(true)}
                  className="ml-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 text-sm"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add Products</span>
                </button>
              )}
            </div>
          ) : (
            <div className="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Select a Shop to Start
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Choose which shop this invoice is for, then add products to begin building your invoice.
              </p>
              <button
                onClick={() => setIsShopModalOpen(true)}
                className="btn-primary"
              >
                Choose Shop
              </button>
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
                        <label className="label">Shop Margin (%)</label>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max={userRole === 'salesman' ? maxShopMargin : 100}
                          value={invoiceDetails.shop_margin}
                          onChange={(e) => {
                            const value = parseFloat(e.target.value) || 0;
                            if (userRole === 'salesman' && value > maxShopMargin) {
                              toast.error(`Salesmen cannot set shop margin above ${maxShopMargin}%`);
                              return;
                            }
                            setInvoiceDetails(prev => ({ ...prev, shop_margin: value }));
                          }}
                          className={`input ${
                            userRole === 'salesman' && invoiceDetails.shop_margin > maxShopMargin 
                              ? 'border-red-500 focus:border-red-500' 
                              : ''
                          }`}
                          placeholder="0.0"
                        />
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          Shop margin to be applied to the total price
                          {userRole === 'salesman' && (
                            <span className="block text-orange-600 dark:text-orange-400">
                              Maximum allowed for salesmen: {maxShopMargin}%
                            </span>
                          )}
                        </p>
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
                          <span className="text-gray-600 dark:text-gray-400">Total Product Price:</span>
                          <span className="font-medium">{formatCurrency(subtotal)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">Shop Margin ({invoiceDetails.shop_margin}%):</span>
                          <span className="font-medium text-red-600">-{formatCurrency(shopMarginAmount)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">After Margin:</span>
                          <span className="font-medium">{formatCurrency(discountedTotal)}</span>
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
                          <span>Invoice Total:</span>
                          <span>{formatCurrency(finalTotal)}</span>
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
                    title="Ctrl+S to create invoice"
                  >
                    {isSubmitting ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    <span>{isSubmitting ? 'Creating...' : 'Create & Download Invoice'}</span>
                    <kbd className="hidden sm:inline-block ml-2 px-1 py-0.5 bg-white bg-opacity-20 rounded text-xs">
                      Ctrl+S
                    </kbd>
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <ShoppingCart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Ready to Add Products
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">
                  Great! You've selected <strong>{selectedShop.name}</strong>.<br />
                  Now add products to build your invoice.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <button
                    onClick={() => setIsProductModalOpen(true)}
                    className="btn-primary flex items-center justify-center space-x-2"
                  >
                    <Plus className="h-5 w-5" />
                    <span>Add Your First Product</span>
                  </button>
                  <p className="text-sm text-gray-500 dark:text-gray-400 sm:self-center">
                    {stockData.length} products available
                  </p>
                </div>
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

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Add Product to Invoice
                    </h3>
                    <button
                      onClick={() => {
                        setIsProductModalOpen(false);
                        setProductSelection({
                          product: null,
                          quantity: 1,
                          unit_price: 0,
                        });
                      }}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Product Selection Panel */}
                    <div className="lg:col-span-2">
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
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {filteredProducts.map((stock) => {
                            const isSelected = productSelection.product?.product === stock.product;
                            const isAlreadyAdded = invoiceItems.some(item => item.product.product === stock.product);
                            
                            return (
                              <div
                                key={stock.id}
                                className={`relative p-3 border rounded-lg cursor-pointer transition-all ${
                                  isSelected
                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                    : isAlreadyAdded
                                    ? 'border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 opacity-50'
                                    : 'border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                                }`}
                              >
                                {isAlreadyAdded && (
                                  <div className="absolute top-2 right-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                                    Added
                                  </div>
                                )}
                                
                                <div 
                                  onClick={() => !isAlreadyAdded && handleSelectProductInModal(stock)}
                                  className={isAlreadyAdded ? 'cursor-not-allowed' : ''}
                                >
                                  <div className="font-medium text-gray-900 dark:text-white text-sm">
                                    {stock.product_name}
                                  </div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400">
                                    SKU: {stock.product_sku}
                                  </div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400">
                                    Available: {stock.available_quantity}
                                  </div>
                                  <div className="text-sm font-medium text-green-600 dark:text-green-400 mt-1">
                                    {formatCurrency(stock.product_base_price || 0)}
                                  </div>
                                </div>
                                
                                {!isAlreadyAdded && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleQuickAddProduct(stock);
                                    }}
                                    className="absolute bottom-2 right-2 bg-blue-600 hover:bg-blue-700 text-white text-xs px-2 py-1 rounded"
                                    title="Quick add with default settings"
                                  >
                                    Quick Add
                                  </button>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {filteredProducts.length === 0 && (
                        <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                          No products found
                        </p>
                      )}
                    </div>

                    {/* Product Configuration Panel */}
                    <div className="lg:col-span-1">
                      {productSelection.product ? (
                        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                          <h4 className="font-medium text-gray-900 dark:text-white mb-3">
                            Configure Product
                          </h4>
                          
                          {/* Selected Product Info */}
                          <div className="mb-4 p-3 bg-white dark:bg-gray-800 rounded border">
                            <div className="font-medium text-sm">{productSelection.product.product_name}</div>
                            <div className="text-xs text-gray-600 dark:text-gray-400">
                              SKU: {productSelection.product.product_sku}
                            </div>
                            <div className="text-xs text-gray-600 dark:text-gray-400">
                              Available: {productSelection.product.available_quantity}
                            </div>
                          </div>

                          {/* Configuration Form */}
                          <div className="space-y-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Quantity
                              </label>
                              <input
                                type="number"
                                min="1"
                                max={productSelection.product.available_quantity}
                                value={productSelection.quantity}
                                onChange={(e) => setProductSelection(prev => ({
                                  ...prev,
                                  quantity: Math.max(1, Math.min(prev.product?.available_quantity || 1, parseInt(e.target.value) || 1))
                                }))}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Unit Price
                              </label>
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={productSelection.unit_price}
                                onChange={(e) => setProductSelection(prev => ({
                                  ...prev,
                                  unit_price: parseFloat(e.target.value) || 0
                                }))}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                              />
                            </div>

                            {/* Preview Total */}
                            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                Total: {formatCurrency(calculatePreviewTotal())}
                              </div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                {productSelection.quantity} × {formatCurrency(productSelection.unit_price)}
                              </div>
                            </div>

                            {/* Add Button */}
                            <button
                              onClick={handleAddProductFromModal}
                              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md flex items-center justify-center space-x-2"
                            >
                              <Plus className="h-4 w-4" />
                              <span>Add to Invoice</span>
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center">
                          <Package className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            Select a product to configure
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
                    <div className="flex justify-between items-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Tip: Use "Quick Add" for fast product addition with default settings
                      </p>
                      <div className="flex space-x-3">
                        <button
                          onClick={() => {
                            setIsProductModalOpen(false);
                            setInvoiceDetails(prev => ({
                              ...prev,
                              shop_margin: invoiceDetails.shop_margin
                            }));
                            setProductSelection({
                              product: null,
                              quantity: 1,
                              unit_price: 0,
                            });
                          }}
                          className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                        >
                          Done
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Floating Add Product Button */}
        {selectedShop && (
          <div className="fixed bottom-6 right-6 z-40">
            <button
              onClick={() => setIsProductModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center space-x-2"
              title="Add Product"
            >
              <Plus className="h-6 w-6" />
              {invoiceItems.length === 0 && (
                <span className="hidden sm:block">Add Product</span>
              )}
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};
