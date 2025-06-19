import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard, LoadingSpinner } from '../components/LoadingSpinner';
import { 
  Package, 
  AlertTriangle, 
  Plus, 
  Search, 
  Eye, 
  Edit, 
  Trash2, 
  DollarSign, 
  X,
  RefreshCw
} from 'lucide-react';
import { productService } from '../services/apiServices';
import { Product, SalesmanStock, Category, CreateProductData } from '../types';
import { formatCurrency } from '../utils/currency';
import { useAuth } from '../contexts/AuthContext';
import { USER_ROLES } from '../config/constants';
import toast from 'react-hot-toast';
import { useForm } from 'react-hook-form';

// Unified product/stock item interface for table display
interface UnifiedProductItem {
  id: number;
  name: string;
  sku: string;
  category_name?: string;
  image_url?: string;
  base_price: number;
  stock_quantity: number;
  allocated_quantity?: number;
  available_quantity?: number;
  min_stock_level: number;
  is_active: boolean;
  isLowStock: boolean;
  product?: Product; // Original product for owners
  stock?: SalesmanStock; // Original stock for salesmen
}

export const ProductsPage: React.FC = () => {
  const { user } = useAuth();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [stockData, setStockData] = useState<{
    stocks: SalesmanStock[];
    summary: { total_products: number; total_stock_value: number };
  } | null>(null);
  const [stockSummary, setStockSummary] = useState<any>(null);
  const [unifiedItems, setUnifiedItems] = useState<UnifiedProductItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isRestockModalOpen, setIsRestockModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [restockProduct, setRestockProduct] = useState<UnifiedProductItem | null>(null);
  const [restockQuantity, setRestockQuantity] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateProductData>();

  const isOwner = user?.role === USER_ROLES.OWNER;
  const isSalesman = user?.role === USER_ROLES.SALESMAN;

  useEffect(() => {
    loadInitialData();
  }, [user]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      // Load categories for all users
      const categoriesData = await productService.getCategories();
      setCategories(categoriesData.results || categoriesData);
      
      if (isOwner) {
        // Owners see all products
        const productsData = await productService.getProducts();
        setProducts(productsData.results || []);
        
        // Try to load stock summary
        try {
          const stockSummaryData = await productService.getProductStockSummary();
          setStockSummary(stockSummaryData);
        } catch (error) {
          console.log('Stock summary not available');
        }
      } else if (isSalesman) {
        // Salesmen see their allocated stock
        try {
          const salesmanStockData = await productService.getMySalesmanStock();
          setStockData(salesmanStockData);
        } catch (error) {
          console.log('Salesman stock not available');
          setStockData({ stocks: [], summary: { total_products: 0, total_stock_value: 0 } });
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load products data');
    } finally {
      setIsLoading(false);
    }
  };

  // Create unified items for table display
  useEffect(() => {
    const items: UnifiedProductItem[] = [];

    if (isOwner && products.length > 0) {
      // For owners, show all products with their stock info
      products.forEach(product => {
        const isLowStock = product.stock_quantity <= (product.min_stock_level || 5);
        items.push({
          id: product.id,
          name: product.name,
          sku: product.sku,
          category_name: product.category?.name,
          image_url: product.image_url,
          base_price: product.base_price,
          stock_quantity: product.stock_quantity,
          min_stock_level: product.min_stock_level,
          is_active: product.is_active,
          isLowStock,
          product
        });
      });
    } else if (isSalesman && stockData?.stocks) {
      // For salesmen, show their allocated stock
      stockData.stocks.forEach(stock => {
        const isLowStock = stock.available_quantity <= 5;
        items.push({
          id: stock.id,
          name: stock.product_name,
          sku: stock.product_sku,
          base_price: stock.product_base_price,
          stock_quantity: stock.available_quantity,
          allocated_quantity: stock.allocated_quantity,
          available_quantity: stock.available_quantity,
          min_stock_level: 5, // Default for salesmen
          is_active: true,
          isLowStock,
          stock
        });
      });
    }

    // Sort by low stock first, then by name
    items.sort((a, b) => {
      if (a.isLowStock && !b.isLowStock) return -1;
      if (!a.isLowStock && b.isLowStock) return 1;
      return a.name.localeCompare(b.name);
    });

    setUnifiedItems(items);
  }, [products, stockData, isOwner, isSalesman]);

  const handleCreateProduct = async (data: CreateProductData) => {
    try {
      setIsSubmitting(true);
      
      // Only require retail price (base_price), set cost_price to 0 if not provided
      const productData = {
        ...data,
        cost_price: 0, // Simplified: no cost price needed
        unit: data.unit || 'pcs' // Default unit
      };
      
      if (selectedProduct) {
        // Update existing product
        await productService.updateProduct(selectedProduct.id, productData);
        toast.success('Product updated successfully!');
      } else {
        // Create new product
        await productService.createProduct(productData);
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

  const handleRestock = async () => {
    if (!restockProduct || restockQuantity <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }

    try {
      setIsSubmitting(true);
      
      if (restockProduct.product) {
        // For owners, update the product's stock quantity
        const updatedData = {
          name: restockProduct.product.name,
          sku: restockProduct.product.sku,
          description: restockProduct.product.description,
          category: restockProduct.product.category?.id,
          base_price: restockProduct.product.base_price,
          cost_price: restockProduct.product.cost_price,
          unit: restockProduct.product.unit,
          stock_quantity: restockProduct.product.stock_quantity + restockQuantity,
          min_stock_level: restockProduct.product.min_stock_level,
          image_url: restockProduct.product.image_url,
          is_active: restockProduct.product.is_active
        };
        
        await productService.updateProduct(restockProduct.product.id, updatedData);
        toast.success(`Added ${restockQuantity} units to ${restockProduct.name}`);
      }
      
      setIsRestockModalOpen(false);
      setRestockProduct(null);
      setRestockQuantity(0);
      loadInitialData();
    } catch (error: any) {
      console.error('Error restocking product:', error);
      toast.error(error.response?.data?.detail || 'Failed to restock product');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenRestock = (item: UnifiedProductItem) => {
    setRestockProduct(item);
    setRestockQuantity(0);
    setIsRestockModalOpen(true);
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
      unit: product.unit,
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

  const handleViewProduct = (item: UnifiedProductItem) => {
    toast(`Viewing: ${item.name}`, { icon: '👀' });
  };

  // Filter items based on search and category
  const filteredItems = unifiedItems.filter(item => {
    const matchesSearch = !searchTerm || 
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.sku.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = !selectedCategory || 
      (item.product?.category?.id === selectedCategory);

    return matchesSearch && matchesCategory;
  });

  const lowStockCount = filteredItems.filter(item => item.isLowStock).length;
  const totalProducts = filteredItems.length;
  const totalStockValue = isOwner 
    ? stockSummary?.total_value || 0 
    : stockData?.summary.total_stock_value || 0;

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
              onClick={() => {
                setSelectedProduct(null);
                reset();
                setIsProductModalOpen(true);
              }}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Add Product</span>
            </button>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card p-6">
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
          </div>

          <div className="card p-6">
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
            {lowStockCount > 0 && (
              <div className="mt-2 text-xs text-red-600 dark:text-red-400">
                Needs attention
              </div>
            )}
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
                  {formatCurrency(totalStockValue, { useLocaleString: true })}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Low Stock Alert */}
        {lowStockCount > 0 && (
          <div className="card p-4 border-l-4 border-red-500 bg-red-50 dark:bg-red-900/20">
            <div className="flex items-center">
              <AlertTriangle className="h-5 w-5 text-red-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-200">
                  {lowStockCount} product{lowStockCount > 1 ? 's' : ''} running low on stock
                </p>
                <p className="text-sm text-red-600 dark:text-red-300">
                  Low stock items are shown at the top of the table
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
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

            <div className="text-sm text-gray-500 dark:text-gray-400">
              Showing {filteredItems.length} product{filteredItems.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Unified Products/Stock Table */}
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
                  {isSalesman && (
                    <>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Allocated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Available
                      </th>
                    </>
                  )}
                  {isOwner && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Stock Quantity
                    </th>
                  )}
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Retail Price
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
                {filteredItems.length > 0 ? (
                  filteredItems.map((item) => (
                    <tr 
                      key={`${isOwner ? 'product' : 'stock'}-${item.id}`} 
                      className={`hover:bg-gray-50 dark:hover:bg-gray-800 ${
                        item.isLowStock ? 'bg-red-50 dark:bg-red-900/10' : ''
                      }`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {item.image_url && (
                            <img 
                              src={item.image_url} 
                              alt={item.name}
                              className="h-10 w-10 rounded-lg object-cover mr-3"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          )}
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {item.name}
                              {item.isLowStock && (
                                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                                  Low Stock
                                </span>
                              )}
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
                          {item.sku}
                        </div>
                      </td>
                      {isSalesman && (
                        <>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900 dark:text-white">
                              {item.allocated_quantity || 0}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className={`text-sm font-medium ${
                              item.isLowStock ? 'text-red-600' : 'text-gray-900 dark:text-white'
                            }`}>
                              {item.available_quantity || 0}
                            </div>
                          </td>
                        </>
                      )}
                      {isOwner && (
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className={`text-sm font-medium ${
                            item.isLowStock ? 'text-red-600' : 'text-gray-900 dark:text-white'
                          }`}>
                            {item.stock_quantity}
                          </div>
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {formatCurrency(item.base_price)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                            item.isLowStock
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : item.stock_quantity > 20
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
                          }`}
                        >
                          {item.isLowStock ? 'Low Stock' : item.stock_quantity > 20 ? 'In Stock' : 'Medium'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => handleViewProduct(item)}
                            className="text-gray-600 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          {isOwner && (
                            <>
                              <button
                                onClick={() => handleOpenRestock(item)}
                                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                                title="Restock Product"
                              >
                                <RefreshCw className="h-4 w-4" />
                              </button>
                              {item.product && (
                                <>
                                  <button
                                    onClick={() => item.product && handleEditProduct(item.product)}
                                    className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
                                    title="Edit Product"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </button>
                                  <button
                                    onClick={() => item.product && handleDeleteProduct(item.product.id, item.product.name)}
                                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                                    title="Delete Product"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={isOwner ? 6 : 7} className="px-6 py-8 text-center">
                      <div className="flex flex-col items-center">
                        <Package className="h-12 w-12 text-gray-400 mb-4" />
                        <p className="text-gray-500 dark:text-gray-400">
                          No products found
                        </p>
                        {isOwner && (
                          <button
                            onClick={() => {
                              setSelectedProduct(null);
                              reset();
                              setIsProductModalOpen(true);
                            }}
                            className="mt-4 btn-primary flex items-center space-x-2"
                          >
                            <Plus className="h-4 w-4" />
                            <span>Add Your First Product</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Product Creation/Edit Modal */}
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
                          <label className="label">Retail Price *</label>
                          <input
                            {...register('base_price', { 
                              required: 'Retail price is required',
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
                          <p className="mt-1 text-xs text-gray-500">
                            This will be the selling price for customers
                          </p>
                        </div>

                        <div>
                          <label className="label">Unit</label>
                          <input
                            {...register('unit')}
                            type="text"
                            className="input"
                            placeholder="pcs, kg, liter, etc."
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="label">Initial Stock Quantity</label>
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

        {/* Restock Modal */}
        {isRestockModalOpen && restockProduct && isOwner && (
          <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
              <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
              </div>

              <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full">
                <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                      Restock Product
                    </h3>
                    <button
                      onClick={() => {
                        setIsRestockModalOpen(false);
                        setRestockProduct(null);
                        setRestockQuantity(0);
                      }}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {restockProduct.name}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        SKU: {restockProduct.sku}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Current Stock: {restockProduct.stock_quantity}
                      </p>
                    </div>

                    <div>
                      <label className="label">Quantity to Add *</label>
                      <input
                        type="number"
                        min="1"
                        value={restockQuantity}
                        onChange={(e) => setRestockQuantity(Number(e.target.value))}
                        className="input"
                        placeholder="Enter quantity to add"
                        autoFocus
                      />
                    </div>

                    {restockQuantity > 0 && (
                      <div className="text-center p-2 bg-gray-50 dark:bg-gray-700 rounded">
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          New Stock Level: {restockProduct.stock_quantity + restockQuantity}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    onClick={handleRestock}
                    disabled={isSubmitting || restockQuantity <= 0}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Restock
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setIsRestockModalOpen(false);
                      setRestockProduct(null);
                      setRestockQuantity(0);
                    }}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm dark:bg-gray-600 dark:text-gray-200 dark:border-gray-500 dark:hover:bg-gray-700"
                  >
                    Cancel
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
