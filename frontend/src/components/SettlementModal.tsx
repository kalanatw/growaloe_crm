import React, { useState, useEffect } from 'react';
import { LoadingSpinner } from './LoadingSpinner';
import { X, Calculator, Package, DollarSign, AlertCircle } from 'lucide-react';
import { deliveryService } from '../services/apiServices';
import { DeliverySettlementData, DeliverySettlementItem } from '../types';
import toast from 'react-hot-toast';

interface SettlementModalProps {
  deliveryId: number;
  isOpen: boolean;
  onClose: () => void;
  onSettled: () => void;
}

export const SettlementModal: React.FC<SettlementModalProps> = ({
  deliveryId,
  isOpen,
  onClose,
  onSettled,
}) => {
  const [settlementData, setSettlementData] = useState<DeliverySettlementData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSettling, setIsSettling] = useState(false);
  const [settlementNotes, setSettlementNotes] = useState('');
  const [items, setItems] = useState<Array<{
    delivery_item_id: number;
    remaining_quantity: number;
    margin_earned: number;
  }>>([]);

  useEffect(() => {
    if (isOpen) {
      loadSettlementData();
    }
  }, [isOpen, deliveryId]);

  const loadSettlementData = async () => {
    try {
      setIsLoading(true);
      const data = await deliveryService.getSettlementData(deliveryId);
      setSettlementData(data);
      
      // Initialize items with current data
      setItems(data.items.map(item => ({
        delivery_item_id: item.delivery_item_id,
        remaining_quantity: item.remaining_quantity,
        margin_earned: item.margin_earned,
      })));
    } catch (error) {
      console.error('Error loading settlement data:', error);
      toast.error('Failed to load settlement data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuantityChange = (deliveryItemId: number, newQuantity: number) => {
    setItems(prev => prev.map(item => 
      item.delivery_item_id === deliveryItemId
        ? { ...item, remaining_quantity: Math.max(0, newQuantity) }
        : item
    ));
  };

  const handleMarginChange = (deliveryItemId: number, newMargin: number) => {
    setItems(prev => prev.map(item => 
      item.delivery_item_id === deliveryItemId
        ? { ...item, margin_earned: Math.max(0, newMargin) }
        : item
    ));
  };

  const calculateTotalMargin = () => {
    return items.reduce((total, item) => total + item.margin_earned, 0);
  };

  const calculateTotalReturning = () => {
    return items.reduce((total, item) => total + item.remaining_quantity, 0);
  };

  const handleSettle = async () => {
    try {
      setIsSettling(true);
      
      await deliveryService.settleDelivery(deliveryId, {
        settlement_notes: settlementNotes.trim() || undefined,
        items: items,
      });

      toast.success('Delivery settled successfully!');
      onSettled();
      onClose();
    } catch (error: any) {
      console.error('Error settling delivery:', error);
      toast.error(error.response?.data?.detail || 'Failed to settle delivery');
    } finally {
      setIsSettling(false);
    }
  };

  const getSettlementItem = (deliveryItemId: number) => {
    return items.find(item => item.delivery_item_id === deliveryItemId);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Calculator className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Settle Delivery</h2>
              <p className="text-gray-600">
                {settlementData ? `Delivery #${settlementData.delivery_id} - ${settlementData.salesman_name}` : 'Loading...'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : settlementData ? (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Package className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800">Total Returning</span>
                </div>
                <p className="text-2xl font-bold text-blue-900 mt-1">
                  {calculateTotalReturning()}
                </p>
                <p className="text-xs text-blue-600">units back to owner</p>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-green-800">Total Margin</span>
                </div>
                <p className="text-2xl font-bold text-green-900 mt-1">
                  LKR {calculateTotalMargin().toFixed(2)}
                </p>
                <p className="text-xs text-green-600">earned by salesman</p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Calculator className="w-5 h-5 text-purple-600" />
                  <span className="text-sm font-medium text-purple-800">Delivery Date</span>
                </div>
                <p className="text-lg font-bold text-purple-900 mt-1">
                  {new Date(settlementData.delivery_date).toLocaleDateString()}
                </p>
                <p className="text-xs text-purple-600">original delivery</p>
              </div>
            </div>

            {/* Settlement Items */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center space-x-2">
                <Package className="w-5 h-5" />
                <span>Settlement Details</span>
              </h3>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Delivered
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sold
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Remaining
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Margin Earned
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {settlementData.items.map((item) => {
                      const settlementItem = getSettlementItem(item.delivery_item_id);
                      const currentRemaining = settlementItem?.remaining_quantity ?? item.remaining_quantity;
                      const currentMargin = settlementItem?.margin_earned ?? item.margin_earned;
                      
                      return (
                        <tr key={item.delivery_item_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {item.product_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                ID: {item.product_id}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">
                              {item.delivered_quantity}
                            </span>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <span className="text-sm text-gray-900">
                              {item.sold_quantity}
                            </span>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <input
                              type="number"
                              min="0"
                              max={item.delivered_quantity - item.sold_quantity}
                              value={currentRemaining}
                              onChange={(e) => handleQuantityChange(
                                item.delivery_item_id,
                                parseInt(e.target.value) || 0
                              )}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="flex items-center space-x-1">
                              <span className="text-sm text-gray-500">LKR</span>
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={currentMargin}
                                onChange={(e) => handleMarginChange(
                                  item.delivery_item_id,
                                  parseFloat(e.target.value) || 0
                                )}
                                className="w-24 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Settlement Notes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Settlement Notes (Optional)
              </label>
              <textarea
                value={settlementNotes}
                onChange={(e) => setSettlementNotes(e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Add any notes about this settlement..."
              />
            </div>

            {/* Warning */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Settlement Confirmation</h4>
                  <p className="text-sm text-yellow-700 mt-1">
                    Once settled, the remaining stock will be returned to the owner and this action cannot be undone.
                    The salesman will receive their calculated margin and the delivery will be marked as completed.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                onClick={onClose}
                disabled={isSettling}
                className="btn btn-outline"
              >
                Cancel
              </button>
              <button
                onClick={handleSettle}
                disabled={isSettling}
                className="btn btn-primary flex items-center space-x-2"
              >
                {isSettling ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Settling...</span>
                  </>
                ) : (
                  <>
                    <Calculator className="w-4 h-4" />
                    <span>Settle Delivery</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">Failed to load settlement data</p>
          </div>
        )}
      </div>
    </div>
  );
};
