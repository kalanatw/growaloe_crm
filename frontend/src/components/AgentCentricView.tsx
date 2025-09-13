import React, { useState, useEffect } from 'react';
import { Package, DollarSign, RotateCcw, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { agentService } from '../services/apiServices';
import toast from 'react-hot-toast';

interface AgentCentricViewProps {
  agents: any[];
  onProcessPayment: (agentId: number, deliveryId: number, paymentData: any) => void;
  onCreateReturn: (returnData: any) => void;
  onApproveReturn: (returnId: number) => void;
  onRejectReturn: (returnId: number, reason: string) => void;
}

export const AgentCentricView: React.FC<AgentCentricViewProps> = ({
  agents,
  onProcessPayment,
  onCreateReturn,
  onApproveReturn,
  onRejectReturn,
}) => {
  const [selectedTab, setSelectedTab] = useState<'deliveries' | 'returns' | 'balances'>('deliveries');
  const [agentDeliveries, setAgentDeliveries] = useState<any[]>([]);
  const [agentReturns, setAgentReturns] = useState<any[]>([]);
  const [agentBalances, setAgentBalances] = useState<any[]>([]);
  const [paymentSummary, setPaymentSummary] = useState<any>(null);
  const [returnsSummary, setReturnsSummary] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadAgentData();
  }, [selectedTab]);

  const loadAgentData = async () => {
    setIsLoading(true);
    try {
      switch (selectedTab) {
        case 'deliveries':
          const [deliveriesData, paymentData] = await Promise.all([
            agentService.getAgentDeliveries(),
            agentService.getAgentPaymentSummary()
          ]);
          setAgentDeliveries(deliveriesData.results);
          setPaymentSummary(paymentData);
          break;
        
        case 'returns':
          const [returnsData, returnsSummaryData] = await Promise.all([
            agentService.getAgentReturns(),
            agentService.getAgentReturnsSummary()
          ]);
          setAgentReturns(returnsData.results);
          setReturnsSummary(returnsSummaryData);
          break;
        
        case 'balances':
          // Load agent balances
          const balancePromises = agents
            .filter(agent => agent.salesman_type === 'agent')
            .map(agent => agentService.getAgentBalance(agent.id));
          const balances = await Promise.all(balancePromises);
          setAgentBalances(balances);
          break;
      }
    } catch (error) {
      console.error('Error loading agent data:', error);
      toast.error('Failed to load agent data');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePaymentProcess = async (agentId: number, deliveryId: number, amount: number) => {
    try {
      await onProcessPayment(agentId, deliveryId, {
        payment_amount: amount,
        payment_method: 'cash',
        notes: 'Payment processed from agent view'
      });
      toast.success('Payment processed successfully');
      loadAgentData();
    } catch (error) {
      console.error('Error processing payment:', error);
      toast.error('Failed to process payment');
    }
  };

  const getPaymentStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'text-green-600 bg-green-100';
      case 'partial': return 'text-yellow-600 bg-yellow-100';
      case 'pending': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getReturnStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'text-green-600 bg-green-100';
      case 'rejected': return 'text-red-600 bg-red-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'processed': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Agent Management</h2>
            <p className="text-sm text-gray-600">Manage agent deliveries, payments, and returns</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 text-sm text-orange-600">
              <Package className="w-4 h-4" />
              <span>{agents.filter(a => a.salesman_type === 'agent').length} Agents</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {[
            { key: 'deliveries', label: 'Deliveries & Payments', icon: Package },
            { key: 'returns', label: 'Returns', icon: RotateCcw },
            { key: 'balances', label: 'Agent Balances', icon: DollarSign },
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setSelectedTab(key as any)}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                selectedTab === key
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
          </div>
        ) : (
          <>
            {selectedTab === 'deliveries' && (
              <div className="space-y-6">
                {/* Payment Summary */}
                {paymentSummary && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <Package className="w-8 h-8 text-blue-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-blue-900">Total Deliveries</p>
                          <p className="text-2xl font-bold text-blue-600">{paymentSummary.total_deliveries}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <DollarSign className="w-8 h-8 text-green-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-green-900">Total Amount</p>
                          <p className="text-2xl font-bold text-green-600">LKR {paymentSummary.total_amount?.toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <Clock className="w-8 h-8 text-yellow-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-yellow-900">Pending Payments</p>
                          <p className="text-2xl font-bold text-yellow-600">
                            {paymentSummary.by_status?.find((s: any) => s.agent_payment_status === 'pending')?.count || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <CheckCircle className="w-8 h-8 text-green-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-green-900">Paid Deliveries</p>
                          <p className="text-2xl font-bold text-green-600">
                            {paymentSummary.by_status?.find((s: any) => s.agent_payment_status === 'paid')?.count || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Agent Deliveries List */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Agent Deliveries</h3>
                  {agentDeliveries.length === 0 ? (
                    <div className="text-center py-12">
                      <Package className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No agent deliveries</h3>
                      <p className="mt-1 text-sm text-gray-500">Create a delivery for an agent to get started.</p>
                    </div>
                  ) : (
                    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                      <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Delivery
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Agent
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Amount
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Payment Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Date
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {agentDeliveries.map((delivery) => (
                            <tr key={delivery.id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {delivery.delivery_number}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {delivery.salesman_name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                LKR {delivery.agent_purchase_amount?.toFixed(2)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPaymentStatusColor(delivery.agent_payment_status)}`}>
                                  {delivery.agent_payment_status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(delivery.delivery_date).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                {delivery.agent_payment_status === 'pending' && (
                                  <button
                                    onClick={() => handlePaymentProcess(delivery.salesman, delivery.id, delivery.agent_purchase_amount)}
                                    className="text-orange-600 hover:text-orange-900"
                                  >
                                    Process Payment
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === 'returns' && (
              <div className="space-y-6">
                {/* Returns Summary */}
                {returnsSummary && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-yellow-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <AlertCircle className="w-8 h-8 text-yellow-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-yellow-900">Pending Returns</p>
                          <p className="text-2xl font-bold text-yellow-600">{returnsSummary.total_pending}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-red-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <DollarSign className="w-8 h-8 text-red-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-red-900">Total Amount</p>
                          <p className="text-2xl font-bold text-red-600">LKR {returnsSummary.total_amount?.toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="flex items-center">
                        <RotateCcw className="w-8 h-8 text-blue-600" />
                        <div className="ml-3">
                          <p className="text-sm font-medium text-blue-900">Return Requests</p>
                          <p className="text-2xl font-bold text-blue-600">{agentReturns.length}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Agent Returns List */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Agent Returns</h3>
                  {agentReturns.length === 0 ? (
                    <div className="text-center py-12">
                      <RotateCcw className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">No agent returns</h3>
                      <p className="mt-1 text-sm text-gray-500">Agent return requests will appear here.</p>
                    </div>
                  ) : (
                    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                      <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Return #
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Agent
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Product
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Quantity
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Amount
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Status
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {agentReturns.map((returnItem) => (
                            <tr key={returnItem.id}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {returnItem.return_number}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {returnItem.agent_name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {returnItem.product_name}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {returnItem.quantity}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                LKR {returnItem.return_amount?.toFixed(2)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getReturnStatusColor(returnItem.status)}`}>
                                  {returnItem.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                {returnItem.status === 'pending' && (
                                  <div className="flex space-x-2">
                                    <button
                                      onClick={() => onApproveReturn(returnItem.id)}
                                      className="text-green-600 hover:text-green-900"
                                    >
                                      Approve
                                    </button>
                                    <button
                                      onClick={() => onRejectReturn(returnItem.id, 'Rejected by owner')}
                                      className="text-red-600 hover:text-red-900"
                                    >
                                      Reject
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedTab === 'balances' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Agent Balances</h3>
                {agentBalances.length === 0 ? (
                  <div className="text-center py-12">
                    <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No agent balances</h3>
                    <p className="mt-1 text-sm text-gray-500">Agent balance information will appear here.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {agentBalances.map((balance) => (
                      <div key={balance.agent_id} className="bg-white border border-gray-200 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-lg font-medium text-gray-900">{balance.agent_name}</h4>
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                            Agent
                          </span>
                        </div>
                        
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Current Balance:</span>
                            <span className="text-sm font-medium text-gray-900">LKR {balance.current_balance?.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Total Purchases:</span>
                            <span className="text-sm font-medium text-gray-900">LKR {balance.total_purchases?.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Total Returns:</span>
                            <span className="text-sm font-medium text-gray-900">LKR {balance.total_returns?.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Net Position:</span>
                            <span className={`text-sm font-medium ${balance.net_position >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              LKR {balance.net_position?.toFixed(2)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Pending Deliveries:</span>
                            <span className="text-sm font-medium text-gray-900">{balance.pending_deliveries_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">Pending Returns:</span>
                            <span className="text-sm font-medium text-gray-900">{balance.pending_returns_count}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};