import React, { useState } from 'react';
import { Calculator } from 'lucide-react';
import { IndividualDeliverySettlementSummary } from './IndividualDeliverySettlementSummary';

interface SettlementSummaryButtonProps {
  deliveryId: number;
  deliveryNumber: string;
  className?: string;
}

export const SettlementSummaryButton: React.FC<SettlementSummaryButtonProps> = ({
  deliveryId,
  deliveryNumber,
  className = ''
}) => {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className={`btn btn-xs btn-outline text-blue-600 hover:text-blue-800 ${className}`}
        title="View Settlement Summary"
      >
        <Calculator className="w-3 h-3 mr-1" />
        Summary
      </button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Settlement Summary - {deliveryNumber}
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="p-4">
              <IndividualDeliverySettlementSummary
                deliveryId={deliveryId}
                className="mb-4"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};