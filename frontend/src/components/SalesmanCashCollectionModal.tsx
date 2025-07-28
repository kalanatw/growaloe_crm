import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { apiClient } from '../services/api';

interface SalesmanCashCollectionModalProps {
  salesman: {
    id: number;
    name: string;
    current_balance: number;
    user: {
      first_name: string;
      last_name: string;
    };
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: any) => void;
}

interface CashCollectionData {
  amount: number;
  collection_date: string;
  collection_method: 'physical_handover' | 'bank_deposit' | 'digital_transfer';
  reference_number?: string;
  notes?: string;
}

export const SalesmanCashCollectionModal: React.FC<SalesmanCashCollectionModalProps> = ({
  salesman,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [formData, setFormData] = useState<CashCollectionData>({
    amount: 0,
    collection_date: new Date().toISOString().split('T')[0],
    collection_method: 'physical_handover',
    reference_number: '',
    notes: ''
  });
  const [isCollecting, setIsCollecting] = useState(false);

  const handleInputChange = (field: keyof CashCollectionData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCollectCash = async () => {
    if (formData.amount <= 0) {
      toast.error('Amount must be greater than zero');
      return;
    }

    if (formData.amount > salesman.current_balance) {
      toast.error(`Amount cannot exceed salesman's current balance of LKR ${salesman.current_balance.toFixed(2)}`);
      return;
    }

    try {
      setIsCollecting(true);
      
      const response = await apiClient.post<{
        collection: any;
        salesman_balance_after: number;
        message: string;
      }>(`/api/accounts/salesmen/${salesman.id}/collect-cash/`, formData);
      
      toast.success(`Cash collected: LKR ${formData.amount.toFixed(2)}`);
      toast.success(`Salesman balance updated to LKR ${response.salesman_balance_after.toFixed(2)}`);
      
      onSuccess(response);
      onClose();
      
      // Reset form
      setFormData({
        amount: 0,
        collection_date: new Date().toISOString().split('T')[0],
        collection_method: 'physical_handover',
        reference_number: '',
        notes: ''
      });
      
    } catch (error: any) {
      console.error('Error collecting cash:', error);
      const errorMessage = error.response?.data?.error || 'Failed to collect cash';
      toast.error(errorMessage);
    } finally {
      setIsCollecting(false);
    }
  };

  const handleMaxAmount = () => {
    setFormData(prev => ({
      ...prev,
      amount: salesman.current_balance
    }));
  };

  if (!isOpen) return null;

  const salesmanName = `${salesman.user.first_name} ${salesman.user.last_name}`;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4 text-gray-900">Collect Cash from Salesman</h2>
        
        <div className="space-y-4">
          {/* Salesman Info */}
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="text-sm text-gray-600">Salesman</div>
            <div className="text-lg font-semibold text-gray-900">{salesmanName}</div>
            <div className="text-sm text-gray-600 mt-1">
              Current Balance: <span className="font-semibold text-green-600">LKR {salesman.current_balance.toFixed(2)}</span>
            </div>
          </div>
          
          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount to Collect *
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => handleInputChange('amount', Number(e.target.value))}
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                step="0.01"
                min="0"
                max={salesman.current_balance}
                placeholder="0.00"
              />
              <button
                type="button"
                onClick={handleMaxAmount}
                className="px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                Max
              </button>
            </div>
            {formData.amount > salesman.current_balance && (
              <p className="text-red-500 text-sm mt-1">
                Amount cannot exceed current balance
              </p>
            )}
          </div>
          
          {/* Collection Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Collection Date *
            </label>
            <input
              type="date"
              value={formData.collection_date}
              onChange={(e) => handleInputChange('collection_date', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Collection Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Collection Method *
            </label>
            <select
              value={formData.collection_method}
              onChange={(e) => handleInputChange('collection_method', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="physical_handover">Physical Handover</option>
              <option value="bank_deposit">Bank Deposit</option>
              <option value="digital_transfer">Digital Transfer</option>
            </select>
          </div>
          
          {/* Reference Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reference Number
            </label>
            <input
              type="text"
              value={formData.reference_number}
              onChange={(e) => handleInputChange('reference_number', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional reference number"
            />
          </div>
          
          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Optional notes about the cash collection..."
            />
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            disabled={isCollecting}
          >
            Cancel
          </button>
          <button
            onClick={handleCollectCash}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-green-500"
            disabled={isCollecting || formData.amount <= 0 || formData.amount > salesman.current_balance}
          >
            {isCollecting ? 'Collecting...' : `Collect LKR ${formData.amount.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
};