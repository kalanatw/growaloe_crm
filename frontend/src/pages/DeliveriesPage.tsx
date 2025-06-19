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
  DollarSign
} from 'lucide-react';
import { deliveryService, salesmanService } from '../services/apiServices';
import { Delivery, Salesman } from '../types';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { CreateDeliveryModal } from '../components/CreateDeliveryModal';
import { SettlementModal } from '../components/SettlementModal';

export const DeliveriesPage: React.FC = () => {
  const { user } = useAuth();
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [salesmen, setSalesmen] = useState<Salesman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedDelivery, setSelectedDelivery] = useState<Delivery | null>(null);
  const [settlementDeliveryId, setSettlementDeliveryId] = useState<number | null>(null);

  useEffect(() => {
    loadData();
    
    // Set up real-time updates every 30 seconds, but pause when modals are open
    const interval = setInterval(() => {
      // Don't auto-refresh if any modal is open to avoid interrupting user interactions
      if (!isCreateModalOpen && !selectedDelivery && !settlementDeliveryId) {
        loadData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isCreateModalOpen, selectedDelivery, settlementDeliveryId]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [deliveriesData, salesmenData] = await Promise.all([
        deliveryService.getDeliveries(),
        salesmanService.getSalesmen(),
      ]);
      
      setDeliveries(deliveriesData.results);
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
      loadData(); // Reload the deliveries
    } catch (error: any) {
      console.error('Error creating delivery:', error);
      toast.error(error.response?.data?.detail || 'Failed to create delivery');
    }
  };

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

  if (isLoading) {
    return (
      <Layout title="Deliveries">
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout title="Product Deliveries">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Product Deliveries</h1>
            <p className="text-gray-600">Manage product allocations to salesmen</p>
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

        {/* Deliveries Grid */}
        {deliveries.length === 0 ? (
          <div className="text-center py-12">
            <Truck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No deliveries yet</h3>
            <p className="text-gray-600 mb-6">Start by creating your first product delivery to salesmen</p>
            {user?.role === 'owner' && (
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="btn btn-primary"
              >
                Create First Delivery
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {deliveries.map((delivery) => (
              <DeliveryCard
                key={delivery.id}
                delivery={delivery}
                user={user}
                onViewDetails={setSelectedDelivery}
                onMarkAsDelivered={handleMarkAsDelivered}
                onStartSettlement={setSettlementDeliveryId}
                getStatusBadge={getStatusBadge}
              />
            ))}
          </div>
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

        {/* Settlement Modal */}
        {settlementDeliveryId && (
          <SettlementModal
            deliveryId={settlementDeliveryId}
            isOpen={!!settlementDeliveryId}
            onClose={() => setSettlementDeliveryId(null)}
            onSettled={handleSettlementCompleted}
          />
        )}

        {/* Delivery Details Modal */}
        {selectedDelivery && (
          <DeliveryDetailsModal
            delivery={selectedDelivery}
            isOpen={!!selectedDelivery}
            onClose={() => setSelectedDelivery(null)}
          />
        )}
      </div>
    </Layout>
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
