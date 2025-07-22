import React, { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Plus, Users, Package, Calculator, DollarSign, BarChart3, Eye, CheckCircle, Mail, AlertTriangle, TrendingUp, ArrowRight } from 'lucide-react';
import { deliveryService, salesmanService } from '../services/apiServices';
import toast from 'react-hot-toast';
import { useAuth } from '../contexts/AuthContext';
import { CreateDeliveryModal } from '../components/CreateDeliveryModal';

export const DeliveriesPage: React.FC = () => {
  const { user } = useAuth();
  const [salesmanOverview, setSalesmanOverview] = useState<any>(null);
  const [settlementQueue, setSettlementQueue] = useState<any>(null);
  const [dailySummary, setDailySummary] = useState<any>(null);
  const [selectedView, setSelectedView] = useState<'overview' | 'settlement' | 'summary'>('overview');
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

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (!isCreateModalOpen && !selectedSalesman) {
        loadData();
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [isCreateModalOpen, selectedSalesman]);

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

  const handleSettleSalesman = async (salesmanId: number, settlement_notes: string = '') => {
    try {
      setIsSettling(salesmanId);
      const result = await deliveryService.settleSalesmanDeliveries(salesmanId, {
        settlement_notes,
        return_all_stock: true,
        create_settlement_record: true
      });
      toast.success(`Settlement completed for ${result.salesman_name}!`);
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
      const [deliveriesRes, settlementsRes] = await Promise.all([
        fetch(`/api/products/deliveries/?salesman=${salesman.salesman_id}`),
        fetch(`/api/products/delivery-settlements/?salesman=${salesman.salesman_id}`)
      ]);
      const deliveriesData = await deliveriesRes.json();
      const settlementsData = await settlementsRes.json();
      setHistoryDeliveries(deliveriesData.results || deliveriesData);
      setHistorySettlements(settlementsData.results || settlementsData);
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

  if (isLoading) {
    return (
      <Layout title="Deliveries">
        <LoadingSpinner />
      </Layout>
    );
  }

  return (
    <Layout title="Salesman-Centric Delivery Management">
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Delivery Management</h1>
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
          onSettleSalesman={handleSettleSalesman}
          isSettling={isSettling}
          onShowHistory={handleShowHistoryModal}
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
        {historyModalSalesman && (
          <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
            <div className="bg-white rounded-lg p-2 sm:p-4 md:p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-4xl">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">History - {historyModalSalesman.salesman_name || historyModalSalesman.name}</h3>
                <button className="btn btn-outline btn-sm" onClick={handleCloseHistoryModal}>Close</button>
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
              {isHistoryLoading ? (
                <div className="text-center py-8">Loading...</div>
              ) : historyTab === 'deliveries' ? (
                historyDeliveries.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No deliveries found.</div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200 mb-6 overflow-x-auto">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivery #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Total Value</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Expenses</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {historyDeliveries.map((delivery: any, idx: number) => (
                        <React.Fragment key={delivery.id}>
                          <tr>
                            <td className="px-4 py-2 text-sm">{delivery.delivery_number}</td>
                            <td className="px-4 py-2 text-sm">{new Date(delivery.delivery_date).toLocaleDateString()}</td>
                            <td className="px-4 py-2 text-sm">{delivery.status}</td>
                            <td className="px-4 py-2 text-sm">LKR {Number(delivery.total_value).toFixed(2)}</td>
                            <td className="px-4 py-2 text-sm">
                              {delivery.expenses && delivery.expenses.length > 0 ? (
                                <button
                                  className="btn btn-xs btn-outline"
                                  onClick={() => setHistoryDeliveries((prev: any[]) => prev.map((d, i) => i === idx ? { ...d, _showExpenses: !d._showExpenses } : d))}
                                >
                                  {delivery._showExpenses ? 'Hide' : 'Show'} ({delivery.expenses.length})
                                </button>
                              ) : (
                                <span className="text-gray-400">None</span>
                              )}
                            </td>
                          </tr>
                          {delivery._showExpenses && delivery.expenses && delivery.expenses.length > 0 && (
                            <tr>
                              <td colSpan={5} className="px-4 pb-4">
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
                )
              ) : (
                historySettlements.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No settlements found.</div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200 mb-6 overflow-x-auto">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Settlement #</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivered</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sold</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Returned</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {historySettlements.map((settlement: any) => (
                        <tr key={settlement.id}>
                          <td className="px-4 py-2 text-sm">{settlement.settlement_number}</td>
                          <td className="px-4 py-2 text-sm">{new Date(settlement.settlement_date).toLocaleDateString()}</td>
                          <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_delivered_value).toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_sold_value).toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm">LKR {Number(settlement.total_returned_value).toFixed(2)}</td>
                          <td className="px-4 py-2 text-sm">{settlement.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )
              )}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
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
  onShowHistory: (salesman: any) => void;
}> = ({ 
  salesmanOverview, 
  settlementQueue, 
  dailySummary, 
  selectedView, 
  setSelectedView, 
  onViewSalesmanDetails, 
  onSettleSalesman, 
  isSettling, 
  onShowHistory 
}) => {
  const { user } = useAuth();
  const [salesmen, setSalesmen] = useState<any[]>([]);
  const [isSalesmenLoading, setIsSalesmenLoading] = useState(false);
  useEffect(() => {
    setIsSalesmenLoading(true);
    import('../services/apiServices').then(({ salesmanService }) => {
      salesmanService.getSalesmen().then((data: any) => {
        setSalesmen(data.results || data);
        setIsSalesmenLoading(false);
      }).catch(() => setIsSalesmenLoading(false));
    });
  }, []);

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
                {`LKR ${(
                  (salesmanOverview?.salesmen?.reduce((sum: number, s: any) =>
                    sum + (s.stock_by_product?.reduce((pSum: number, p: any) => pSum + (p.quantity * Number(p.unit_price || 0)), 0) || 0)
                  , 0) || 0)
                ).toFixed(2)}`}
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
            { id: 'settlement', label: 'Settlement History', icon: Calculator },
           
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
          onShowHistory={onShowHistory}
        />
      )}

      {selectedView === 'settlement' && (
        <SettlementHistoryFull
          salesmen={salesmen}
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

// Salesman Stock Overview Component
const SalesmanStockOverview: React.FC<{
  data: any;
  onViewDetails: (salesmanId: number) => void;
  onShowHistory: (salesman: any) => void;
}> = ({ data, onViewDetails, onShowHistory }) => {
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
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h3
                  className="font-semibold text-gray-900 cursor-pointer hover:underline"
                  onClick={() => onShowHistory(salesman)}
                >
                  {salesman.salesman_name}
                </h3>
                <p className="text-sm text-gray-600 flex items-center">
                  <Mail className="w-3 h-3 mr-1" />
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
                {`LKR ${(
                  salesman.stock_by_product.reduce((sum: number, p: any) => sum + (p.quantity * Number(p.unit_price || 0)), 0)
                ).toFixed(2)}`}
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
                      <span className="text-gray-700 ml-2">
                        LKR {Number(product.unit_price || 0).toFixed(2)}
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
interface SalesmanDetailsModalProps {
  salesman: any;
  isOpen: boolean;
  onClose: () => void;
  onSettle: (salesmanId: number, notes?: string, deliveryId?: number, netCash?: number) => void;
  isSettling: number | null;
  activeDeliveryId?: number;
  user: any;
}

const SalesmanDetailsModal: React.FC<SalesmanDetailsModalProps> = function SalesmanDetailsModal({
  salesman,
  isOpen,
  onClose,
  onSettle,
  isSettling,
  activeDeliveryId,
  user
}) {
  // Always show details for the active delivery (default to most recent)
  const deliveryList = salesman.deliveries?.recent_deliveries || [];
  const defaultDeliveryId = activeDeliveryId || (deliveryList.length > 0 ? deliveryList[0].id : null);
  const [expenses, setExpenses] = useState<any[]>([]);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<any | null>(null);
  const [expenseForm, setExpenseForm] = useState({
    category: '',
    amount: '',
    ref_id: '',
    notes: ''
  });
  const [expenseError, setExpenseError] = useState('');
  const expenseCategories = [
    { value: 'food', label: 'Food' },
    { value: 'transportation', label: 'Transportation' },
    { value: 'labour', label: 'Labour' },
    { value: 'accommodation', label: 'Accommodation' },
    { value: 'other', label: 'Other' },
  ];
  const isOwner = user?.role === 'owner';
  const [isSavingExpense, setIsSavingExpense] = useState(false);
  const categoryRef = React.useRef<HTMLSelectElement>(null);

  // Find the active delivery object
  const activeDelivery = deliveryList.find((d: any) => d.id === defaultDeliveryId) || null;

  // Load expenses for the active delivery
  useEffect(() => {
    if (activeDelivery) {
      deliveryService.getDeliveryExpenses(activeDelivery.id).then((res: any) => {
        setExpenses(res.results || res);
      });
    }
  }, [activeDelivery?.id]);

  useEffect(() => {
    if (isExpenseModalOpen && categoryRef.current) {
      categoryRef.current.focus();
    }
  }, [isExpenseModalOpen]);

  const handleOpenAddExpense = () => {
    setEditingExpense(null);
    setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
    setExpenseError('');
    setIsExpenseModalOpen(true);
  };
  const handleOpenEditExpense = (expense: any) => {
    setEditingExpense(expense);
    setExpenseForm({
      category: expense.category,
      amount: expense.amount.toString(),
      ref_id: expense.ref_id || '',
      notes: expense.notes || ''
    });
    setExpenseError('');
    setIsExpenseModalOpen(true);
  };
  const handleCloseExpenseModal = () => {
    setIsExpenseModalOpen(false);
    setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
    setExpenseError('');
    setEditingExpense(null);
  };
  const handleDeleteExpense = async (id: number) => {
    if (!window.confirm('Delete this expense?')) return;
    try {
      await deliveryService.deleteDeliveryExpense(id);
      setExpenses((prev) => prev.filter((e: any) => e.id !== id));
      toast.success('Expense deleted');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to delete expense');
    }
  };
  const handleExpenseFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    if (e.target.name === 'amount') {
      // Prevent negative values
      if (e.target.value && parseFloat(e.target.value) < 0) return;
    }
    setExpenseForm({ ...expenseForm, [e.target.name]: e.target.value });
  };
  const handleSaveExpense = async () => {
    setExpenseError('');
    if (!expenseForm.category) {
      setExpenseError('Category is required');
      return;
    }
    const amount = parseFloat(expenseForm.amount);
    if (!amount || amount <= 0) {
      setExpenseError('Amount must be greater than zero');
      return;
    }
    if (!activeDelivery) {
      setExpenseError('No delivery selected');
      return;
    }
    const data = {
      delivery: activeDelivery.id,
      category: expenseForm.category,
      amount,
      ref_id: expenseForm.ref_id || undefined,
      notes: expenseForm.notes || undefined
    };
    setIsSavingExpense(true);
    try {
      if (editingExpense) {
        const updated = await deliveryService.updateDeliveryExpense(editingExpense.id, data) as any;
        setExpenses((prev) => prev.map((e: any) => e.id === editingExpense.id ? updated : e));
        toast.success('Expense updated');
      } else {
        const created = await deliveryService.createDeliveryExpense(data) as any;
        setExpenses((prev) => [...prev, created]);
        toast.success('Expense added');
      }
      setIsExpenseModalOpen(false);
      setExpenseForm({ category: '', amount: '', ref_id: '', notes: '' });
      setEditingExpense(null);
    } catch (err: any) {
      setExpenseError(err.response?.data?.detail || 'Failed to save expense');
    } finally {
      setIsSavingExpense(false);
    }
  };

  if (!isOpen || !activeDelivery) return null;

  const deliveryTotal = activeDelivery.items?.reduce((sum: number, item: any) => sum + (item.quantity * Number(item.unit_price || 0)), 0) || 0;
  const totalExpenses = expenses.reduce((sum: number, e: any) => sum + Number(e.amount), 0);
  const netCash = deliveryTotal - totalExpenses;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                {salesman.salesman.name}
              </h2>
              <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {salesman.salesman.phone}
                </span>
                <span className="flex items-center">
                  <Mail className="w-4 h-4 mr-1" />
                  {salesman.salesman.email}
                </span>
              </div>
            </div>
            <button onClick={onClose} className="btn btn-outline btn-sm">
              Close
            </button>
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
                            LKR {Number(product.unit_price || 0).toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            LKR {(product.quantity * Number(product.unit_price || 0)).toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Delivery Expense Management Section - Only for active delivery */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Delivery Expense Management</h3>
            <div className="flex items-center mb-2">
              <h4 className="text-md font-semibold flex items-center mb-0">Expenses</h4>
              {isOwner && (
                <button className="ml-4 btn btn-outline btn-xs" onClick={handleOpenAddExpense}>Add Expense</button>
              )}
            </div>
            {expenses.length === 0 ? (
              <p className="text-gray-500">No expenses recorded for this delivery.</p>
            ) : (
              <div className="overflow-x-auto mb-2">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivery ID</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Ref ID</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                      {isOwner && <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {expenses.map((exp: any) => (
                      <tr key={exp.id}>
                        <td className="px-4 py-2 text-sm">{exp.delivery}</td>
                        <td className="px-4 py-2 text-sm">{expenseCategories.find(c => c.value === exp.category)?.label || exp.category}</td>
                        <td className="px-4 py-2 text-sm">LKR {Number(exp.amount).toFixed(2)}</td>
                        <td className="px-4 py-2 text-sm">{exp.ref_id || '-'}</td>
                        <td className="px-4 py-2 text-sm">{exp.notes || '-'}</td>
                        {isOwner && <td className="px-4 py-2 text-sm">
                          <button className="btn btn-xs btn-outline mr-2" onClick={() => handleOpenEditExpense(exp)}>Edit</button>
                          <button className="btn btn-xs btn-danger" onClick={() => handleDeleteExpense(exp.id)}>Delete</button>
                        </td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="flex flex-col items-end space-y-2 mt-2">
              <div className="font-medium text-gray-700">Total Expenses: <span className="font-bold">LKR {totalExpenses.toFixed(2)}</span></div>
              <div className={`font-medium ${netCash < 0 ? 'text-red-600' : 'text-green-700'}`}>Net Cash to Collect: <span className="font-bold">LKR {netCash.toFixed(2)}</span></div>
              {isOwner && (
                <button
                  className="btn btn-primary mt-2"
                  disabled={isSettling === activeDelivery.id}
                  onClick={() => onSettle(salesman.salesman.id, '', activeDelivery.id, netCash)}
                >
                  {isSettling === activeDelivery.id ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <Calculator className="w-4 h-4" />
                  )}
                  <span>Settle Delivery</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Expense Modal */}
        {isExpenseModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto flex flex-col justify-start lg:items-center lg:justify-center z-50">
            <div className="bg-white rounded-lg p-2 sm:p-4 md:p-6 w-full h-auto lg:max-h-[90vh] lg:overflow-y-auto max-w-md">
              <h3 className="text-lg font-semibold mb-4">{editingExpense ? 'Edit Expense' : 'Add Expense'}</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                  <select
                    name="category"
                    value={expenseForm.category}
                    onChange={handleExpenseFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    ref={categoryRef}
                  >
                    <option value="">Select Category</option>
                    {expenseCategories.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
                  <input
                    name="amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={expenseForm.amount}
                    onChange={handleExpenseFormChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ref ID</label>
                  <input name="ref_id" type="text" value={expenseForm.ref_id} onChange={handleExpenseFormChange} className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <textarea name="notes" value={expenseForm.notes} onChange={handleExpenseFormChange} className="w-full px-3 py-2 border border-gray-300 rounded-md" />
                </div>
                {expenseError && <div className="text-red-600 text-sm">{expenseError}</div>}
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button className="btn btn-outline" onClick={handleCloseExpenseModal} disabled={isSavingExpense}>Cancel</button>
                <button className="btn btn-primary" onClick={handleSaveExpense} disabled={isSavingExpense}>{editingExpense ? 'Update' : 'Add'}</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Add the SettlementHistoryFull component
const SettlementHistoryFull: React.FC<{ salesmen: any[] }> = ({ salesmen }) => {
  const [selectedSalesman, setSelectedSalesman] = useState<any | null>(null);
  const [settlements, setSettlements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedSalesman) {
      setIsLoading(true);
      setError(null);
      deliveryService.getSettlementHistory(selectedSalesman.id)
        .then((data: any) => setSettlements(data.results || data))
        .catch(() => setError('Failed to load settlement history.'))
        .finally(() => setIsLoading(false));
    } else {
      setSettlements([]);
    }
  }, [selectedSalesman]);

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-4 flex items-center space-x-2">
        <label className="font-medium text-gray-700">Select Salesman:</label>
        <select
          className="border px-2 py-1 rounded"
          value={selectedSalesman?.id || ''}
          onChange={e => {
            const id = Number(e.target.value) || null;
            setSelectedSalesman(salesmen.find(s => s.id === id) || null);
          }}
        >
          <option value="">-- Select --</option>
          {salesmen.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>
      {isLoading ? (
        <div className="text-center py-8"><LoadingSpinner /></div>
      ) : error ? (
        <div className="text-center text-red-600 py-8">{error}</div>
      ) : settlements.length === 0 && selectedSalesman ? (
        <div className="text-center py-8 text-gray-500">No settlements found for this salesman.</div>
      ) : settlements.length === 0 ? (
        <div className="text-center py-8 text-gray-500">Please select a salesman to view settlement history.</div>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 mb-6 overflow-x-auto">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Settlement #</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Delivered</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sold</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Returned</th>
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
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
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
