import React, { useState } from 'react';
import toast from 'react-hot-toast';
import { deliveryService } from '../services/apiServices';

interface PhysicalCashCollectionModalProps {
  settlement: {
    id: number;
    salesman_name: string;
    current_balance: number;
    settlement_date: string;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: any) => void;
}

export const PhysicalCashCollectionModal: React.FC<PhysicalCashCollectionModalProps> = ({
  settlement,
  isOpen,
  onClose,
  onSuccess
}) => {
  const [amountCollected, setAmountCollected] = useState(settlement.current_balance);
  const [collectionMethod, setCollectionMethod] = useState<'full_amount' | 'partial_amount' | 'excess_returned'>('full_amount');
  const [collectionNotes, setCollectionNotes] = useState('');
  const [isCollecting, setIsCollecting] = useState(false);

  const handleCollectCash = async () => {
    try {
      setIsCollecting(true);
      
      const response = await deliveryService.collectPhysicalCash({
        settlement_id: settlement.id,
        amount_collected: amountCollected,
        collection_method: collectionMethod,
        collection_notes: collectionNotes
      });
      
      toast.success(`Cash collected: LKR ${amountCollected.toFixed(2)}`);
      if (response.next_delivery_ready) {
        toast.success(`${response.salesman_name} is ready for next delivery!`);
      }
      onSuccess(response);
      onClose();
      
    } catch (error: any) {
      console.error('Error collecting cash:', error);
      toast.error(error.response?.data?.error || 'Failed to collect cash');
    } finally {
      setIsCollecting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-semibold mb-4">Collect Physical Cash</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Salesman
            </label>
            <div className="text-lg font-semibold text-gray-900">
              {settlement.salesman_name}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Available Cash
            </label>
            <div className="text-lg font-semibold text-green-600">
              LKR {settlement.current_balance.toFixed(2)}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount to Collect
            </label>
            <input
              type="number"
              value={amountCollected}
              onChange={(e) => setAmountCollected(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              step="0.01"
              min="0"
              max={settlement.current_balance}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Collection Method
            </label>
            <select
              value={collectionMethod}
              onChange={(e) => setCollectionMethod(e.target.value as any)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="full_amount">Full Amount</option>
              <option value="partial_amount">Partial Amount</option>
              <option value="excess_returned">Excess Returned to Salesman</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Collection Notes
            </label>
            <textarea
              value={collectionNotes}
              onChange={(e) => setCollectionNotes(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              rows={3}
              placeholder="Notes about the cash collection..."
            />
          </div>
        </div>
        
        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            disabled={isCollecting}
          >
            Cancel
          </button>
          <button
            onClick={handleCollectCash}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            disabled={isCollecting || amountCollected <= 0}
          >
            {isCollecting ? 'Collecting...' : `Collect LKR ${amountCollected.toFixed(2)}`}
          </button>
        </div>
      </div>
    </div>
  );
};