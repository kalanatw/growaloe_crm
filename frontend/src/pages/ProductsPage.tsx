import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard, LoadingSpinner } from '../components/LoadingSpinner';
import { 
  Package, 
  AlertTriangle, 
  Plus, 
  Search, 
  Filter, 
  SortAsc, 
  SortDesc, 
  Eye, 
  Edit, 
  Trash2, 
  DollarSign, 
  Tag, 
  Image,
  X,
  Calculator
} from 'lucide-react';
import { productService } from '../services/apiServices';
import { Product, SalesmanStock, Category, CreateProductData, ProfitCalculation } from '../types';
import { formatCurrency } from '../utils/currency';
import { useAuth } from '../contexts/AuthContext';
import { USER_ROLES } from '../config/constants';
import toast from 'react-hot-toast';
import { useForm } from 'react-hook-form';

export const ProductsPage: React.FC = () => {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stockData, setStockData] = useState<{
    stocks: SalesmanStock[];
    summary: { total_products: number; total_stock_value: number };
  } | null>(null);
  const [stockSummary, setStockSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isProfitModalOpen, setIsProfitModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [profitCalculation, setProfitCalculation] = useState<ProfitCalculation | null>(null);
  const [filter, setFilter] = useState<'all' | 'low_stock' | 'products'>('all');
  const [view, setView] = useState<'table' | 'cards'>('table');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'stock' | 'price' | 'category'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<CreateProductData>();

  useEffect(() => {
    loadInitialData();
  }, [user]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      if (user?.role === USER_ROLES.OWNER) {
        // Owner can see all products and stock summary
        const [productsData, categoriesData, stockSummaryData] = await Promise.all([
          productService.getProducts(),
          productService.getCategories(),
          productService.getProductStockSummary()
        ]);
        setProducts(productsData.results || []);
        setCategories(categoriesData.results || categoriesData);
        setStockSummary(stockSummaryData);
      } else if (user?.role === USER_ROLES.SALESMAN) {
        // Salesman can see their allocated stock
        const [stockData, categoriesData] = await Promise.all([
          productService.getMySalesmanStock(),
          productService.getCategories()
        ]);
        setStockData(stockData);
        setCategories(categoriesData.results || categoriesData);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load products data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateProduct = async (data: CreateProductData) => {
    try {
      setIsSubmitting(true);
      
      if (selectedProduct) {
        // Update existing product
        await productService.updateProduct(selectedProduct.id, data);
        toast.success('Product updated successfully!');
      } else {
        // Create new product
        await productService.createProduct(data);
        toast.success('Product created successfully!');
      }
      
      setIsProductModalOpen(false);
      setSelectedProduct(null);
      reset();
      loadInitialData();
    } catch (error: any) {
      console.error('Error saving product:', error);
      toast.error(error.response?.data?.detail || `Failed to ${selectedProduct ? 'update' : 'create'} product`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCalculateProfit = async (product: Product) => {
    try {
      const salesmanMargin = 10; // Default salesman margin, could be dynamic
      const shopMargin = 15; // Default shop margin, could be dynamic
      
      const basePrice = Number(product.base_price);
      const costPrice = Number(product.cost_price);
      
      // Calculate selling price with margins
      const salesmanMarginAmount = basePrice * (salesmanMargin / 100);
      const shopMarginAmount = (basePrice + salesmanMarginAmount) * (shopMargin / 100);
      const sellingPrice = basePrice + salesmanMarginAmount + shopMarginAmount;
      
      const calculation: ProfitCalculation = {
        cost_price: costPrice,
        base_price: basePrice,
        selling_price: sellingPrice,
        total_profit: sellingPrice - costPrice,
        salesman_margin_amount: salesmanMarginAmount,
        shop_margin_amount: shopMarginAmount,
        owner_profit: basePrice - costPrice,
        profit_percentage: ((sellingPrice - costPrice) / sellingPrice) * 100
      };

      setSelectedProduct(product);
      setProfitCalculation(calculation);
      setIsProfitModalOpen(true);
    } catch (error) {
      console.error('Error calculating profit:', error);
      toast.error('Failed to calculate profit');
    }
  };

  const handleEditProduct = (product: Product) => {
    setSelectedProduct(product);
    // Reset form with product data
    reset({
      name: product.name,
      sku: product.sku,
      description: product.description || '',
      category: product.category?.id || undefined,
      base_price: product.base_price,
      cost_price: product.cost_price,
      stock_quantity: product.stock_quantity,
      min_stock_level: product.min_stock_level,
      image_url: product.image_url || '',
      is_active: product.is_active
    });
    setIsProductModalOpen(true);
  };

  const handleDeleteProduct = async (productId: number, productName: string) => {
    if (window.confirm(`Are you sure you want to delete "${productName}"? This action cannot be undone.`)) {
      try {
        await productService.deleteProduct(productId);
        toast.success('Product deleted successfully!');
        loadInitialData();
      } catch (error: any) {
        console.error('Error deleting product:', error);
        toast.error(error.response?.data?.detail || 'Failed to delete product');
      }
    }
  };

  const handleViewProduct = (product: Product) => {
    setSelectedProduct(product);
    // You can implement a view modal or navigate to a detail page
    toast(`Viewing product: ${product.name}`, {
      icon: '👀',
    });
  };

  const isOwner = user?.role === USER_ROLES.OWNER;
  const isSalesman = user?.role === USER_ROLES.SALESMAN;

  // Filter and sort data based on current view
  const getFilteredData = () => {
    let data: any[] = [];
    
    if (isOwner && filter === 'products') {
      data = products;
    } else if (isSalesman || filter === 'all' || filter === 'low_stock') {
      data = stockData?.stocks || [];
    }

    // Apply search filter
    if (searchTerm) {
      data = data.filter((item) => {
        const name = 'product_name' in item ? item.product_name : item.name;
        const sku = 'product_sku' in item ? item.product_sku : item.sku;
        return name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
               sku?.toLowerCase().includes(searchTerm.toLowerCase());
      });
    }

    // Apply category filter
    if (selectedCategory) {
      data = data.filter((item) => {
        const categoryId = 'category' in item ? item.category : item.product_category;
        return categoryId === selectedCategory;
      });
    }

    // Apply stock filter
    if (filter === 'low_stock') {
      data = data.filter((item) => {
        const quantity = 'available_quantity' in item ? item.available_quantity : item.stock_quantity;
        return quantity <= 5;
      });
    }

    return data;
  };

  const filteredData = getFilteredData();
  const lowStockCount = (stockData?.stocks || []).filter(stock => stock.available_quantity <= 5).length;
  const totalProducts = isOwner ? products.length : stockData?.summary.total_products || 0;

  if (isLoading) {
    return (
      <Layout title="Products & Stock">
        <LoadingCard title="Loading products data..." />
      </Layout>
    );
  }

  return (
    <Layout title="Products & Stock">
      <div className="space-y-6">
        {/* Header with Actions */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div className="flex items-center space-x-3">
            <Package className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Products & Stock Management
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {isOwner ? 'Manage your product catalog and inventory' : 'View your allocated product inventory'}
              </p>
            </div>
          </div>
          
          {isOwner && (
            <button
              onClick={() => setIsProductModalOpen(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Add Product</span>
            </button>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div 
            className="card p-6 cursor-pointer hover:shadow-lg transition-shadow duration-200"
            onClick={() => setFilter('all')}
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                <Package className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Products
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {totalProducts}
                </p>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Click for breakdown
            </div>
          </div>

          <div 
            className="card p-6 cursor-pointer hover:shadow-lg transition-shadow duration-200"
            onClick={() => setFilter('low_stock')}
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-red-500">
                <AlertTriangle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Low Stock Items
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {lowStockCount}
                </p>
              </div>
            </div>
            <div className="mt-2 text-xs text-red-600 dark:text-red-400">
              Needs attention
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
                <DollarSign className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Stock Value
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {formatCurrency(
                    isOwner ? stockSummary?.total_value || 0 : stockData?.summary.total_stock_value || 0, 
                    { useLocaleString: true }
                  )}
                </p>
              </div>
            </div>
          </div>

          {isOwner && (
            <div 
              className="card p-6 cursor-pointer hover:shadow-lg transition-shadow duration-200"
              onClick={() => setFilter('products')}
            >
              <div className="flex items-center">
                <div className="flex-shrink-0 p-3 rounded-lg bg-purple-500">
                  <Tag className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                    Product Catalog
                  </p>
                  <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                    {products.length}
                  </p>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                All products
              </div>
            </div>
          )}
        </div>

        {/* Low Stock Alert */}
        {lowStockCount > 0 && filter !== 'low_stock' && (
          <div className="card p-4 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {lowStockCount} product{lowStockCount > 1 ? 's' : ''} running low on stock
                </p>
                <button
                  onClick={() => setFilter('low_stock')}
                  className="text-sm text-red-600 hover:text-red-800 dark:text-red-300 dark:hover:text-red-200 underline"
                >
                  View low stock items →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="card p-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                />
              </div>

              <select
                value={selectedCategory || ''}
                onChange={(e) => setSelectedCategory(e.target.value ? Number(e.target.value) : null)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              {/* Filter Buttons */}
              <div className="flex space-x-1">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    filter === 'all'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  All Stock
                </button>
                <button
                  onClick={() => setFilter('low_stock')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    filter === 'low_stock'
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  Low Stock
                </button>
                {isOwner && (
                  <button
                    onClick={() => setFilter('products')}
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                      filter === 'products'
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    Products
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Products Table/Cards */}
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    SKU
                  </th>
                  {filter !== 'products' && (
                    <>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Allocated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Available
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Sold
                      </th>
                    </>
                  )}
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Price (MRP)
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {filteredData.length > 0 ? (
                  filteredData.map((item: any) => {
                    const isStock = 'product_name' in item;
                    const name = isStock ? item.product_name : item.name;
                    const sku = isStock ? item.product_sku : item.sku;
                    const price = isStock ? item.base_price : item.base_price;
                    const isLowStock = isStock ? item.available_quantity <= 5 : item.stock_quantity <= 5;
                    const soldQuantity = isStock ? item.allocated_quantity - item.available_quantity : 0;

                    return (
                      <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            {item.image_url && (
                              <img 
                                src={item.image_url} 
                                alt={name}
                                className="h-10 w-10 rounded-lg object-cover mr-3"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = 'none';
                                }}
                              />
                            )}
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {name}
                              </div>
                              {item.category_name && (
                                <div className="text-xs text-gray-500 dark:text-gray-400">
                                  {item.category_name}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-white">
                            {sku}
                          </div>
                        </td>
                        {filter !== 'products' && (
                          <>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900 dark:text-white">
                                {item.allocated_quantity || 0}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className={`text-sm font-medium ${
                                isLowStock ? 'text-red-600' : 'text-gray-900 dark:text-white'
                              }`}>
                                {item.available_quantity || item.stock_quantity || 0}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm text-gray-900 dark:text-white">
                                {soldQuantity}
                              </div>
                            </td>
                          </>
                        )}
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {formatCurrency(price || 0)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                              isLowStock
                                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                : (item.available_quantity || item.stock_quantity || 0) > 20
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                            }`}
                          >
                            {isLowStock ? 'Low Stock' : (item.available_quantity || item.stock_quantity || 0) > 20 ? 'In Stock' : 'Medium'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleCalculateProfit(isStock ? { 
                                ...item, 
                                name: item.product_name, 
                                sku: item.product_sku 
                              } : item)}
                              className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                              title="Calculate Profit"
                            >
                              <Calculator className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleViewProduct(isStock ? { 
                                ...item, 
                                name: item.product_name, 
                                sku: item.product_sku 
                              } : item)}
                              className="text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                              title="View Details"
                            >
                              <Eye className="h-4 w-4" />
                            </button>
                            {isOwner && filter === 'products' && (
                              <>
                                <button
                                  onClick={() => handleEditProduct(item)}
                                  className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                                  title="Edit Product"
                                >
                                  <Edit className="h-4 w-4" />
                                </button>
                                <button
                                  onClick={() => handleDeleteProduct(item.id, item.name)}
                                  className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                                  title="Delete Product"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="px-6 py-8 text-center">
                      <div className="flex flex-col items-center">
                        <Package className="h-12 w-12 text-gray-400 mb-4" />
                        <p className="text-gray-500 dark:text-gray-400">
                          {filter === 'low_stock' ? 'No low stock items found' : 
                           filter === 'products' ? 'No products found' : 'No stock items found'}
                        </p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Product Creation Modal */}
        {isProductModalOpen && isOwner && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                <form onSubmit={handleSubmit(handleCreateProduct)}>
                  <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                        {selectedProduct ? 'Edit Product' : 'Add New Product'}
                      </h3>
                      <button
                        type="button"
                        onClick={() => {
                          setIsProductModalOpen(false);
                          setSelectedProduct(null);
                          reset();
                        }}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        <X className="h-5 w-5" />
                      </button>
                    </div>

                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="label">Product Name *</label>
                          <input
                            {...register('name', { required: 'Product name is required' })}
                            type="text"
                            className="input"
                            placeholder="Enter product name"
                          />
                          {errors.name && (
                            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                          )}
                        </div>

                        <div>
                          <label className="label">SKU *</label>
                          <input
                            {...register('sku', { required: 'SKU is required' })}
                            type="text"
                            className="input"
                            placeholder="Enter SKU"
                          />
                          {errors.sku && (
                            <p className="mt-1 text-sm text-red-600">{errors.sku.message}</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <label className="label">Description</label>
                        <textarea
                          {...register('description')}
                          rows={3}
                          className="input resize-none"
                          placeholder="Enter product description"
                        />
                      </div>

                      <div>
                        <label className="label">Category *</label>
                        <select
                          {...register('category', { required: 'Category is required' })}
                          className="input"
                        >
                          <option value="">Select category</option>
                          {categories.map((category) => (
                            <option key={category.id} value={category.id}>
                              {category.name}
                            </option>
                          ))}
                        </select>
                        {errors.category && (
                          <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="label">MRP (Base Price) *</label>
                          <input
                            {...register('base_price', { 
                              required: 'Base price is required',
                              valueAsNumber: true,
                              min: { value: 0, message: 'Price must be positive' }
                            })}
                            type="number"
                            step="0.01"
                            min="0"
                            className="input"
                            placeholder="0.00"
                          />
                          {errors.base_price && (
                            <p className="mt-1 text-sm text-red-600">{errors.base_price.message}</p>
                          )}
                        </div>

                        <div>
                          <label className="label">Cost Price *</label>
                          <input
                            {...register('cost_price', { 
                              required: 'Cost price is required',
                              valueAsNumber: true,
                              min: { value: 0, message: 'Price must be positive' }
                            })}
                            type="number"
                            step="0.01"
                            min="0"
                            className="input"
                            placeholder="0.00"
                          />
                          {errors.cost_price && (
                            <p className="mt-1 text-sm text-red-600">{errors.cost_price.message}</p>
                          )}
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="label">Stock Quantity</label>
                          <input
                            {...register('stock_quantity', { 
                              valueAsNumber: true,
                              min: { value: 0, message: 'Stock quantity cannot be negative' }
                            })}
                            type="number"
                            min="0"
                            className="input"
                            placeholder="0"
                          />
                          {errors.stock_quantity && (
                            <p className="mt-1 text-sm text-red-600">{errors.stock_quantity.message}</p>
                          )}
                        </div>

                        <div>
                          <label className="label">Minimum Stock Level</label>
                          <input
                            {...register('min_stock_level', { 
                              valueAsNumber: true,
                              min: { value: 0, message: 'Minimum stock level cannot be negative' }
                            })}
                            type="number"
                            min="0"
                            className="input"
                            placeholder="5"
                          />
                          {errors.min_stock_level && (
                            <p className="mt-1 text-sm text-red-600">{errors.min_stock_level.message}</p>
                          )}
                        </div>
                      </div>

                      <div>
                        <label className="label">Image URL</label>
                        <input
                          {...register('image_url')}
                          type="url"
                          className="input"
                          placeholder="https://example.com/image.jpg"
                        />
                      </div>

                      <div className="flex items-center">
                        <input
                          {...register('is_active')}
                          type="checkbox"
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          defaultChecked={true}
                        />
                        <label className="ml-2 block text-sm text-gray-900 dark:text-white">
                          Active product
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                    >
                      {isSubmitting ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        selectedProduct ? 'Update Product' : 'Create Product'
                      )}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsProductModalOpen(false);
                        setSelectedProduct(null);
                        reset();
                      }}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-600 dark:text-gray-200 dark:border-gray-500 dark:hover:bg-gray-700"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Profit Calculation Modal */}
        {isProfitModalOpen && selectedProduct && profitCalculation && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Profit Calculation
                    </h3>
                    <button
                      onClick={() => setIsProfitModalOpen(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {selectedProduct.name}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        SKU: {selectedProduct.sku}
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">MRP (Base Price):</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(profitCalculation.base_price)}
                        </span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Cost Price:</span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(profitCalculation.cost_price)}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Salesman Margin:</span>
                        <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                          10.0%
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Shop Margin:</span>
                        <span className="text-sm font-medium text-green-600 dark:text-green-400">
                          15.0%
                        </span>
                      </div>

                      <hr className="border-gray-200 dark:border-gray-600" />

                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">Selling Price:</span>
                        <span className="text-sm font-bold text-green-600 dark:text-green-400">
                          {formatCurrency(profitCalculation.selling_price)}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">Total Profit:</span>
                        <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                          {formatCurrency(profitCalculation.total_profit)}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">Profit %:</span>
                        <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                          {profitCalculation.profit_percentage.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6">
                  <button
                    onClick={() => setIsProfitModalOpen(false)}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:text-sm"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
