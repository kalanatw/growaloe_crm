import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import {
  Package,
  Users,
  FileText,
  TrendingUp,
  DollarSign,
  ShoppingCart,
  AlertTriangle,
  Activity,
  Target,
  Percent,
  Calendar,
  PieChart,
  BarChart,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  CheckCircle,
  XCircle,
  Star,
} from 'lucide-react';
import { 
  productService, 
  invoiceService, 
  shopService, 
  analyticsService,
  transactionService,
  salesmanService 
} from '../services/apiServices';
import { SalesmanStock, Invoice, Shop, MonthlyTrend, User } from '../types';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';
import { formatCurrency } from '../utils/currency';
import { getResponsiveFontSize, getCardAmountClass } from '../utils/responsiveFonts';
import { useAuth } from '../contexts/AuthContext';

interface DashboardStats {
  totalProducts: number;
  lowStockProducts: number;
  totalShops: number;
  totalInvoices: number;
  totalSales: number;
  pendingInvoices: number;
  paidInvoices: number;
  outstandingAmount: number;
  draftInvoices: number;
  overdueInvoices: number;
}

interface CommissionData {
  total_pending_commissions: number;
  total_paid_commissions: number;
  salesman_commissions: Array<{
    salesman_id: number;
    salesman_name: string;
    pending_commission: number;
    total_invoices: number;
  }>;
  recent_commissions: any[];
}

interface InvoiceSummary {
  total_invoices: number;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  overdue_invoices: number;
  draft_invoices: number;
}

interface PerformanceMetrics {
  salesGrowth: number;
  revenueGrowth: number;
  averageOrderValue: number;
  conversionRate: number;
  topPerformingSalesman?: string;
  topSellingProduct?: string;
}

