import React, { useState } from 'react';
import { CompactSettlementButton } from './SettlementBreakdownButton';
import { SettlementSummaryButton } from './SettlementSummaryButton';

interface SalesmanHistoryModalProps {
  salesman: any;
  isOpen: boolean;
  onClose: () => void;
  deliveries: any[];
  settlements: any[];
  isLoading: boolean;
  onShowCashCollection: (settlement: any) => void;
}

export const SalesmanHistoryModal: React.FC<SalesmanHistoryModalProps> = ({
  salesman,
  isOpen,
  onClose,
  deliveries,
  settlements,
  isLoading,
  onShowCashCollection
}) => {
  const [historyTab, setHistoryTab] = useState<'deliveries' | 'settlements'>('deliveries');
  const [expandedDeliveries, setExpandedDeliveries] = useState<{ [key: number]: boolean }>({});

  const toggleExpenseVisibility = (deliveryIndex: number) => {
    setExpandedDeliveries(prev => ({
      ...prev,
      [deliveryIndex]: !prev[deliveryIndex]
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
      <div className="bg-white rounded-lg p-2 sm:p-4 md:p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-4xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">History - {salesman?.salesman_name || salesman?.name}</h3>
          <button className="btn btn-outline btn-sm" onClick={onClose}>Close</button>
        </div>
        
        <div className="flex space-x-4 mb-4">
          <button
            className={`btn btn-sm ${historyTab === 'deliveries' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setHistoryTab('deliveries')}
          >
            Deliveries
          </button>
          <button
            className={`btn btn-sm ${historyTab === 'settlements' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setHistoryTab('settlements')}
          >
            Settlements
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">Loading...</div>
        ) : historyTab === 'deliveries' ? (
          <DeliveriesTab 
            deliveries={deliveries} 
            expandedDeliveries={expandedDeliveries}
            onToggleExpenses={toggleExpenseVisibility}
          />
        ) : (
          <SettlementsTab 
            settlements={settlements} 
            onShowCashCollection={onShowCashCollection}
          />
        )}
      </div>
    </div>
  );
};

const DeliveriesTab: React.FC<{
  deliveries: any[];
  expandedDeliveries: { [key: number]: boolean };
  onToggleExpenses: (index: number) => void;
}> = ({ deliveries, expandedDeliveries, onToggleExpenses }) => {
  if (deliveries.length === 0) {
    return <div className="text-center py-8 text-gray-500">No deliveries found.</div>;
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 mb-6 overflow-x-auto">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivery #</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total Value</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Settlement Balance</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Settlement Summary</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Expenses</th>
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        {deliveries.map((delivery: any, idx: number) => (
          <React.Fragment key={delivery.id}>
            <tr>
              <td className="px-4 py-2 text-sm">{delivery.delivery_number}</td>
              <td className="px-4 py-2 text-sm">{new Date(delivery.delivery_date).toLocaleDateString()}</td>
              <td className="px-4 py-2 text-sm">{delivery.status}</td>
              <td className="px-4 py-2 text-sm">LKR {Number(delivery.total_value).toFixed(2)}</td>
              <td className="px-4 py-2 text-sm">
                {delivery.settlement_breakdown ? (
                  <CompactSettlementButton
                    deliveryId={delivery.id}
                    settlementData={{
                      invoice_settlements_total: delivery.invoice_settlements_total,
                      uncollected_settlements_total: delivery.uncollected_settlements_total,
                      settlement_count: delivery.settlement_count
                    }}
                  />
                ) : (
                  <span className="text-gray-400 text-xs">No settlements</span>
                )}
              </td>
              <td className="px-4 py-2 text-sm">
                <SettlementSummaryButton
                  deliveryId={delivery.id}
                  deliveryNumber={delivery.delivery_number}
                />
              </td>
              <td className="px-4 py-2 text-sm">
                {delivery.expenses && delivery.expenses.length > 0 ? (
                  <button
                    className="btn btn-xs btn-outline"
                    onClick={() => onToggleExpenses(idx)}
                  >
                    {expandedDeliveries[idx] ? 'Hide' : 'Show'} ({delivery.expenses.length})
                  </button>
                ) : (
                  <span className="text-gray-400">None</span>
                )}
              </td>
            </tr>
            {expandedDeliveries[idx] && delivery.expenses && delivery.expenses.length > 0 && (
              <tr>
                <td colSpan={7} className="px-4 pb-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <table className="min-w-full text-xs">
                      <thead>
                        <tr>
                          <th className="px-2 py-1 text-left font-medium text-gray-500">Category</th>
                          <th className="px-2 py-1 text-left font-medium text-gray-500">Amount</th>
                          <th className="px-2 py-1 text-left font-medium text-gray-500">Ref ID</th>
                          <th className="px-2 py-1 text-left font-medium text-gray-500">Notes</th>
                          <th className="px-2 py-1 text-left font-medium text-gray-500">Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        {delivery.expenses.map((exp: any) => (
                          <tr key={exp.id}>
                            <td className="px-2 py-1">{exp.category}</td>
                            <td className="px-2 py-1">LKR {Number(exp.amount).toFixed(2)}</td>
                            <td className="px-2 py-1">{exp.ref_id || '-'}</td>
                            <td className="px-2 py-1">{exp.notes || '-'}</td>
                            <td className="px-2 py-1">{new Date(exp.created_at).toLocaleDateString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </td>
              </tr>
            )}
          </React.Fragment>
        ))}
      </tbody>
    </table>
  );
};

const SettlementsTab: React.FC<{
  settlements: any[];
  onShowCashCollection: (settlement: any) => void;
}> = ({ settlements, onShowCashCollection }) => {
  if (settlements.length === 0) {
    return <div className="text-center py-8 text-gray-500">No settlements found.</div>;
  }

  return (
    <table className="min-w-full divide-y divide-gray-200 mb-6 overflow-x-auto">
      <thead className="bg-gray-50">
        <tr>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Settlement #</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivered</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sold</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Returned</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Cash Collection</th>
        </tr>
      </thead>
      <tbody className="bg-white divide-y divide-gray-200">
        {settlements.map((settlement: any) => (
          <tr key={settlement.id}>
            <td className="px-4 py-2 text-sm">{settlement.settlement_number}</td>
            <td className="px-4 py-2 text-sm">{new Date(settlement.settlement_date).toLocaleDateString()}</td>
            <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_delivered_value).toFixed(2)}</td>
            <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_sold_value).toFixed(2)}</td>
            <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_returned_value).toFixed(2)}</td>
            <td className="px-4 py-2 text-sm">{settlement.status}</td>
            <td className="px-4 py-2 text-sm">
              {settlement.physical_cash_collected ? (
                <div className="flex flex-col">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    ✓ Collected
                  </span>
                  {settlement.physical_cash_amount && (
                    <span className="text-xs text-gray-500 mt-1">
                      LKR {Number(settlement.physical_cash_amount).toFixed(2)}
                    </span>
                  )}
                  {settlement.physical_cash_collected_date && (
                    <span className="text-xs text-gray-500">
                      {new Date(settlement.physical_cash_collected_date).toLocaleDateString()}
                    </span>
                  )}
                </div>
              ) : (
                <div className="flex flex-col space-y-1">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Pending
                  </span>
                  <button
                    onClick={() => {
                      if (!settlement.physical_cash_collected) {
                        onShowCashCollection({
                          salesman_id: settlement.salesman_id,
                          salesman_name: settlement.salesman_name,
                          current_balance: settlement.current_balance || settlement.total_cash_collected || 0
                        });
                      }
                    }}
                    className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={settlement.physical_cash_collected}
                  >
                    Collect Cash
                  </button>
                </div>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};