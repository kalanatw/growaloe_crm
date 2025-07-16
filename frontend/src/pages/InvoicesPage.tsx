import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { FileText, Plus, Eye, Filter, Search, Download } from 'lucide-react';
import { invoiceService } from '../services/apiServices';
import { shopService } from '../services/apiServices';
import { Invoice } from '../types';
import { INVOICE_STATUS } from '../config/constants';
import { format } from 'date-fns';
import { formatCurrency } from '../utils/currency';
import { getCardAmountClass, getTableAmountClass } from '../utils/responsiveFonts';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export const InvoicesPage: React.FC = () => {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [shops, setShops] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedShopId, setExpandedShopId] = useState<number | null>(null);

  useEffect(() => {
    loadInvoicesAndShops();
  }, []);

  const loadInvoicesAndShops = async () => {
    try {
      setIsLoading(true);
      const [invoiceData, shopData] = await Promise.all([
        invoiceService.getInvoices({ ordering: '-created_at' }),
        shopService.getShops(),
      ]);
      setInvoices(invoiceData.results);
      setShops(shopData.results);
    } catch (error) {
      console.error('Error loading invoices or shops:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Group invoices by shop
  const shopInvoiceMap: { [shopId: number]: Invoice[] } = {};
  invoices.forEach((inv) => {
    if (!shopInvoiceMap[inv.shop]) shopInvoiceMap[inv.shop] = [];
    shopInvoiceMap[inv.shop].push(inv);
  });

  // Filtering/search logic
  const filteredShops = shops.filter((shop) =>
    shop.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Shop summary helpers
  const getShopSummary = (shopId: number) => {
    const shopInvoices = shopInvoiceMap[shopId] || [];
    const totalAmount = shopInvoices.reduce((sum, inv) => sum + inv.net_total, 0);
    const outstanding = shopInvoices.reduce((sum, inv) => sum + (inv.balance_due || 0), 0);
    return {
      count: shopInvoices.length,
      totalAmount,
      outstanding,
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'overdue':
        return 'bg-red-100 text-red-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'partial':
        return 'bg-blue-100 text-blue-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const statusCounts = invoices.reduce((acc, invoice) => {
    acc[invoice.status] = (acc[invoice.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const totalAmount = invoices.reduce((sum, invoice) => sum + invoice.net_total, 0);
  const paidAmount = invoices
    .filter(inv => inv.status === 'paid')
    .reduce((sum, invoice) => sum + invoice.net_total, 0);

  const handleDownloadPDF = async (invoice: Invoice) => {
    try {
      toast.loading('Generating PDF...', { id: `pdf-${invoice.id}` });
      await invoiceService.generateInvoicePDF(invoice.id);
      toast.success('PDF downloaded successfully!', { id: `pdf-${invoice.id}` });
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF', { id: `pdf-${invoice.id}` });
    }
  };

  if (isLoading) {
    return (
      <Layout title="Invoices">
        <LoadingCard title="Loading invoices..." />
      </Layout>
    );
  }

  return (
    <Layout title="Invoices">
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-blue-500">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Invoices
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {invoices.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-purple-500">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Value
                </p>
                <p className={`${getCardAmountClass(invoices.reduce((sum, inv) => sum + inv.net_total, 0))} text-gray-900 dark:text-white`}>
                  {formatCurrency(invoices.reduce((sum, inv) => sum + inv.net_total, 0), { useLocaleString: true })}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Search */}
        <div className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search shops..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
            <Link to="/invoices/create" className="btn-primary">
              <Plus className="h-4 w-4 mr-2" />
              Create Invoice
            </Link>
          </div>
        </div>

        {/* Shop-centric Accordion/Table */}
        <div className="space-y-4">
          {filteredShops.length === 0 && (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">No shops found.</div>
          )}
          {filteredShops.map((shop) => {
            const summary = getShopSummary(shop.id);
            const shopInvoices = shopInvoiceMap[shop.id] || [];
            return (
              <div key={shop.id} className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
                <div
                  className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
                  onClick={() => setExpandedShopId(expandedShopId === shop.id ? null : shop.id)}
                >
                  <div>
                    <div className="font-bold text-lg text-gray-900 dark:text-white">{shop.name}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{summary.count} invoices | Total: {formatCurrency(summary.totalAmount)} | Outstanding: {formatCurrency(summary.outstanding)}</div>
                  </div>
                  <button className="text-primary-600 font-medium">
                    {expandedShopId === shop.id ? 'Hide' : 'View'}
                  </button>
                </div>
                {expandedShopId === shop.id && (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-900">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Invoice</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Amount</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Paid</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Outstanding</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {shopInvoices.length === 0 ? (
                          <tr><td colSpan={7} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">No invoices for this shop.</td></tr>
                        ) : (
                          shopInvoices.map((invoice) => (
                            <tr key={invoice.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900 dark:text-white">{invoice.invoice_number}</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">{invoice.items_count} items</div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                {format(new Date(invoice.invoice_date), 'MMM dd, yyyy')}
                                {invoice.due_date && (
                                  <div className="text-xs text-gray-500 dark:text-gray-400">Due: {format(new Date(invoice.due_date), 'MMM dd, yyyy')}</div>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{formatCurrency(invoice.net_total)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{formatCurrency(invoice.paid_amount)}</td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-red-600">{formatCurrency(invoice.balance_due)}</td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>{invoice.status}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                <div className="flex items-center space-x-2">
                                  <Link to={`/invoices/${invoice.id}`} className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title="View Invoice">
                                    <Eye className="h-4 w-4" />
                                  </Link>
                                  <button onClick={() => handleDownloadPDF(invoice)} className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700" title="Download PDF">
                                    <Download className="h-4 w-4" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Layout>
  );
};
