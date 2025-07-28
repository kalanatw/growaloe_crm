import React, { useState } from 'react';
import { SalesmanCashManagementCard } from './SalesmanCashManagementCard';

// Example component showing how to integrate the cash management system
export const SalesmanCashManagementExample: React.FC = () => {
  // Example salesman data - replace with your actual data
  const [salesmen, setSalesmen] = useState([
    {
      id: 1,
      name: 'Roshan Padukka',
      current_balance: 3500.00,
      user: {
        first_name: 'Roshan',
        last_name: 'Padukka'
      }
    },
    {
      id: 2,
      name: 'John Silva',
      current_balance: 1200.00,
      user: {
        first_name: 'John',
        last_name: 'Silva'
      }
    }
  ]);

  const handleBalanceUpdate = (salesmanId: number, newBalance: number) => {
    setSalesmen(prev => prev.map(salesman => 
      salesman.id === salesmanId 
        ? { ...salesman, current_balance: newBalance }
        : salesman
    ));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Salesman Cash Management</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {salesmen.map((salesman) => (
          <SalesmanCashManagementCard
            key={salesman.id}
            salesman={salesman}
            onBalanceUpdate={(newBalance) => handleBalanceUpdate(salesman.id, newBalance)}
            showCompact={false}
          />
        ))}
      </div>
      
      {/* Example of compact view */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Compact View Example</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {salesmen.map((salesman) => (
            <SalesmanCashManagementCard
              key={`compact-${salesman.id}`}
              salesman={salesman}
              onBalanceUpdate={(newBalance) => handleBalanceUpdate(salesman.id, newBalance)}
              showCompact={true}
            />
          ))}
        </div>
      </div>
    </div>
  );
};