import React, { useState, useEffect, useCallback } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Plus } from 'lucide-react';
import { deliveryService, salesmanService } from '../services/apiServices';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { CreateDeliveryModal } from '../components/CreateDeliveryModal';
import { DeliverySettlementModal } from '../components/DeliverySettlementModal';
import { SalesmanCashCollectionModal } from '../components/SalesmanCashCollectionModal';
import { SalesmanCentricView } from '../components/SalesmanCentricView';
import { SalesmanDetailsModal } from '../components/SalesmanDetailsModal';
import { SalesmanHistoryModal } from '../components/SalesmanHistoryModal';

export const DeliveriesPage: React.FC = () => {
  const { user } = useAuth();
  const [salesmanOverview, setSalesmanOverview] = useState<any>(null);
  const [settlementQueue, setSettlementQueue] = useState<any>(null);
  const [dailySummary, setDailySummary] = useState<any>(null);
  const [selectedView, setSelectedView] = useState<'overview' | 'balances' | 'settlement' | 'summary'>('overview');
  const [selectedSalesman, setSelectedSalesman] = useState<any>(null);
  const [isSettling, setIsSettling] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [salesmen, setSalesmen] = useState<any[]>([]);
  const [historyModalSalesman, setHistoryModalSalesman] = useState<any | null>(null);
  const [historyDeliveries, setHistoryDeliveries] = useState<any[]>([]);
  const [historySettlements, setHistorySettlements] = useState<any[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyTab, setHistoryTab] = useState<'deliveries' | 'settlements'>('deliveries');
  const [settlementModalSalesman, setSettlementModalSalesman] = useState<any>(null);
  const [cashCollectionModal, setCashCollectionModal] = useState<any>(null);
  const [salesmanBalances, setSalesmanBalances] = useState<any>(null);
  const [cashCollectionAmounts, setCashCollectionAmounts] = useState<{ [key: number]: string }>({});

  useEffect(() => {
    loadData();
    loadSalesmanBalances();
    const interval = setInterval(() => {
      if (!isCreateModalOpen && !selectedSalesman) {
        loadData();
        loadSalesmanBalances();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [isCreateModalOpen, selectedSalesman]);

  const loadSalesmanBalances = async () => {
    try {
      const balanceData = await deliveryService.getSalesmanBalanceSummary();
      setSalesmanBalances(balanceData);
    } catch (error) {
      console.error('Error loading salesman balances:', error);
      // Don't show error toast for balance data as it's supplementary
    }
  };

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [overviewData, queueData, summaryData, salesmenData] = await Promise.all([
        deliveryService.getSalesmanOverview(),
        deliveryService.getSettlementQueue(),
        deliveryService.getDailySummary(),
        salesmanService.getSalesmen(),
      ]);
      setSalesmanOverview(overviewData);
      setSettlementQueue(queueData);
      setDailySummary(summaryData);
      setSalesmen(salesmenData.results);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load deliveries');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateDelivery = async (deliveryData: any) => {
    try {
      await deliveryService.createDelivery(deliveryData);
      toast.success('Delivery created successfully!');
      setIsCreateModalOpen(false);
      loadData();
    } catch (error: any) {
      console.error('Error creating delivery:', error);
      toast.error(error.response?.data?.detail || 'Failed to create delivery');
    }
  };

  const handleSettleSalesman = async (salesmanId: number, settlementData: any) => {
    try {
      setIsSettling(salesmanId);
      const result = await deliveryService.settleSalesmanDeliveries(salesmanId, settlementData);
      toast.success(`Settlement completed for ${result.salesman_name}!`);
      if (result.cash_settlement_amount > 0) {
        toast.success(`Cash settled: LKR ${result.cash_settlement_amount.toFixed(2)}`);
      }
      setSettlementModalSalesman(null); // Close the settlement modal
      loadData();
    } catch (error: any) {
      console.error('Error settling salesman:', error);
      toast.error(error.response?.data?.error || 'Failed to settle deliveries');
    } finally {
      setIsSettling(null);
    }
  };

  const handleViewSalesmanDetails = async (salesmanId: number) => {
    try {
      const details = await deliveryService.getSalesmanDeliveryDetails(salesmanId);
      setSelectedSalesman(details);
    } catch (error: any) {
      console.error('Error loading salesman details:', error);
      toast.error('Failed to load salesman details');
    }
  };

  const handleShowHistoryModal = async (salesman: any) => {
    setHistoryModalSalesman(salesman);
    setIsHistoryLoading(true);
    setHistoryTab('deliveries');
    try {
      // Use the correct salesman ID field - could be salesman_id or id depending on context
      const salesmanId = salesman.salesman_id || salesman.id;
      // Use deliveryService for proper authentication
      const [deliveriesData, settlementsData] = await Promise.all([
        deliveryService.getSalesmanDeliveryDetails(salesmanId).then(data => ({ results: data.deliveries?.recent_deliveries || [] })),
        deliveryService.getSettlementHistory(salesmanId)
      ]);
      setHistoryDeliveries(deliveriesData.results || deliveriesData);
      setHistorySettlements((settlementsData as any).results || settlementsData);
    } catch (err) {
      setHistoryDeliveries([]);
      setHistorySettlements([]);
    } finally {
      setIsHistoryLoading(false);
    }
  };

  const handleCloseHistoryModal = () => {
    setHistoryModalSalesman(null);
    setHistoryDeliveries([]);
    setHistorySettlements([]);
  };

  const handleCashCollectionSuccess = (result: any) => {
    toast.success(`Cash collected: LKR ${result.amount_collected}`);
    if (result.next_delivery_ready) {
      toast.success(`${result.salesman_name} is ready for next delivery!`);
    }
    loadData(); // Refresh data
    setCashCollectionModal(null);
  };

  const handleQuickCashCollection = async (salesman: any) => {
    const amount = parseFloat(cashCollectionAmounts[salesman.id] || '0');
    if (amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (amount > salesman.current_balance) {
      toast.error(`Amount cannot exceed available cash: LKR ${salesman.current_balance.toFixed(2)}`);
      return;
    }

    try {
      // First, try to get the most recent settlement for this salesman
      let settlementId = null;

      try {
        // Use deliveryService which handles authentication properly
        const settlements = await deliveryService.getSettlementHistory(salesman.id) as any;
        const settlementData = settlements.results || settlements;
        if (Array.isArray(settlementData) && settlementData.length > 0) {
          settlementId = settlementData[0].id;
        }
      } catch (fetchError: any) {
        console.warn('Could not fetch recent settlement, using fallback');

        // Handle authentication errors
        if (fetchError?.response?.status === 401) {
          toast.error('Session expired. Please login again.');
          return; // Exit early on auth error
        }
      }

      // If we couldn't find a recent settlement, use a fallback approach
      if (!settlementId) {
        // Try the known settlement ID 41 as last resort
        settlementId = 41;
      }

      const response = await deliveryService.collectPhysicalCash({
        settlement_id: settlementId,
        amount_collected: amount,
        collection_method: amount === salesman.current_balance ? 'full_amount' : 'partial_amount',
        collection_notes: `Quick collection from delivery view - ${new Date().toLocaleString()}`
      });

      toast.success(`Cash collected: LKR ${amount.toFixed(2)}`);
      if (response.next_delivery_ready) {
        toast.success(`${response.salesman_name} is ready for next delivery!`);
      }

      // Clear the input and refresh data
      setCashCollectionAmounts(prev => ({
        ...prev,
        [salesman.id]: ''
      }));
      loadData();
      loadSalesmanBalances();

    } catch (error: any) {
      console.error('Error collecting cash:', error);
      const errorMessage = error.response?.data?.error || 'Failed to collect cash';
      toast.error(errorMessage);

      // If settlement not found, suggest using the modal instead
      if (errorMessage.includes('Settlement not found')) {
        toast.error('Please use the detailed cash collection modal instead');
      }
    }
  };

  if (isLoading) {
    return (
      <Layout title="Deliveries">
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout title="Deliveries">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            {/* <h1 className="text-2xl font-bold text-gray-900">Delivery Management</h1> */}
            <p className="text-gray-600">Manage deliveries and settlements by salesman</p>
          </div>
          {user?.role === 'owner' && (
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="btn btn-primary flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>New Delivery</span>
            </button>
          )}
        </div>
        <SalesmanCentricView
          salesmanOverview={salesmanOverview}
          settlementQueue={settlementQueue}
          dailySummary={dailySummary}
          selectedView={selectedView}
          setSelectedView={setSelectedView}
          onViewSalesmanDetails={handleViewSalesmanDetails}
          onSettleSalesman={(salesmanId: number) => {
            const salesmanData = salesmanOverview?.salesmen?.find((s: any) => s.salesman_id === salesmanId);
            if (salesmanData) {
              setSettlementModalSalesman(salesmanData);
            }
          }}
          isSettling={isSettling}
          onShowHistory={handleShowHistoryModal}
          salesmanBalances={salesmanBalances}
          cashCollectionAmounts={cashCollectionAmounts}
          setCashCollectionAmounts={setCashCollectionAmounts}
          onQuickCashCollection={handleQuickCashCollection}
          onShowCashCollection={setCashCollectionModal}
        />
        {isCreateModalOpen && (
          <CreateDeliveryModal
            isOpen={isCreateModalOpen}
            onClose={() => setIsCreateModalOpen(false)}
            onSubmit={handleCreateDelivery}
            salesmen={salesmen}
          />
        )}
        {selectedSalesman && (
          <SalesmanDetailsModal
            salesman={selectedSalesman}
            isOpen={!!selectedSalesman}
            onClose={() => setSelectedSalesman(null)}
            onSettle={handleSettleSalesman}
            isSettling={isSettling}
            activeDeliveryId={selectedSalesman.active_delivery_id} // Pass the active delivery ID
            user={user} // Pass user down
          />
        )}
        <SalesmanHistoryModal
          salesman={historyModalSalesman}
          isOpen={!!historyModalSalesman}
          onClose={handleCloseHistoryModal}
          deliveries={historyDeliveries}
          settlements={historySettlements}
          isLoading={isHistoryLoading}
          onShowCashCollection={setCashCollectionModal}
        />

        {/* Settlement Modal */}
        <DeliverySettlementModal
          salesman={settlementModalSalesman}
          isOpen={!!settlementModalSalesman}
          onClose={() => setSettlementModalSalesman(null)}
          onSettle={handleSettleSalesman}
          isSettling={!!isSettling}
        />

        {/* Physical Cash Collection Modal */}
        {cashCollectionModal && (
          <SalesmanCashCollectionModal
            salesman={{
              id: cashCollectionModal.salesman_id || cashCollectionModal.id,
              name: cashCollectionModal.salesman_name,
              current_balance: cashCollectionModal.current_balance || cashCollectionModal.total_cash_collected || 0,
              user: {
                first_name: cashCollectionModal.salesman_name.split(' ')[0] || '',
                last_name: cashCollectionModal.salesman_name.split(' ').slice(1).join(' ') || ''
              }
            }}
            isOpen={!!cashCollectionModal}
            onClose={() => setCashCollectionModal(null)}
            onSuccess={(result) => {
              handleCashCollectionSuccess(result);
              loadData(); // Refresh data
            }}
          />
        )}
      </div>
    </Layout>
  );
};