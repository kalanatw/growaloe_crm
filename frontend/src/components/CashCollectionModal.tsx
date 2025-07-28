import React, { useState } from 'react';
import { X, DollarSign, Receipt, CheckCircle } from 'lucide-react';
import { cashFlowService } from '../services/apiServices';
import toast from 'react-hot-toast';

interface CashCollectionModalProps {
  invoice: {
    id: number;
    invoice_number: string;
    shop_name: string;
    net_total: number;
    paid_amount: number;
    balance_due: number;
    salesman_name?: string;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const CashCollectionModal: React.FC<CashCollectionModalProps> = ({
  invoice,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [amount, setAmount] = useState(0);
  const [notes, setNotes] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleRecord = async () => {
    if (amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (amount > invoice.balance_due) {
      toast.error('Amount cannot exceed balance due');
      return;
    }

    try {
      setIsRecording(true);
      await cashFlowService.recordCashCollection({
        invoice_id: invoice.id,
        amount: amount,
        notes: notes || `Cash collection for invoice ${invoice.invoice_number}`
      });
      
      toast.success(`Cash collection recorded: LKR ${amount.toFixed(2)}`);
      
      // Reset form
      setAmount(0);
      setNotes('');
      
      // Call success callback
      if (onSuccess) {
        onSuccess();
      }
      
      onClose();
    } catch (error: any) {
      console.error('Error recording cash collection:', error);
      toast.error(error.response?.data?.error || 'Failed to record cash collection');
    } finally {
      setIsRecording(false);
    }
  };

  const handleClose = () => {
    setAmount(0);
    setNotes('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Receipt className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Record Cash Collection
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Invoice Details */}
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Invoice:</span>
                <span className="font-medium text-gray-900 dark:text-white">{invoice.invoice_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Shop:</span>
                <span className="font-medium text-gray-900 dark:text-white">{invoice.shop_name}</span>
              </div>
              {invoice.salesman_name && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Salesman:</span>
                  <span className="font-medium text-gray-900 dark:text-white">{invoice.salesman_name}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Total Amount:</span>
                <span className="font-medium text-gray-900 dark:text-white">LKR {invoice.net_total.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Already Paid:</span>
                <span className="font-medium text-green-600">LKR {invoice.paid_amount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-gray-200 dark:border-gray-600 pt-2">
                <span className="text-gray-600 dark:text-gray-400">Balance Due:</span>
                <span className="font-bold text-red-600">LKR {invoice.balance_due.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Collection Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Collection Amount
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                max={invoice.balance_due}
                className="w-full px-3 py-2 pl-8 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="0.00"
              />
              <DollarSign className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Maximum: LKR {invoice.balance_due.toFixed(2)}
            </p>
            {amount > invoice.balance_due && (
              <p className="text-xs text-red-600 mt-1">
                Amount exceeds balance due
              </p>
            )}
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Notes (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={2}
              placeholder="Add collection notes..."
            />
          </div>

          {/* Preview */}
          {amount > 0 && (
            <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-800 dark:text-green-200">
                  Collection Preview
                </span>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-green-700 dark:text-green-300">Collection Amount:</span>
                  <span className="font-medium">LKR {amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-green-700 dark:text-green-300">New Balance Due:</span>
                  <span className="font-medium">LKR {(invoice.balance_due - amount).toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isRecording}
          >
            Cancel
          </button>
          <button
            onClick={handleRecord}
            disabled={isRecording || amount <= 0 || amount > invoice.balance_due}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isRecording ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Recording...</span>
              </>
            ) : (
              <>
                <DollarSign className="w-4 h-4" />
                <span>Record Collection</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};