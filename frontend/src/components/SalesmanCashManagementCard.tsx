import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import { SalesmanCashCollectionModal } from './SalesmanCashCollectionModal';
import { SalesmanCashTransactionHistory } from './SalesmanCashTransactionHistory';
import toast from 'react-hot-toast';

interface Salesman {
  id: number;
  name: string;
  current_balance: number;
  user: {
    first_name: string;
    last_name: string;
  };
}

interface OutstandingCashData {
  salesman_id: number;
  salesman_name: string;
  current_balance: number;
  total_cash_from_invoices: number;
  total_cash_collected_by_owner: number;
  outstanding_cash_with_salesman: number;
  last_collection_date: string | null;
}

interface SalesmanCashManagementCardProps {
  salesman: Salesman;
  onBalanceUpdate?: (newBalance: number) => void;
  showCompact?: boolean;
}

export const SalesmanCashManagementCard: React.FC<SalesmanCashManagementCardProps> = ({
  salesman,
  onBalanceUpdate,
  showCompact = false
}) => {
  const [outstandingData, setOutstandingData] = useState<OutstandingCashData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCollectionModal, setShowCollectionModal] = useState(false);
  const [showTransactionHistory, setShowTransactionHistory] = useState(false);
  const [currentBalance, setCurrentBalance] = useState(salesman.current_balance);

  const fetchOutstandingCash = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<OutstandingCashData>(`/api/accounts/salesmen/${salesman.id}/outstanding-cash/`);
      setOutstandingData(response);
      setCurrentBalance(response.current_balance);
    } catch (error) {
      console.error('Error fetching outstanding cash:', error);
      toast.error('Failed to fetch cash data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOutstandingCash();
  }, [salesman.id]);

  const handleCashCollected = (result: any) => {
    // Update local state
    setCurrentBalance(result.salesman_balance_after);
    
    // Refresh outstanding cash data
    fetchOutstandingCash();
    
    // Notify parent component
    if (onBalanceUpdate) {
      onBalanceUpdate(result.salesman_balance_after);
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

  const getBalanceStatus = (balance: number) => {
    if (balance > 1000) return { color: 'bg-green-500', text: 'High balance - ready for collection' };
    if (balance > 0) return { color: 'bg-yellow-500', text: 'Cash available for collection' };
    return { color: 'bg-gray-500', text: 'No cash to collect' };
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow ${showCompact ? 'p-4' : 'p-6'} animate-pulse`}>
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
      <div className={`bg-white rounded-lg shadow ${showCompact ? 'p-4' : 'p-6'}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Cash Status - {salesman.name}
        </h3>
        <p className="text-red-500">Failed to load cash data</p>
      </div>
    );
  }

  const balanceStatus = getBalanceStatus(currentBalance);

  if (showCompact) {
    return (
      <>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h4 className="font-medium text-gray-900">{outstandingData.salesman_name}</h4>
              <div className="flex items-center mt-1">
                <div className={`w-2 h-2 ${balanceStatus.color} rounded-full mr-2`}></div>
                <span className="text-xs text-gray-600">{balanceStatus.text}</span>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-lg font-bold ${getBalanceColor(currentBalance)}`}>
                LKR {currentBalance.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">Current Balance</div>
            </div>
          </div>
          
          <div className="flex space-x-2">
            {currentBalance > 0 && (
              <button
                onClick={() => setShowCollectionModal(true)}
                className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Collect Cash
              </button>
            )}
            <button
              onClick={() => setShowTransactionHistory(true)}
              className="flex-1 px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              History
            </button>
          </div>
        </div>
        
        {/* Modals */}
        <SalesmanCashCollectionModal
          salesman={salesman}
          isOpen={showCollectionModal}
          onClose={() => setShowCollectionModal(false)}
          onSuccess={handleCashCollected}
        />
        
        <SalesmanCashTransactionHistory
          salesmanId={salesman.id}
          salesmanName={outstandingData.salesman_name}
          currentBalance={currentBalance}
          isOpen={showTransactionHistory}
          onClose={() => setShowTransactionHistory(false)}
        />
      </>
    );
  }

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Cash Management - {outstandingData.salesman_name}
          </h3>
          <div className="flex space-x-2">
            {currentBalance > 0 && (
              <button
                onClick={() => setShowCollectionModal(true)}
                className="px-3 py-1 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                Collect Cash
              </button>
            )}
            <button
              onClick={() => setShowTransactionHistory(true)}
              className="px-3 py-1 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Transaction History
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Current Balance */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Current Balance</div>
            <div className={`text-2xl font-bold ${getBalanceColor(currentBalance)}`}>
              LKR {currentBalance.toFixed(2)}
            </div>
            <div className="flex items-center mt-2">
              <div className={`w-2 h-2 ${balanceStatus.color} rounded-full mr-2`}></div>
              <span className="text-xs text-gray-600">{balanceStatus.text}</span>
            </div>
          </div>
          
          {/* Outstanding Cash */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Outstanding Cash</div>
            <div className={`text-2xl font-bold ${getBalanceColor(outstandingData.outstanding_cash_with_salesman)}`}>
              LKR {outstandingData.outstanding_cash_with_salesman.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-2">
              From unpaid invoices
            </div>
          </div>
        </div>
        
        <div className="space-y-3">
          {/* Total from Invoices */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total from Invoices:</span>
            <span className="font-semibold text-blue-600">
              LKR {outstandingData.total_cash_from_invoices.toFixed(2)}
            </span>
          </div>
          
          {/* Total Collected */}
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Total Collected by Owner:</span>
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
        
        {/* Cash Flow Summary */}
        <div className="mt-4 pt-4 border-t bg-gray-50 -mx-6 -mb-6 px-6 pb-6 rounded-b-lg">
          <div className="text-sm font-medium text-gray-700 mb-2">Cash Flow Summary</div>
          <div className="text-xs text-gray-600">
            <div>• Invoice collections increase balance</div>
            <div>• Delivery expenses reduce balance</div>
            <div>• Owner cash collections reduce balance</div>
            <div>• Current balance shows cash with salesman</div>
          </div>
        </div>
      </div>
      
      {/* Modals */}
      <SalesmanCashCollectionModal
        salesman={salesman}
        isOpen={showCollectionModal}
        onClose={() => setShowCollectionModal(false)}
        onSuccess={handleCashCollected}
      />
      
      <SalesmanCashTransactionHistory
        salesmanId={salesman.id}
        salesmanName={outstandingData.salesman_name}
        currentBalance={currentBalance}
        isOpen={showTransactionHistory}
        onClose={() => setShowTransactionHistory(false)}
      />
    </>
  );
};