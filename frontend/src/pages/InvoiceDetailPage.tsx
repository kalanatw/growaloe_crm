import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { invoiceService } from '../services/apiServices';
import { Invoice, InvoiceItem } from '../types';
import { INVOICE_STATUS, PAYMENT_METHODS } from '../config/constants';
import { 
  ArrowLeftIcon, 
  PrinterIcon, 
  DocumentArrowDownIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { formatCurrency } from '../utils/currency';

const getStatusIcon = (status: string) => {
  switch (status) {
    case INVOICE_STATUS.PAID:
      return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
    case INVOICE_STATUS.PENDING:
      return <ClockIcon className="w-5 h-5 text-yellow-500" />;
    case INVOICE_STATUS.CANCELLED:
      return <XCircleIcon className="w-5 h-5 text-red-500" />;
    default:
      return <InformationCircleIcon className="w-5 h-5 text-gray-500" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case INVOICE_STATUS.PAID:
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case INVOICE_STATUS.PENDING:
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case INVOICE_STATUS.CANCELLED:
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

export const InvoiceDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchInvoice(id);
    }
  }, [id]);

  const fetchInvoice = async (invoiceId: string) => {
    try {
      setLoading(true);
      const data = await invoiceService.getInvoice(parseInt(invoiceId));
      setInvoice(data);
    } catch (error) {
      console.error('Error fetching invoice:', error);
      toast.error('Failed to load invoice');
      navigate('/invoices');
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = async () => {
    if (!invoice) return;
    
    try {
      toast.loading('Generating PDF...', { id: 'pdf-generation' });
      await invoiceService.generateInvoicePDF(invoice.id);
      toast.success('PDF downloaded successfully!', { id: 'pdf-generation' });
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF', { id: 'pdf-generation' });
    }
  };

  const handleUpdateStatus = async (status: string) => {
    if (!invoice) return;
    
    try {
      const updatedInvoice = await invoiceService.updateInvoice(invoice.id, { status });
      setInvoice(updatedInvoice);
      toast.success('Invoice status updated successfully');
    } catch (error) {
      console.error('Error updating invoice status:', error);
      toast.error('Failed to update invoice status');
    }
  };

  if (loading) {
    return (
      <Layout title="Invoice Details">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      </Layout>
    );
  }

  if (!invoice) {
    return (
      <Layout title="Invoice Details">
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Invoice not found</p>
        </div>
      </Layout>
    );
  }

  const subtotal = invoice.items?.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0) || 0;
  const taxAmount = invoice.tax_amount || 0;
  const discountAmount = invoice.discount_amount || 0;
  const total = invoice.total_amount;

  return (
    <Layout title={`Invoice #${invoice.invoice_number}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/invoices')}
              className="p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              <ArrowLeftIcon className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Invoice #{invoice.invoice_number}
              </h1>
              <div className="flex items-center mt-2 space-x-2">
                {getStatusIcon(invoice.status)}
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>
                  {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex space-x-2 mt-4 sm:mt-0">
            <button
              onClick={handlePrint}
              className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <PrinterIcon className="w-4 h-4 mr-2" />
              Print
            </button>
            <button
              onClick={handleDownloadPDF}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700"
            >
              <DocumentArrowDownIcon className="w-4 h-4 mr-2" />
              Download PDF
            </button>
          </div>
        </div>

        {/* Invoice Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
          <div className="p-6 print:p-0">
            {/* Invoice Header */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">From:</h2>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p className="font-medium text-gray-900 dark:text-white">{invoice.salesman_name}</p>
                  <p>Salesman ID: {invoice.salesman}</p>
                </div>
              </div>
              
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">To:</h2>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p className="font-medium text-gray-900 dark:text-white">{invoice.shop_name}</p>
                  <p>Shop ID: {invoice.shop}</p>
                </div>
              </div>
            </div>

            {/* Invoice Details */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Invoice Number</p>
                <p className="text-sm text-gray-900 dark:text-white">{invoice.invoice_number}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Date Issued</p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {new Date(invoice.date_created || invoice.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Due Date</p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>

            {/* Invoice Items */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Items</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Unit Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {invoice.items?.map((item: InvoiceItem, index: number) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {typeof item.product === 'object' ? item.product.name : item.product_name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {typeof item.product === 'object' ? item.product.sku : item.product_sku}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {item.quantity}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {formatCurrency(item.unit_price)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {formatCurrency(item.quantity * item.unit_price)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Invoice Totals */}
            <div className="flex justify-end">
              <div className="w-full max-w-sm">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Subtotal:</span>
                    <span className="text-gray-900 dark:text-white">{formatCurrency(subtotal)}</span>
                  </div>
                  {discountAmount && discountAmount > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Discount:</span>
                      <span className="text-gray-900 dark:text-white">-{formatCurrency(discountAmount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Tax:</span>
                    <span className="text-gray-900 dark:text-white">{formatCurrency(taxAmount)}</span>
                  </div>
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                    <div className="flex justify-between font-semibold">
                      <span className="text-gray-900 dark:text-white">Total:</span>
                      <span className="text-gray-900 dark:text-white">{formatCurrency(total)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Information */}
            {invoice.payment_method && (
              <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Payment Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Payment Method</p>
                    <p className="text-sm text-gray-900 dark:text-white">{invoice.payment_method}</p>
                  </div>
                  {invoice.payment_date && (
                    <div>
                      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Payment Date</p>
                      <p className="text-sm text-gray-900 dark:text-white">
                        {new Date(invoice.payment_date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Notes */}
            {invoice.notes && (
              <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notes</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">{invoice.notes}</p>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {invoice.status === INVOICE_STATUS.PENDING && (
          <div className="flex space-x-4">
            <button
              onClick={() => handleUpdateStatus(INVOICE_STATUS.PAID)}
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 font-medium"
            >
              Mark as Paid
            </button>
            <button
              onClick={() => handleUpdateStatus(INVOICE_STATUS.CANCELLED)}
              className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 font-medium"
            >
              Cancel Invoice
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};
