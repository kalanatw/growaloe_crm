import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { 
  Plus, 
  Package, 
  Calendar, 
  User, 
  CheckCircle, 
  Clock, 
  Eye,
  Edit,
  Truck,
  Calculator,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  Users,
  BarChart3,
  ArrowRight,
  Phone,
  Mail,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';
import { deliveryService, salesmanService } from '../services/apiServices';
import { Delivery, Salesman } from '../types';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { CreateDeliveryModal } from '../components/CreateDeliveryModal';
import { SettlementModal } from '../components/SettlementModal';

export const DeliveriesPage: React.FC = () => {
  const { user } = useAuth();
  const [useSalesmanView, setUseSalesmanView] = useState(true); // Default to new view
  
  // Legacy state
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [salesmen, setSalesmen] = useState<Salesman[]>([]);
  const [selectedDelivery, setSelectedDelivery] = useState<Delivery | null>(null);
  const [settlementDeliveryId, setSettlementDeliveryId] = useState<number | null>(null);
  
  // New salesman-centric state
  const [salesmanOverview, setSalesmanOverview] = useState<any>(null);
  const [settlementQueue, setSettlementQueue] = useState<any>(null);
  const [dailySummary, setDailySummary] = useState<any>(null);
  const [selectedView, setSelectedView] = useState<'overview' | 'settlement' | 'summary'>('overview');
  const [selectedSalesman, setSelectedSalesman] = useState<any>(null);
  const [isSettling, setIsSettling] = useState<number | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    loadData();
    
    // Set up real-time updates every 30 seconds, but pause when modals are open
    const interval = setInterval(() => {
      // Don't auto-refresh if any modal is open to avoid interrupting user interactions
      if (!isCreateModalOpen && !selectedDelivery && !settlementDeliveryId && !selectedSalesman) {
        loadData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isCreateModalOpen, selectedDelivery, settlementDeliveryId, selectedSalesman, useSalesmanView]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      
      if (useSalesmanView) {
        // Load salesman-centric data
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
      } else {
        // Load legacy delivery data
        const [deliveriesData, salesmenData] = await Promise.all([
          deliveryService.getDeliveries(),
          salesmanService.getSalesmen(),
        ]);
        
        setDeliveries(deliveriesData.results);
        setSalesmen(salesmenData.results);
      }
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
      loadData(); // Reload the deliveries
    } catch (error: any) {
      console.error('Error creating delivery:', error);
      toast.error(error.response?.data?.detail || 'Failed to create delivery');
    }
  };

  // Legacy handlers
  const handleMarkAsDelivered = async (deliveryId: number) => {
    try {
      await deliveryService.markAsDelivered(deliveryId);
      toast.success('Delivery marked as delivered!');
      loadData(); // Reload the deliveries
    } catch (error: any) {
      console.error('Error updating delivery status:', error);
      toast.error(error.response?.data?.detail || 'Failed to update delivery status');
    }
  };

  const handleSettlementCompleted = () => {
    setSettlementDeliveryId(null);
    loadData(); // Reload deliveries to reflect settlement
  };

  // New salesman-centric handlers
  const handleSettleSalesman = async (salesmanId: number, settlement_notes: string = '') => {
    try {
      setIsSettling(salesmanId);
      const result = await deliveryService.settleSalesmanDeliveries(salesmanId, {
        settlement_notes,
        return_all_stock: true,
        create_settlement_record: true
      });
      
      toast.success(`Settlement completed for ${result.salesman_name}!`);
      loadData(); // Refresh data
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

  if (isLoading) {
    return (
      <Layout title="Deliveries">
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout title={useSalesmanView ? "Salesman-Centric Delivery Management" : "Product Deliveries"}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {useSalesmanView ? "Delivery Management" : "Product Deliveries"}
                </h1>
                <p className="text-gray-600">
                  {useSalesmanView 
                    ? "Manage deliveries and settlements by salesman" 
                    : "Manage product allocations to salesmen"
                  }
                </p>
              </div>
              
              {/* View Toggle */}
              <div className="flex items-center space-x-2 ml-8">
                <span className="text-sm text-gray-600">Legacy View</span>
                <button
                  onClick={() => setUseSalesmanView(!useSalesmanView)}
                  className="relative inline-flex items-center"
                >
                  {useSalesmanView ? (
                    <ToggleRight className="w-8 h-8 text-blue-600" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                </button>
                <span className="text-sm text-gray-600">Salesman View</span>
              </div>
            </div>
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

        {/* Render based on selected view */}
        {useSalesmanView ? (
          <SalesmanCentricView
            salesmanOverview={salesmanOverview}
            settlementQueue={settlementQueue}
            dailySummary={dailySummary}
            selectedView={selectedView}
            setSelectedView={setSelectedView}
            onViewSalesmanDetails={handleViewSalesmanDetails}
            onSettleSalesman={handleSettleSalesman}
            isSettling={isSettling}
          />
        ) : (
          <LegacyDeliveryView
            deliveries={deliveries}
            user={user}
            onViewDetails={setSelectedDelivery}
            onMarkAsDelivered={handleMarkAsDelivered}
            onStartSettlement={setSettlementDeliveryId}
          />
        )}

        {/* Create Delivery Modal */}
        {isCreateModalOpen && (
          <CreateDeliveryModal
            isOpen={isCreateModalOpen}
            onClose={() => setIsCreateModalOpen(false)}
            onSubmit={handleCreateDelivery}
            salesmen={salesmen}
          />
        )}

        {/* Legacy Settlement Modal */}
        {settlementDeliveryId && (
          <SettlementModal
            deliveryId={settlementDeliveryId}
            isOpen={!!settlementDeliveryId}
            onClose={() => setSettlementDeliveryId(null)}
            onSettled={handleSettlementCompleted}
          />
        )}

        {/* Legacy Delivery Details Modal */}
        {selectedDelivery && (
          <DeliveryDetailsModal
            delivery={selectedDelivery}
            isOpen={!!selectedDelivery}
            onClose={() => setSelectedDelivery(null)}
          />
        )}

        {/* Salesman Details Modal */}
        {selectedSalesman && (
          <SalesmanDetailsModal
            salesman={selectedSalesman}
            isOpen={!!selectedSalesman}
            onClose={() => setSelectedSalesman(null)}
            onSettle={handleSettleSalesman}
            isSettling={isSettling}
          />
        )}
      </div>
    </Layout>
  );
};

// Helper function for status badges
const getStatusBadge = (status: string) => {
  switch (status) {
    case 'pending':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <Clock className="w-3 h-3 mr-1" />
          Pending
        </span>
      );
    case 'delivered':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Delivered
        </span>
      );
    case 'settled':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <CheckCircle className="w-3 h-3 mr-1" />
          Settled
        </span>
      );
    case 'cancelled':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
          Cancelled
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
          {status}
        </span>
      );
  }
};

// Salesman-Centric View Component
const SalesmanCentricView: React.FC<{
  salesmanOverview: any;
  settlementQueue: any;
  dailySummary: any;
  selectedView: 'overview' | 'settlement' | 'summary';
  setSelectedView: (view: 'overview' | 'settlement' | 'summary') => void;
  onViewSalesmanDetails: (salesmanId: number) => void;
  onSettleSalesman: (salesmanId: number, notes?: string) => void;
  isSettling: number | null;
}> = ({ 
  salesmanOverview, 
  settlementQueue, 
  dailySummary, 
  selectedView, 
  setSelectedView, 
  onViewSalesmanDetails, 
  onSettleSalesman, 
  isSettling 
}) => {
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Salesmen</p>
              <p className="text-2xl font-bold text-gray-900">
                {salesmanOverview?.salesmen_count || 0}
              </p>
            </div>
            <Users className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Stock Value</p>
              <p className="text-2xl font-bold text-gray-900">
                LKR {(salesmanOverview?.total_stock_value || 0).toFixed(2)}
              </p>
            </div>
            <Package className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Pending Settlements</p>
              <p className="text-2xl font-bold text-gray-900">
                {settlementQueue?.total_deliveries_pending || 0}
              </p>
            </div>
            <Calculator className="w-8 h-8 text-orange-500" />
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Today's Revenue</p>
              <p className="text-2xl font-bold text-gray-900">
                LKR {(dailySummary?.summary?.total_sales_revenue || 0).toFixed(2)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Stock Overview', icon: Package },
            { id: 'settlement', label: 'Settlement Queue', icon: Calculator },
            { id: 'summary', label: 'Daily Summary', icon: BarChart3 }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedView(tab.id as any)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedView === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content based on selected view */}
      {selectedView === 'overview' && (
        <SalesmanStockOverview 
          data={salesmanOverview} 
          onViewDetails={onViewSalesmanDetails}
        />
      )}

      {selectedView === 'settlement' && (
        <SettlementQueue 
          data={settlementQueue} 
          onSettle={onSettleSalesman}
          onViewDetails={onViewSalesmanDetails}
          isSettling={isSettling}
        />
      )}

      {selectedView === 'summary' && (
        <DailySummary 
          data={dailySummary} 
          onSettle={onSettleSalesman}
          onViewDetails={onViewSalesmanDetails}
          isSettling={isSettling}
        />
      )}
    </div>
  );
};

// Legacy Delivery View Component
const LegacyDeliveryView: React.FC<{
  deliveries: Delivery[];
  user: any;
  onViewDetails: (delivery: Delivery) => void;
  onMarkAsDelivered: (id: number) => void;
  onStartSettlement: (id: number) => void;
}> = ({ deliveries, user, onViewDetails, onMarkAsDelivered, onStartSettlement }) => {
  return (
    <>
      {/* Deliveries Grid */}
      {deliveries.length === 0 ? (
        <div className="text-center py-12">
          <Truck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No deliveries yet</h3>
          <p className="text-gray-600 mb-6">Start by creating your first product delivery to salesmen</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {deliveries.map((delivery) => (
            <DeliveryCard
              key={delivery.id}
              delivery={delivery}
              user={user}
              onViewDetails={onViewDetails}
              onMarkAsDelivered={onMarkAsDelivered}
              onStartSettlement={onStartSettlement}
              getStatusBadge={getStatusBadge}
            />
          ))}
        </div>
      )}
    </>
  );
};

// Delivery Card Component
const DeliveryCard: React.FC<{
  delivery: Delivery;
  user: any;
  onViewDetails: (delivery: Delivery) => void;
  onMarkAsDelivered: (id: number) => void;
  onStartSettlement: (id: number) => void;
  getStatusBadge: (status: string) => JSX.Element;
}> = ({ delivery, user, onViewDetails, onMarkAsDelivered, onStartSettlement, getStatusBadge }) => {
  const [remainingStock, setRemainingStock] = useState<{ [key: number]: number }>({});
  const [isLoadingStock, setIsLoadingStock] = useState(false);

  useEffect(() => {
    if (delivery.status === 'delivered') {
      loadRemainingStock();
    }
  }, [delivery.id, delivery.status]);

  const loadRemainingStock = async () => {
    try {
      setIsLoadingStock(true);
      const settlementData = await deliveryService.getSettlementData(delivery.id!);
      const stockMap: { [key: number]: number } = {};
      settlementData.items.forEach(item => {
        stockMap[item.product_id] = item.remaining_quantity;
      });
      setRemainingStock(stockMap);
    } catch (error) {
      console.error('Error loading remaining stock:', error);
      // Don't show toast error for this as it's a background operation
    } finally {
      setIsLoadingStock(false);
    }
  };

  const getTotalRemainingStock = () => {
    return Object.values(remainingStock).reduce((total, stock) => total + stock, 0);
  };

  const hasRemainingStock = () => {
    return getTotalRemainingStock() > 0;
  };

  return (
    <div className="card p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Package className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">
              Delivery #{delivery.id}
            </h3>
            <p className="text-sm text-gray-600">
              To: {delivery.salesman_name}
            </p>
          </div>
        </div>
        {getStatusBadge(delivery.status)}
      </div>

      <div className="space-y-3">
        <div className="flex items-center text-sm text-gray-600">
          <Calendar className="w-4 h-4 mr-2" />
          <span>{new Date(delivery.delivery_date).toLocaleDateString()}</span>
        </div>
        
        <div className="flex items-center text-sm text-gray-600">
          <Package className="w-4 h-4 mr-2" />
          <span>{delivery.total_items || delivery.items?.length || 0} items</span>
        </div>

        {/* Show remaining stock for delivered deliveries */}
        {delivery.status === 'delivered' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <div className="flex items-center space-x-2 mb-2">
              <Package className="w-4 h-4 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">Remaining Stock</span>
              {isLoadingStock && (
                <div className="w-3 h-3 border-2 border-yellow-600 border-t-transparent rounded-full animate-spin" />
              )}
            </div>
            {isLoadingStock ? (
              <p className="text-xs text-yellow-600">Loading stock data...</p>
            ) : hasRemainingStock() ? (
              <div>
                <p className="text-sm font-semibold text-yellow-900">
                  {getTotalRemainingStock()} units pending return
                </p>
                <div className="mt-1 space-y-1">
                  {Object.entries(remainingStock).map(([productId, stock]) => {
                    if (stock > 0) {
                      const item = delivery.items?.find(i => i.product?.toString() === productId);
                      return (
                        <p key={productId} className="text-xs text-yellow-700">
                          {item?.product_name || `Product ${productId}`}: {stock} units
                        </p>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            ) : (
              <p className="text-xs text-yellow-600">All stock sold or settled</p>
            )}
          </div>
        )}

        {/* Show settlement info for settled deliveries */}
        {delivery.status === 'settled' && delivery.total_margin_earned && (
          <div className="bg-green-50 border border-green-200 rounded-md p-3">
            <div className="flex items-center space-x-2 mb-1">
              <DollarSign className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-800">Settled</span>
            </div>
            <p className="text-sm font-semibold text-green-900">
              Margin: LKR {delivery.total_margin_earned.toFixed(2)}
            </p>
            {delivery.settlement_date && (
              <p className="text-xs text-green-600">
                On {new Date(delivery.settlement_date).toLocaleDateString()}
              </p>
            )}
          </div>
        )}

        {delivery.notes && (
          <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
            {delivery.notes}
          </p>
        )}
      </div>

      <div className="mt-6 flex space-x-2">
        <button
          onClick={() => onViewDetails(delivery)}
          className="flex-1 btn btn-outline btn-sm flex items-center justify-center space-x-1"
        >
          <Eye className="w-4 h-4" />
          <span>View</span>
        </button>
        
        {delivery.status === 'pending' && user?.role === 'owner' && (
          <button
            onClick={() => onMarkAsDelivered(delivery.id!)}
            className="flex-1 btn btn-primary btn-sm flex items-center justify-center space-x-1"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Mark Delivered</span>
          </button>
        )}

        {delivery.status === 'delivered' && user?.role === 'owner' && (
          <button
            onClick={() => onStartSettlement(delivery.id!)}
            className="flex-1 btn btn-success btn-sm flex items-center justify-center space-x-1"
          >
            <Calculator className="w-4 h-4" />
            <span>Settle</span>
          </button>
        )}
      </div>
    </div>
  );
};

// Delivery Details Modal Component
const DeliveryDetailsModal: React.FC<{
  delivery: Delivery;
  isOpen: boolean;
  onClose: () => void;
}> = ({ delivery, isOpen, onClose }) => {
  const [batchAssignments, setBatchAssignments] = useState<any>(null);
  const [isLoadingBatches, setIsLoadingBatches] = useState(false);

  useEffect(() => {
    if (isOpen && delivery.id) {
      loadBatchAssignments();
    }
  }, [isOpen, delivery.id]);

  const loadBatchAssignments = async () => {
    try {
      setIsLoadingBatches(true);
      const batchData = await deliveryService.getBatchAssignments(delivery.id!);
      setBatchAssignments(batchData);
    } catch (error) {
      console.error('Error loading batch assignments:', error);
      toast.error('Failed to load batch assignments');
    } finally {
      setIsLoadingBatches(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold">Delivery Details #{delivery.id}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        </div>

        <div className="space-y-6">
          {/* Delivery Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Salesman</label>
              <p className="text-gray-900">{delivery.salesman_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Delivery Date</label>
              <p className="text-gray-900">{new Date(delivery.delivery_date).toLocaleDateString()}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Status</label>
              <div className="mt-1">
                {delivery.status === 'pending' ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    <Clock className="w-3 h-3 mr-1" />
                    Pending
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Delivered
                  </span>
                )}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Created By</label>
              <p className="text-gray-900">{delivery.created_by_name}</p>
            </div>
          </div>

          {delivery.notes && (
            <div>
              <label className="text-sm font-medium text-gray-600">Notes</label>
              <p className="text-gray-900 bg-gray-50 p-3 rounded">{delivery.notes}</p>
            </div>
          )}

          {/* Delivery Items */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Items</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SKU
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quantity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Notes
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {delivery.items.map((item, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {item.product_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.product_sku}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {item.notes || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Batch Assignments */}
          {delivery.batch_assignments && delivery.batch_assignments.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Batch Assignments</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Batch #
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Unit Cost
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Expiry Date
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {delivery.batch_assignments.map((batch, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {batch.batch_number}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          {batch.product_name}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="space-y-1">
                            <div>Assigned: <span className="font-medium">{batch.quantity}</span></div>
                            <div className="text-xs text-gray-500">
                              Delivered: {batch.delivered_quantity} | 
                              Outstanding: {batch.outstanding_quantity}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          ${parseFloat(batch.unit_cost.toString()).toFixed(2)}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                          <div className="space-y-1">
                            <div>{new Date(batch.expiry_date).toLocaleDateString()}</div>
                            <div className="text-xs text-gray-500">
                              Mfg: {new Date(batch.manufacturing_date).toLocaleDateString()}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            batch.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                            batch.status === 'delivered' ? 'bg-green-100 text-green-800' :
                            batch.status === 'partially_delivered' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {batch.status.replace('_', ' ').toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Batch Summary */}
              <div className="mt-4 bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Batch Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Batches:</span>
                    <span className="ml-2 font-medium">{delivery.batch_assignments.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Assigned:</span>
                    <span className="ml-2 font-medium">
                      {delivery.batch_assignments.reduce((sum, batch) => sum + batch.quantity, 0)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Value:</span>
                    <span className="ml-2 font-medium">
                      ${delivery.batch_assignments.reduce((sum, batch) => 
                        sum + (batch.quantity * parseFloat(batch.unit_cost.toString())), 0
                      ).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="btn btn-outline"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Salesman Stock Overview Component
const SalesmanStockOverview: React.FC<{
  data: any;
  onViewDetails: (salesmanId: number) => void;
}> = ({ data, onViewDetails }) => {
  if (!data?.salesmen?.length) {
    return (
      <div className="text-center py-12">
        <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No stock distributed</h3>
        <p className="text-gray-600">No salesmen currently have allocated stock</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.salesmen.map((salesman: any) => (
        <div key={salesman.salesman_id} className="card p-6 hover:shadow-lg transition-shadow">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <User className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {salesman.salesman_name}
                </h3>
                <p className="text-sm text-gray-600 flex items-center">
                  <Phone className="w-3 h-3 mr-1" />
                  {salesman.salesman_phone}
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-blue-800">Current Stock</span>
                <Package className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-lg font-bold text-blue-900">
                {salesman.total_stock_quantity} items
              </p>
              <p className="text-sm text-blue-700">
                LKR {salesman.total_stock_value.toFixed(2)}
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-3">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium text-green-800">Today's Sales</span>
                <TrendingUp className="w-4 h-4 text-green-600" />
              </div>
              <p className="text-lg font-bold text-green-900">
                {salesman.today_sales_quantity} items
              </p>
              <p className="text-sm text-green-700">
                LKR {salesman.today_sales_revenue.toFixed(2)}
              </p>
            </div>

            {salesman.stock_by_product.length > 0 && (
              <div className="space-y-1">
                <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  Products ({salesman.total_products})
                </h4>
                <div className="max-h-20 overflow-y-auto space-y-1">
                  {salesman.stock_by_product.slice(0, 3).map((product: any) => (
                    <div key={product.product_id} className="flex justify-between text-xs">
                      <span className="text-gray-600 truncate">
                        {product.product_name}
                      </span>
                      <span className="text-gray-900 font-medium">
                        {product.quantity}
                      </span>
                    </div>
                  ))}
                  {salesman.stock_by_product.length > 3 && (
                    <p className="text-xs text-gray-500">
                      +{salesman.stock_by_product.length - 3} more...
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={() => onViewDetails(salesman.salesman_id)}
              className="w-full btn btn-outline btn-sm flex items-center justify-center space-x-2"
            >
              <Eye className="w-4 h-4" />
              <span>View Details</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

// Settlement Queue Component
const SettlementQueue: React.FC<{
  data: any;
  onSettle: (salesmanId: number, notes?: string) => void;
  onViewDetails: (salesmanId: number) => void;
  isSettling: number | null;
}> = ({ data, onSettle, onViewDetails, isSettling }) => {
  if (!data?.salesmen?.length) {
    return (
      <div className="text-center py-12">
        <CheckCircle className="w-16 h-16 text-green-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">All settled!</h3>
        <p className="text-gray-600">No deliveries pending settlement</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {data.salesmen.map((salesman: any) => (
        <div key={salesman.salesman_id} className="card p-6">
          <div className="flex justify-between items-start mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <User className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {salesman.salesman_name}
                </h3>
                <p className="text-sm text-gray-600">
                  {salesman.total_deliveries} deliveries pending settlement
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onViewDetails(salesman.salesman_id)}
                className="btn btn-outline btn-sm"
              >
                <Eye className="w-4 h-4 mr-1" />
                Details
              </button>
              
              <button
                onClick={() => onSettle(salesman.salesman_id)}
                disabled={isSettling === salesman.salesman_id}
                className="btn btn-primary btn-sm flex items-center space-x-1"
              >
                {isSettling === salesman.salesman_id ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Calculator className="w-4 h-4" />
                )}
                <span>Settle All</span>
              </button>
            </div>
          </div>

          <div className="bg-orange-50 rounded-lg p-4 mb-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm font-medium text-orange-800">
                  Outstanding Value
                </p>
                <p className="text-xl font-bold text-orange-900">
                  LKR {salesman.total_outstanding_value.toFixed(2)}
                </p>
              </div>
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
            {salesman.oldest_delivery_date && (
              <p className="text-xs text-orange-700 mt-1">
                Oldest delivery: {new Date(salesman.oldest_delivery_date).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="space-y-3">
            {salesman.deliveries.slice(0, 2).map((delivery: any) => (
              <div key={delivery.delivery_id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {delivery.delivery_number}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {new Date(delivery.delivery_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {delivery.outstanding_quantity} items
                    </p>
                    <p className="text-sm text-gray-600">
                      LKR {delivery.outstanding_value.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
            
            {salesman.deliveries.length > 2 && (
              <p className="text-sm text-gray-500 text-center">
                +{salesman.deliveries.length - 2} more deliveries...
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

// Daily Summary Component
const DailySummary: React.FC<{
  data: any;
  onSettle: (salesmanId: number, notes?: string) => void;
  onViewDetails: (salesmanId: number) => void;
  isSettling: number | null;
}> = ({ data, onSettle, onViewDetails, isSettling }) => {
  const getRecommendationBadge = (recommendation: string) => {
    switch (recommendation) {
      case 'settle_recommended':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Settlement Recommended
          </span>
        );
      case 'review_required':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Review Required
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            No Action Needed
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Daily Summary - {new Date(data?.date).toLocaleDateString()}
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {data?.summary?.settlement_recommended || 0}
            </p>
            <p className="text-sm text-gray-600">Need Settlement</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600">
              {data?.summary?.review_required || 0}
            </p>
            <p className="text-sm text-gray-600">Need Review</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              LKR {(data?.summary?.total_sales_revenue || 0).toFixed(0)}
            </p>
            <p className="text-sm text-gray-600">Total Revenue</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              LKR {(data?.summary?.total_outstanding_value || 0).toFixed(0)}
            </p>
            <p className="text-sm text-gray-600">Outstanding Value</p>
          </div>
        </div>
      </div>

      {/* Salesmen List */}
      <div className="space-y-4">
        {data?.salesmen?.map((salesman: any) => (
          <div key={salesman.salesman_id} className="card p-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {salesman.salesman_name}
                  </h4>
                  <div className="flex items-center space-x-2 mt-1">
                    {getRecommendationBadge(salesman.recommendation)}
                  </div>
                </div>
                
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Deliveries</p>
                    <p className="font-medium">{salesman.deliveries_count}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Sales</p>
                    <p className="font-medium">LKR {salesman.sales_revenue.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Outstanding</p>
                    <p className="font-medium">LKR {salesman.outstanding_value.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Efficiency</p>
                    <p className="font-medium">{salesman.efficiency_rate}%</p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => onViewDetails(salesman.salesman_id)}
                  className="btn btn-outline btn-sm"
                >
                  <Eye className="w-4 h-4 mr-1" />
                  Details
                </button>
                
                {salesman.recommendation !== 'no_action' && (
                  <button
                    onClick={() => onSettle(salesman.salesman_id)}
                    disabled={isSettling === salesman.salesman_id}
                    className="btn btn-primary btn-sm flex items-center space-x-1"
                  >
                    {isSettling === salesman.salesman_id ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Calculator className="w-4 h-4" />
                    )}
                    <span>Settle</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Salesman Details Modal Component
const SalesmanDetailsModal: React.FC<{
  salesman: any;
  isOpen: boolean;
  onClose: () => void;
  onSettle: (salesmanId: number, notes?: string) => void;
  isSettling: number | null;
}> = ({ salesman, isOpen, onClose, onSettle, isSettling }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {salesman.salesman.name}
              </h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                <span className="flex items-center">
                  <Phone className="w-4 h-4 mr-1" />
                  {salesman.salesman.phone}
                </span>
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {salesman.salesman.email}
                </span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {salesman.current_stock.total_value > 0 && (
                <button
                  onClick={() => onSettle(salesman.salesman.id)}
                  disabled={isSettling === salesman.salesman.id}
                  className="btn btn-primary btn-sm flex items-center space-x-1"
                >
                  {isSettling === salesman.salesman.id ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Calculator className="w-4 h-4" />
                  )}
                  <span>Settle All</span>
                </button>
              )}
              <button onClick={onClose} className="btn btn-outline btn-sm">
                Close
              </button>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Current Stock */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Current Stock</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {salesman.current_stock.total_products}
                  </p>
                  <p className="text-sm text-gray-600">Products</p>
                </div>
              </div>
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {salesman.current_stock.total_quantity}
                  </p>
                  <p className="text-sm text-gray-600">Items</p>
                </div>
              </div>
              <div className="card p-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    LKR {salesman.current_stock.total_value.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">Value</p>
                </div>
              </div>
            </div>

            {salesman.current_stock.products.length > 0 && (
              <div className="card">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          SKU
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Unit Price
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total Value
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {salesman.current_stock.products.map((product: any) => (
                        <tr key={product.product_id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {product.product_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {product.product_sku}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {product.quantity}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            LKR {product.unit_price.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            LKR {product.total_value.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Delivery Summary */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">Delivery Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card p-4 text-center">
                <p className="text-xl font-bold text-gray-900">
                  {salesman.deliveries.total_count}
                </p>
                <p className="text-sm text-gray-600">Total</p>
              </div>
              <div className="card p-4 text-center">
                <p className="text-xl font-bold text-yellow-600">
                  {salesman.deliveries.pending_count}
                </p>
                <p className="text-sm text-gray-600">Pending</p>
              </div>
              <div className="card p-4 text-center">
                <p className="text-xl font-bold text-green-600">
                  {salesman.deliveries.delivered_count}
                </p>
                <p className="text-sm text-gray-600">Delivered</p>
              </div>
              <div className="card p-4 text-center">
                <p className="text-xl font-bold text-blue-600">
                  {salesman.deliveries.settled_count}
                </p>
                <p className="text-sm text-gray-600">Settled</p>
              </div>
            </div>
          </div>

          {/* Performance Chart */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              Sales Performance (Last 30 Days)
            </h3>
            <div className="card p-4">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center">
                  <p className="text-xl font-bold text-green-600">
                    LKR {salesman.sales_performance.total_revenue_30d.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">Total Revenue</p>
                </div>
                <div className="text-center">
                  <p className="text-xl font-bold text-blue-600">
                    {salesman.sales_performance.total_quantity_30d}
                  </p>
                  <p className="text-sm text-gray-600">Items Sold</p>
                </div>
              </div>
              
              {salesman.sales_performance.last_30_days.length > 0 ? (
                <div className="text-sm text-gray-600">
                  <p>Recent daily sales available</p>
                  <p>Best day: {Math.max(...salesman.sales_performance.last_30_days.map((d: any) => d.daily_revenue))} LKR</p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">No sales data for the last 30 days</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
