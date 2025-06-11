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
} from 'lucide-react';
import { productService, invoiceService, shopService, analyticsService } from '../services/apiServices';
import { SalesmanStock, Invoice, Shop, MonthlyTrend } from '../types';
import { format } from 'date-fns';
import { formatCurrency } from '../utils/currency';

interface DashboardStats {
  totalProducts: number;
  lowStockProducts: number;
  totalShops: number;
  totalInvoices: number;
  totalSales: number;
  pendingInvoices: number;
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentInvoices, setRecentInvoices] = useState<Invoice[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyTrend[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      // Load dashboard data concurrently
      const [stockData, invoicesData, shopsData, trendsData] = await Promise.all([
        productService.getMySalesmanStock(),
        invoiceService.getInvoices({ ordering: '-created_at', page_size: 5 }),
        shopService.getShops(),
        analyticsService.getMonthlyTrends(),
      ]);

      // Calculate stats
      const totalProducts = stockData.stocks.length;
      const lowStockProducts = stockData.stocks.filter(stock => stock.available_quantity <= 5).length;
      const totalShops = shopsData.results.length;
      const totalInvoices = invoicesData.results.length;
      const pendingInvoices = invoicesData.results.filter(inv => inv.status === 'pending').length;
      const totalSales = invoicesData.results.reduce((sum, inv) => sum + inv.net_total, 0);

      setStats({
        totalProducts,
        lowStockProducts,
        totalShops,
        totalInvoices,
        totalSales,
        pendingInvoices,
      });

      setRecentInvoices(invoicesData.results);
      setMonthlyTrends(trendsData.slice(-6)); // Last 6 months
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="Dashboard">
        <LoadingCard title="Loading dashboard data..." />
      </Layout>
    );
  }

  const statCards = [
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
    {
      name: 'Total Shops',
      value: stats?.totalShops || 0,
      icon: Users,
      color: 'green',
      description: 'Assigned shops',
    },
    {
      name: 'Total Sales',
      value: formatCurrency(stats?.totalSales || 0, { useLocaleString: true }),
      icon: DollarSign,
      color: 'purple',
      description: 'This month',
    },
    {
      name: 'Total Invoices',
      value: stats?.totalInvoices || 0,
      icon: FileText,
      color: 'orange',
      description: 'All time',
    },
    {
      name: 'Pending Invoices',
      value: stats?.pendingInvoices || 0,
      icon: ShoppingCart,
      color: 'yellow',
      description: 'Awaiting payment',
    },
  ];

  const getColorClasses = (color: string) => {
    const colorMap = {
      blue: 'bg-blue-500 text-blue-600 bg-blue-50',
      red: 'bg-red-500 text-red-600 bg-red-50',
      green: 'bg-green-500 text-green-600 bg-green-50',
      purple: 'bg-purple-500 text-purple-600 bg-purple-50',
      orange: 'bg-orange-500 text-orange-600 bg-orange-50',
      yellow: 'bg-yellow-500 text-yellow-600 bg-yellow-50',
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.blue;
  };

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {statCards.map((stat) => {
            const colorClasses = getColorClasses(stat.color).split(' ');
            const iconBg = colorClasses[0];
            const textColor = colorClasses[1];
            const cardBg = colorClasses[2];

            return (
              <div key={stat.name} className="card p-6">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 p-3 rounded-lg ${iconBg}`}>
                    <stat.icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4 flex-1">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                      {stat.name}
                    </p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stat.value}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {stat.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Invoices */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Recent Invoices
            </h3>
            <div className="space-y-3">
              {recentInvoices.length > 0 ? (
                recentInvoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {invoice.invoice_number}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {invoice.shop_name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {format(new Date(invoice.created_at), 'MMM dd, yyyy')}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(invoice.net_total, { useLocaleString: true })}
                      </p>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          invoice.status === 'paid'
                            ? 'bg-green-100 text-green-800'
                            : invoice.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {invoice.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  No recent invoices
                </p>
              )}
            </div>
          </div>

          {/* Monthly Sales Trend */}
          <div className="card p-6">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
              Monthly Sales Trend
            </h3>
            <div className="space-y-3">
              {monthlyTrends.length > 0 ? (
                monthlyTrends.map((trend) => (
                  <div
                    key={trend.month}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {trend.month_name}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {trend.invoice_count} invoices
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {formatCurrency(trend.total_sales, { useLocaleString: true })}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  No sales data available
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
