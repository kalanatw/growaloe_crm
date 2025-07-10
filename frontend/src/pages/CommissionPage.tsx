import React, { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

interface SalesmanCommissionSummary {
  salesman_id: number;
  salesman_name: string;
  pending_commission: string;
  total_invoices: number;
}

interface Commission {
  id: number;
  invoice_number: string;
  salesman_name: string;
  shop_name: string;
  commission_rate: string;
  commission_amount: string;
  status: string;
  paid_date?: string;
  payment_reference?: string;
}

interface DashboardData {
  total_pending_commissions: string;
  total_paid_commissions: string;
  salesman_commissions: SalesmanCommissionSummary[];
  recent_commissions: Commission[];
}

export const CommissionPage: React.FC = () => {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [settling, setSettling] = useState<number | null>(null);
  const [recentLoading, setRecentLoading] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get<DashboardData>('/sales/commissions/dashboard_data/');
      setDashboard(res);
    } catch (e) {
      toast.error('Failed to load commission dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleSettleSalesman = async (salesmanId: number) => {
    setSettling(salesmanId);
    try {
      // Get all pending commissions for this salesman
      const res = await apiClient.get<{ results: Commission[] }>('/sales/commissions/', { status: 'pending', salesman: salesmanId });
      const ids = res.results.map(c => c.id);
      if (!ids.length) {
        toast('No pending commissions');
        setSettling(null);
        return;
      }
      await apiClient.post('/sales/commissions/bulk_mark_paid/', {
        commission_ids: ids,
        payment_reference: '',
      });
      toast.success('Settled all pending commissions for salesman');
      fetchDashboard();
    } catch (e) {
      toast.error('Failed to settle commissions');
    } finally {
      setSettling(null);
    }
  };

  return (
    <Layout title="Commissions">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Commissions</h1>
            <p className="text-gray-600 dark:text-gray-400">Settle commissions by salesman</p>
          </div>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <LoadingSpinner />
          </div>
        ) : dashboard ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {dashboard.salesman_commissions.map((s) => (
                <div key={s.salesman_id} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 flex flex-col gap-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{s.salesman_name}</h2>
                      <p className="text-gray-500 dark:text-gray-400 text-sm">Total Invoices: {s.total_invoices}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-primary-600 dark:text-primary-400">{s.pending_commission}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">Pending</div>
                    </div>
                  </div>
                  <button
                    className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                    onClick={() => handleSettleSalesman(s.salesman_id)}
                    disabled={settling === s.salesman_id || s.pending_commission === '0.00'}
                  >
                    {settling === s.salesman_id ? 'Settling...' : 'Settle All Pending'}
                  </button>
                </div>
              ))}
            </div>
            <div className="mt-10">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Commissions</h3>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-4 py-2">Invoice</th>
                      <th className="px-4 py-2">Salesman</th>
                      <th className="px-4 py-2">Shop</th>
                      <th className="px-4 py-2">Rate</th>
                      <th className="px-4 py-2">Amount</th>
                      <th className="px-4 py-2">Status</th>
                      <th className="px-4 py-2">Paid Date</th>
                      <th className="px-4 py-2">Reference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dashboard.recent_commissions.map((c) => (
                      <tr key={c.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-4 py-2">{c.invoice_number}</td>
                        <td className="px-4 py-2">{c.salesman_name}</td>
                        <td className="px-4 py-2">{c.shop_name}</td>
                        <td className="px-4 py-2">{c.commission_rate}</td>
                        <td className="px-4 py-2">{c.commission_amount}</td>
                        <td className="px-4 py-2 capitalize">{c.status}</td>
                        <td className="px-4 py-2">{c.paid_date ? new Date(c.paid_date).toLocaleString() : '-'}</td>
                        <td className="px-4 py-2">{c.payment_reference || '-'}</td>
                      </tr>
                    ))}
                    {!dashboard.recent_commissions.length && (
                      <tr>
                        <td colSpan={8} className="text-center py-8 text-gray-500 dark:text-gray-400">
                          No recent commissions found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">No commission data available</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default CommissionPage;