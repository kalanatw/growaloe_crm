import React, { useState } from 'react';
import { TrendingUp, DollarSign } from 'lucide-react';
import { InvoiceSettlementBreakdown } from './InvoiceSettlementBreakdown';

interface SettlementBreakdownButtonProps {
  deliveryId: number;
  settlementData?: {
    invoice_settlements_total: number;
    uncollected_settlements_total: number;
    settlement_count: number;
  };
  className?: string;
}

export const SettlementBreakdownButton: React.FC<SettlementBreakdownButtonProps> = ({
  deliveryId,
  settlementData,
  className = ''
}) => {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const totalCollected = settlementData?.invoice_settlements_total || 0;
  const totalOutstanding = settlementData?.uncollected_settlements_total || 0;
  const settlementCount = settlementData?.settlement_count || 0;

  return (
    <>
      <button
        onClick={() => setShowBreakdown(true)}
        className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${className}`}
        title="View detailed settlement breakdown"
      >
        <TrendingUp className="w-4 h-4 mr-2" />
        <div className="text-left">
          <div className="flex items-center space-x-2">
            <span>Settlement Balance</span>
            {settlementCount > 0 && (
              <span className="bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400 px-2 py-0.5 rounded-full text-xs">
                {settlementCount}
              </span>
            )}
          </div>
          <div className="text-xs opacity-75">
            <span className="text-green-600">LKR {totalCollected.toFixed(2)}</span>
            {totalOutstanding > 0 && (
              <>
                <span className="mx-1">•</span>
                <span className="text-orange-600">LKR {totalOutstanding.toFixed(2)} pending</span>
              </>
            )}
          </div>
        </div>
      </button>

      <InvoiceSettlementBreakdown
        deliveryId={deliveryId}
        isOpen={showBreakdown}
        onClose={() => setShowBreakdown(false)}
      />
    </>
  );
};

// Compact version for table cells
export const CompactSettlementButton: React.FC<SettlementBreakdownButtonProps> = ({
  deliveryId,
  settlementData,
  className = ''
}) => {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const totalCollected = settlementData?.invoice_settlements_total || 0;
  const totalOutstanding = settlementData?.uncollected_settlements_total || 0;
  const settlementCount = settlementData?.settlement_count || 0;

  return (
    <>
      <button
        onClick={() => setShowBreakdown(true)}
        className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:hover:bg-blue-900/30 transition-colors ${className}`}
        title="View settlement breakdown"
      >
        <DollarSign className="w-3 h-3 mr-1" />
        <span>LKR {totalCollected.toFixed(0)}</span>
        {settlementCount > 0 && (
          <span className="ml-1 bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200 px-1 rounded-full text-xs">
            {settlementCount}
          </span>
        )}
      </button>

      <InvoiceSettlementBreakdown
        deliveryId={deliveryId}
        isOpen={showBreakdown}
        onClose={() => setShowBreakdown(false)}
      />
    </>
  );
};