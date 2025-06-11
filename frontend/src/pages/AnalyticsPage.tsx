import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { analyticsService } from '../services/apiServices';
import { AnalyticsData } from '../types';
import { 
  ChartBarIcon, 
  CurrencyDollarIcon, 
  ShoppingBagIcon, 
  UsersIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon 
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon: Icon, color }) => {
  const isPositive = change ? change > 0 : false;
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{value}</p>
          {change !== undefined && (
            <div className={`flex items-center mt-2 text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}>
              {isPositive ? (
                <ArrowTrendingUpIcon className="w-4 h-4 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="w-4 h-4 mr-1" />
              )}
              <span>{Math.abs(change)}%</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-8 h-8 text-white" />
        </div>
      </div>
    </div>
  );
};

interface SimpleChartProps {
  data: { label: string; value: number }[];
  title: string;
  color: string;
}

const SimpleChart: React.FC<SimpleChartProps> = ({ data, title, color }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index} className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">{item.label}</span>
            <div className="flex items-center space-x-2 flex-1 ml-4">
              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${color}`}
                  style={{ width: `${(item.value / maxValue) * 100}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white min-w-[60px] text-right">
                {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const AnalyticsPage: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('month'); // week, month, quarter, year

  useEffect(() => {
    fetchAnalytics();
  }, [dateRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await analyticsService.getAnalytics({ period: dateRange });
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Analytics & Reports">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  if (!analytics) {
    return (
      <Layout title="Analytics & Reports">
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">No analytics data available</p>
        </div>
      </Layout>
    );
  }

  const salesData = analytics.salesByDay?.map((item: any) => ({
    label: new Date(item.date).toLocaleDateString(),
    value: item.total_sales
  })) || [];

  const productData = analytics.topProducts?.map((item: any) => ({
    label: item.product_name,
    value: item.quantity_sold
  })) || [];

  const revenueData = analytics.revenueByMonth?.map((item: any) => ({
    label: new Date(item.month).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    value: item.revenue
  })) || [];

  return (
    <Layout title="Analytics & Reports">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics & Reports</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Monitor your sales performance and business metrics
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="week">This Week</option>
              <option value="month">This Month</option>
              <option value="quarter">This Quarter</option>
              <option value="year">This Year</option>
            </select>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Sales"
            value={formatCurrency(analytics.totalSales || 0, { useLocaleString: true })}
            change={analytics.salesGrowth}
            icon={CurrencyDollarIcon}
            color="bg-primary-500"
          />
          <StatCard
            title="Total Orders"
            value={analytics.totalOrders || 0}
            change={analytics.ordersGrowth}
            icon={ShoppingBagIcon}
            color="bg-orange-500"
          />
          <StatCard
            title="Active Shops"
            value={analytics.totalShops || 0}
            icon={UsersIcon}
            color="bg-green-500"
          />
          <StatCard
            title="Products Sold"
            value={analytics.totalProductsSold || 0}
            change={analytics.productsGrowth}
            icon={ChartBarIcon}
            color="bg-purple-500"
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {salesData.length > 0 && (
            <SimpleChart
              data={salesData.slice(-7)} // Last 7 days
              title="Daily Sales"
              color="bg-primary-500"
            />
          )}
          
          {productData.length > 0 && (
            <SimpleChart
              data={productData.slice(0, 5)} // Top 5 products
              title="Top Products"
              color="bg-orange-500"
            />
          )}
        </div>

        {/* Revenue Chart */}
        {revenueData.length > 0 && (
          <div className="grid grid-cols-1">
            <SimpleChart
              data={revenueData}
              title="Monthly Revenue"
              color="bg-green-500"
            />
          </div>
        )}

        {/* Additional Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Average Order Value
            </h3>
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">
              {formatCurrency(analytics.averageOrderValue || 0)}
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Total Profit Margin
            </h3>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
              {analytics.totalProfitMargin?.toFixed(1) || '0.0'}%
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Pending Payments
            </h3>
            <p className="text-3xl font-bold text-orange-600 dark:text-orange-400">
              {formatCurrency(analytics.pendingPayments || 0, { useLocaleString: true })}
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};