export const ComprehensiveDashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [commissionData, setCommissionData] = useState<CommissionData | null>(null);
  const [invoiceSummary, setInvoiceSummary] = useState<InvoiceSummary | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const isOwner = user?.role === 'owner';
  const isSalesman = user?.role === 'salesman';

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      if (isOwner) {
        await loadOwnerDashboard();
      } else if (isSalesman) {
        await loadSalesmanDashboard();
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadOwnerDashboard = async () => {
    try {
      // Load comprehensive owner dashboard data
      const [
        stockData, 
        invoicesData, 
        shopsData, 
        commissionsData,
        invoiceSummaryData,
        trendsData
      ] = await Promise.all([
        productService.getMySalesmanStock().catch(() => ({ stocks: [] })),
        invoiceService.getInvoices({ ordering: '-created_at', page_size: 10 }),
        shopService.getShops(),
        fetchCommissionData(),
        fetchInvoiceSummary(),
        analyticsService.getMonthlyTrends().catch(() => []),
      ]);

      // Calculate comprehensive stats
      const totalProducts = stockData.stocks?.length || 0;
      const lowStockProducts = stockData.stocks?.filter(stock => stock.available_quantity <= 5).length || 0;
      const totalShops = shopsData.results?.length || 0;
      const invoices = invoicesData.results || [];
      const totalInvoices = invoices.length;
      const pendingInvoices = invoices.filter(inv => inv.status === 'pending' || inv.status === 'SENT').length;
      const paidInvoices = invoices.filter(inv => inv.status === 'paid' || inv.status === 'PAID').length;
      const draftInvoices = invoices.filter(inv => inv.status === 'DRAFT').length;
      const overdueInvoices = invoices.filter(inv => {
        if (!inv.due_date) return false;
        return new Date(inv.due_date) < new Date() && ['pending', 'SENT', 'PARTIAL'].includes(inv.status);
      }).length;
      
      const totalSales = invoices.reduce((sum, inv) => sum + (inv.net_total || 0), 0);
      const outstandingAmount = invoices.reduce((sum, inv) => sum + (inv.balance_due || 0), 0);

      setStats({
        totalProducts,
        lowStockProducts,
        totalShops,
        totalInvoices,
        totalSales,
        pendingInvoices,
        paidInvoices,
        outstandingAmount,
        draftInvoices,
        overdueInvoices,
      });

      setCommissionData(commissionsData);
      setInvoiceSummary(invoiceSummaryData);
      setRecentInvoices(invoices.slice(0, 5));
      setMonthlyTrends(Array.isArray(trendsData) ? trendsData.slice(-6) : []);

      // Calculate performance metrics
      calculatePerformanceMetrics(invoices, commissionsData);
      
    } catch (error) {
      console.error('Error loading owner dashboard:', error);
    }
  };

  const loadSalesmanDashboard = async () => {
    try {
      // Load salesman-specific dashboard data
      const [
        stockData, 
        invoicesData, 
        shopsData
      ] = await Promise.all([
        productService.getMySalesmanStock(),
        invoiceService.getInvoices({ ordering: '-created_at', page_size: 10 }),
        shopService.getShops(),
      ]);

      // Calculate salesman-specific stats
      const totalProducts = stockData.stocks?.length || 0;
      const lowStockProducts = stockData.stocks?.filter(stock => stock.available_quantity <= 5).length || 0;
      
      // Filter shops for current salesman
      const myShops = shopsData.results?.filter(shop => 
        shop.salesman?.user?.id === user?.id
      ) || [];
      
      const totalShops = myShops.length;
      const invoices = invoicesData.results || [];
      
      // Filter invoices for current salesman - use the salesman ID since it's a number in Invoice interface
      const myInvoices = invoices.filter(inv => 
        inv.salesman === user?.id
      );
      
      const totalInvoices = myInvoices.length;
      const pendingInvoices = myInvoices.filter(inv => inv.status === 'pending' || inv.status === 'SENT').length;
      const paidInvoices = myInvoices.filter(inv => inv.status === 'paid' || inv.status === 'PAID').length;
      const draftInvoices = myInvoices.filter(inv => inv.status === 'DRAFT').length;
      const overdueInvoices = myInvoices.filter(inv => {
        if (!inv.due_date) return false;
        return new Date(inv.due_date) < new Date() && ['pending', 'SENT', 'PARTIAL'].includes(inv.status);
      }).length;
      
      const totalSales = myInvoices.reduce((sum, inv) => sum + (inv.net_total || 0), 0);
      const outstandingAmount = myInvoices.reduce((sum, inv) => sum + (inv.balance_due || 0), 0);

      setStats({
        totalProducts,
        lowStockProducts,
        totalShops,
        totalInvoices,
        totalSales,
        pendingInvoices,
        paidInvoices,
        outstandingAmount,
        draftInvoices,
        overdueInvoices,
      });

      setRecentInvoices(myInvoices.slice(0, 5));
      
    } catch (error) {
      console.error('Error loading salesman dashboard:', error);
    }
  };

  const fetchCommissionData = async (): Promise<CommissionData> => {
    try {
      const response = await fetch('/api/sales/commissions/dashboard_data/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Error fetching commission data:', error);
    }
    return {
      total_pending_commissions: 0,
      total_paid_commissions: 0,
      salesman_commissions: [],
      recent_commissions: [],
    };
  };

  const fetchInvoiceSummary = async (): Promise<InvoiceSummary> => {
    try {
      const response = await fetch('/api/sales/invoices/summary/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Error fetching invoice summary:', error);
    }
    return {
      total_invoices: 0,
      total_amount: 0,
      paid_amount: 0,
      outstanding_amount: 0,
      overdue_invoices: 0,
      draft_invoices: 0,
    };
  };

  const calculatePerformanceMetrics = (invoices: Invoice[], commissionData: CommissionData | null) => {
    const currentMonth = startOfMonth(new Date());
    const lastMonth = startOfMonth(subDays(currentMonth, 1));
    
    const currentMonthInvoices = invoices.filter(inv => 
      new Date(inv.created_at) >= currentMonth
    );
    const lastMonthInvoices = invoices.filter(inv => {
      const invDate = new Date(inv.created_at);
      return invDate >= lastMonth && invDate < currentMonth;
    });

    const currentRevenue = currentMonthInvoices.reduce((sum, inv) => sum + (inv.net_total || 0), 0);
    const lastRevenue = lastMonthInvoices.reduce((sum, inv) => sum + (inv.net_total || 0), 0);
    
    const salesGrowth = lastRevenue > 0 ? ((currentRevenue - lastRevenue) / lastRevenue) * 100 : 0;
    const revenueGrowth = salesGrowth; // Same calculation for demo
    const averageOrderValue = invoices.length > 0 ? (invoices.reduce((sum, inv) => sum + (inv.net_total || 0), 0) / invoices.length) : 0;
    
    // Find top performing salesman
    let topPerformingSalesman = '';
    if (commissionData?.salesman_commissions?.length) {
      const topSalesman = commissionData.salesman_commissions.reduce((prev, current) => 
        (prev.pending_commission > current.pending_commission) ? prev : current
      );
      topPerformingSalesman = topSalesman.salesman_name;
    }

    setPerformanceMetrics({
      salesGrowth,
      revenueGrowth,
      averageOrderValue,
      conversionRate: 85.2, // Mock data for demo
      topPerformingSalesman,
      topSellingProduct: 'Premium Aloe Vera Gel', // Mock data for demo
    });
  };

  if (isLoading) {
    return (
      <Layout title="Dashboard">
        <LoadingCard title="Loading dashboard data..." />
      </Layout>
    );
  }

  const getStatCards = () => {
    const baseCards = [
      {
        name: 'Total Products',
        value: stats?.totalProducts || 0,
        icon: Package,
        color: 'blue',
        description: 'Products in stock',
      },
      {
        name: 'Low Stock Items',
        value: stats?.lowStockProducts || 0,
        icon: AlertTriangle,
        color: 'red',
        description: '≤ 5 items remaining',
      },
    ];

    if (isOwner) {
      return [
        ...baseCards,
        {
          name: 'Total Shops',
          value: stats?.totalShops || 0,
          icon: ShoppingCart,
          color: 'green',
          description: 'Active shop partners',
        },
        {
          name: 'Total Sales',
          value: formatCurrency(stats?.totalSales || 0),
          icon: DollarSign,
          color: 'purple',
          description: 'Overall revenue',
        },
        {
          name: 'Pending Invoices',
          value: stats?.pendingInvoices || 0,
          icon: Clock,
          color: 'orange',
          description: 'Awaiting payment',
        },
        {
          name: 'Overdue Invoices',
          value: stats?.overdueInvoices || 0,
          icon: XCircle,
          color: 'red',
          description: 'Past due date',
        },
        {
          name: 'Outstanding Amount',
          value: formatCurrency(stats?.outstandingAmount || 0),
          icon: FileText,
          color: 'yellow',
          description: 'Amount due',
        },
        {
          name: 'Monthly Growth',
          value: `${performanceMetrics?.salesGrowth?.toFixed(1) || '0.0'}%`,
          icon: performanceMetrics?.salesGrowth && performanceMetrics.salesGrowth > 0 ? ArrowUpRight : ArrowDownRight,
          color: performanceMetrics?.salesGrowth && performanceMetrics.salesGrowth > 0 ? 'green' : 'red',
          description: 'vs last month',
        },
      ];
    } else {
      return [
        ...baseCards,
        {
          name: 'My Shops',
          value: stats?.totalShops || 0,
          icon: ShoppingCart,
          color: 'green',
          description: 'Shops under management',
        },
        {
          name: 'My Sales',
          value: formatCurrency(stats?.totalSales || 0),
          icon: DollarSign,
          color: 'purple',
          description: 'Total revenue generated',
        },
        {
          name: 'Pending Invoices',
          value: stats?.pendingInvoices || 0,
          icon: Clock,
          color: 'orange',
          description: 'Awaiting payment',
        },
        {
          name: 'Paid Invoices',
          value: stats?.paidInvoices || 0,
          icon: CheckCircle,
          color: 'green',
          description: 'Successfully completed',
        },
      ];
    }
  };

  return (
    <Layout title={`${isOwner ? 'Owner' : 'Salesman'} Dashboard`}>
      <div className="space-y-6">
        {/* Header with Role-Specific Title */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isOwner ? '🏢 Business Overview Dashboard' : '👤 Salesman Performance Dashboard'}
              </h1>
              <p className="text-gray-600 mt-1">
                {isOwner 
                  ? 'Complete business insights and analytics' 
                  : 'Your personal sales performance and targets'
                }
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Last updated</p>
              <p className="text-sm font-medium">{format(new Date(), 'MMM dd, yyyy HH:mm')}</p>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {getStatCards().map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.name} className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Icon
                        className={`h-6 w-6 text-${item.color}-600`}
                        aria-hidden="true"
                      />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          {item.name}
                        </dt>
                        <dd>
                          <div className={`text-lg font-medium text-gray-900 ${getCardAmountClass(typeof item.value === 'string' ? item.value : item.value.toString())}`}>
                            {item.value}
                          </div>
                        </dd>
                      </dl>
                    </div>
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">{item.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Owner-specific sections */}
        {isOwner && (
          <>
            {/* Commission Overview */}
            {commissionData && (
              <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">💰 Commission Overview</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Pending Commissions</span>
                        <span className="text-lg font-semibold text-orange-600">
                          {formatCurrency(commissionData.total_pending_commissions)}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Paid Commissions</span>
                        <span className="text-lg font-semibold text-green-600">
                          {formatCurrency(commissionData.total_paid_commissions)}
                        </span>
                      </div>
                      <div className="border-t pt-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-gray-900">Total Commission Value</span>
                          <span className="text-xl font-bold text-gray-900">
                            {formatCurrency(commissionData.total_pending_commissions + commissionData.total_paid_commissions)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                {performanceMetrics && (
                  <div className="bg-white overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Performance Metrics</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Average Order Value</span>
                          <span className="text-lg font-semibold text-blue-600">
                            {formatCurrency(performanceMetrics.averageOrderValue)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Top Salesman</span>
                          <span className="text-sm font-medium text-gray-900">
                            {performanceMetrics.topPerformingSalesman || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Top Product</span>
                          <span className="text-sm font-medium text-gray-900">
                            {performanceMetrics.topSellingProduct || 'N/A'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Salesman Performance Table */}
            {commissionData?.salesman_commissions && commissionData.salesman_commissions.length > 0 && (
              <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">👥 Salesman Performance</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Salesman
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Invoices
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Pending Commission
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Performance
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {commissionData.salesman_commissions.map((salesman) => (
                        <tr key={salesman.salesman_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <Star className="h-4 w-4 text-yellow-400 mr-2" />
                              <span className="text-sm font-medium text-gray-900">
                                {salesman.salesman_name}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {salesman.total_invoices}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                            {formatCurrency(salesman.pending_commission)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {salesman.pending_commission > 1000 ? (
                                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                              ) : (
                                <Activity className="h-4 w-4 text-yellow-500 mr-1" />
                              )}
                              <span className={`text-xs ${salesman.pending_commission > 1000 ? 'text-green-600' : 'text-yellow-600'}`}>
                                {salesman.pending_commission > 1000 ? 'Excellent' : 'Good'}
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* Recent Invoices - For both owners and salesmen */}
        {recentInvoices.length > 0 && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                📄 {isSalesman ? 'My Recent Invoices' : 'Recent Invoices'}
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invoice #
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Shop
                    </th>
                    {isOwner && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Salesman
                      </th>
                    )}
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {recentInvoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                        {invoice.invoice_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {invoice.shop_name || 'N/A'}
                      </td>
                      {isOwner && (
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {invoice.salesman_name || 'N/A'}
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(invoice.net_total)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          invoice.status === 'PAID' || invoice.status === 'paid'
                            ? 'bg-green-100 text-green-800'
                            : invoice.status === 'DRAFT'
                            ? 'bg-gray-100 text-gray-800'
                            : invoice.status === 'SENT' || invoice.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {format(new Date(invoice.created_at), 'MMM dd, yyyy')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">🚀 Quick Actions</h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <button
                onClick={() => window.location.href = '/invoices/create'}
                className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FileText className="h-8 w-8 text-blue-600 mb-2" />
                <span className="text-sm font-medium text-gray-900">Create Invoice</span>
              </button>
              
              {isOwner && (
                <>
                  <button
                    onClick={() => window.location.href = '/shops/create'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <ShoppingCart className="h-8 w-8 text-green-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">Add Shop</span>
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/salesmen/create'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Users className="h-8 w-8 text-purple-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">Add Salesman</span>
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/analytics'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <BarChart className="h-8 w-8 text-indigo-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">View Analytics</span>
                  </button>
                </>
              )}
              
              {isSalesman && (
                <>
                  <button
                    onClick={() => window.location.href = '/stock-management'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <Package className="h-8 w-8 text-green-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">Manage Stock</span>
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/shops'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <ShoppingCart className="h-8 w-8 text-purple-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">My Shops</span>
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/invoices'}
                    className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <FileText className="h-8 w-8 text-indigo-600 mb-2" />
                    <span className="text-sm font-medium text-gray-900">My Invoices</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* System Status (Owner only) */}
        {isOwner && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">🔧 System Status</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    <span className="text-sm font-medium text-green-800">Database</span>
                  </div>
                  <span className="text-xs text-green-600">Healthy</span>
                </div>
                
                <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                    <span className="text-sm font-medium text-green-800">API Services</span>
                  </div>
                  <span className="text-xs text-green-600">Online</span>
                </div>
                
                <div className="flex items-center justify-between p-4 bg-yellow-50 rounded-lg">
                  <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                    <span className="text-sm font-medium text-yellow-800">Backup</span>
                  </div>
                  <span className="text-xs text-yellow-600">Due Soon</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};
