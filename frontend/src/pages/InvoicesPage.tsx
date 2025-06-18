import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingCard } from '../components/LoadingSpinner';
import { FileText, Plus, Eye, Filter, Search, Download } from 'lucide-react';
import { invoiceService } from '../services/apiServices';
import { Invoice } from '../types';
import { INVOICE_STATUS } from '../config/constants';
import { format } from 'date-fns';
import { formatCurrency } from '../utils/currency';
import { getCardAmountClass, getTableAmountClass } from '../utils/responsiveFonts';
import toast from 'react-hot-toast';

export const InvoicesPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setIsLoading(true);
      const data = await invoiceService.getInvoices({ ordering: '-created_at' });
      setInvoices(data.results);
    } catch (error) {
      console.error('Error loading invoices:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredInvoices = invoices.filter((invoice) => {
    const matchesFilter = filter === 'all' || invoice.status === filter;
    const matchesSearch = 
      invoice.invoice_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      invoice.shop_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesFilter && matchesSearch;
  });

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
              <div className="flex-shrink-0 p-3 rounded-lg bg-green-500">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Paid Invoices
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {statusCounts.paid || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-lg bg-yellow-500">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Pending
                </p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {statusCounts.pending || 0}
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
                <p className={`${getCardAmountClass(totalAmount)} text-gray-900 dark:text-white`}>
                  {formatCurrency(totalAmount, { useLocaleString: true })}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="card p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search invoices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>

              {/* Status Filter */}
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="input"
              >
                <option value="all">All Statuses</option>
                <option value="draft">Draft ({statusCounts.draft || 0})</option>
                <option value="pending">Pending ({statusCounts.pending || 0})</option>
                <option value="paid">Paid ({statusCounts.paid || 0})</option>
                <option value="partial">Partial ({statusCounts.partial || 0})</option>
                <option value="overdue">Overdue ({statusCounts.overdue || 0})</option>
                <option value="cancelled">Cancelled ({statusCounts.cancelled || 0})</option>
              </select>
            </div>

            <Link to="/invoices/create" className="btn-primary">
              <Plus className="h-4 w-4 mr-2" />
              Create Invoice
            </Link>
          </div>
        </div>

        {/* Invoices Table */}
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Invoice
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Shop
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Amount
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
                {filteredInvoices.length > 0 ? (
                  filteredInvoices.map((invoice) => (
                    <tr key={invoice.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {invoice.invoice_number}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {invoice.items_count} items
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          {invoice.shop_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white">
                          {format(new Date(invoice.invoice_date), 'MMM dd, yyyy')}
                        </div>
                        {invoice.due_date && (
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Due: {format(new Date(invoice.due_date), 'MMM dd, yyyy')}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`${getTableAmountClass(invoice.net_total)} text-gray-900 dark:text-white`}>
                          {formatCurrency(invoice.net_total, { useLocaleString: true })}
                        </div>
                        {invoice.paid_amount > 0 && (
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Paid: {formatCurrency(invoice.paid_amount, { useLocaleString: true })}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                            invoice.status
                          )}`}
                        >
                          {invoice.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <Link
                            to={`/invoices/${invoice.id}`}
                            className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="View Invoice"
                          >
                            <Eye className="h-4 w-4" />
                          </Link>
                          <button
                            onClick={() => handleDownloadPDF(invoice)}
                            className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="Download PDF"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center">
                      <div className="flex flex-col items-center">
                        <FileText className="h-12 w-12 text-gray-400 mb-4" />
                        <p className="text-gray-500 dark:text-gray-400">
                          {searchTerm || filter !== 'all' ? 'No invoices match your criteria' : 'No invoices found'}
                        </p>
                        {(!searchTerm && filter === 'all') && (
                          <Link to="/invoices/create" className="mt-4 btn-primary">
                            <Plus className="h-4 w-4 mr-2" />
                            Create Your First Invoice
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};
