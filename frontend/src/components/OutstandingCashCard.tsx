import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { SalesmanCashCollectionModal } from './SalesmanCashCollectionModal';
import toast from 'react-hot-toast';

interface OutstandingCashData {
  salesman_id: number;
  salesman_name: string;
  current_balance: number;
  total_cash_from_invoices: number;
  total_cash_collected_by_owner: number;
  outstanding_cash_with_salesman: number;
  last_collection_date: string | null;
}

interface Salesman {
  id: number;
  name: string;
  current_balance: number;
  user: {
    first_name: string;
    last_name: string;
  };
}

interface OutstandingCashCardProps {
  salesman: Salesman;
  onCashCollected?: () => void;
}

export const OutstandingCashCard: React.FC<OutstandingCashCardProps> = ({
  salesman,
  onCashCollected
}) => {
  const [outstandingData, setOutstandingData] = useState<OutstandingCashData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCollectionModal, setShowCollectionModal] = useState(false);

  const fetchOutstandingCash = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<OutstandingCashData>(`/api/accounts/salesmen/${salesman.id}/outstanding-cash/`);
      setOutstandingData(response);
    } catch (error) {
      console.error('Error fetching outstanding cash:', error);
      toast.error('Failed to fetch outstanding cash data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOutstandingCash();
  }, [salesman.id]);

  const handleCashCollected = (result: any) => {
    // Refresh the outstanding cash data
    fetchOutstandingCash();
    
    // Update the salesman's current balance in the parent component
    if (onCashCollected) {
      onCashCollected();
    }
    
    toast.success('Cash collection recorded successfully');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const getBalanceColor = (balance: number) => {
    if (balance > 1000) return 'text-green-600';
    if (balance > 0) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-200 rounded"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          <div className="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    );
  }

  if (!outstandingData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Cash Status - {salesman.name}
        </h3>
        <p className="text-red-500">Failed to load cash data</p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Cash Status - {outstandingData.salesman_name}
          </h3>
          {outstandingData.current_balance > 0 && (
            <button
              onClick={() => setShowCollectionModal(true)}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              Collect Cash
            </button>
          )}
        </div>
        
        <div className="space-y-3">
          {/* Current Balance */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Current Balance:</span>
            <span className={`font-semibold ${getBalanceColor(outstandingData.current_balance)}`}>
              LKR {outstandingData.current_balance.toFixed(2)}
            </span>
          </div>
          
          {/* Outstanding Cash */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Outstanding Cash:</span>
            <span className={`font-semibold ${getBalanceColor(outstandingData.outstanding_cash_with_salesman)}`}>
              LKR {outstandingData.outstanding_cash_with_salesman.toFixed(2)}
            </span>
          </div>
          
          {/* Total from Invoices */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total from Invoices:</span>
            <span className="font-semibold text-blue-600">
              LKR {outstandingData.total_cash_from_invoices.toFixed(2)}
            </span>
          </div>
          
          {/* Total Collected */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total Collected:</span>
            <span className="font-semibold text-purple-600">
              LKR {outstandingData.total_cash_collected_by_owner.toFixed(2)}
            </span>
          </div>
          
          {/* Last Collection Date */}
          <div className="flex justify-between items-center pt-2 border-t">
            <span className="text-sm text-gray-600">Last Collection:</span>
            <span className="text-sm text-gray-900">
              {formatDate(outstandingData.last_collection_date)}
            </span>
          </div>
        </div>
        
        {/* Status Indicator */}
        <div className="mt-4 pt-3 border-t">
          {outstandingData.current_balance > 0 ? (
            <div className="flex items-center text-sm">
              <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
              <span className="text-yellow-700">Cash available for collection</span>
            </div>
          ) : (
            <div className="flex items-center text-sm">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-green-700">All cash collected</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Cash Collection Modal */}
      <SalesmanCashCollectionModal
        salesman={salesman}
        isOpen={showCollectionModal}
        onClose={() => setShowCollectionModal(false)}
        onSuccess={handleCashCollected}
      />
    </>
  );
};