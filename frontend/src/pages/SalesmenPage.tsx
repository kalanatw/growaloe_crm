import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { 
  Plus, 
  Users, 
  Edit, 
  ToggleLeft, 
  ToggleRight, 
  Phone, 
  Mail, 
  MapPin, 
  Calendar,
  DollarSign,
  Package,
  Filter
} from 'lucide-react';
import { salesmanService } from '../services/apiServices';
import { Salesman } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { USER_ROLES } from '../config/constants';
import toast from 'react-hot-toast';

export const SalesmenPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [salesmen, setSalesmen] = useState<Salesman[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterType, setFilterType] = useState<'all' | 'employee' | 'agent'>('all');

  useEffect(() => {
    loadSalesmen();
  }, []);

  const loadSalesmen = async () => {
    try {
      setIsLoading(true);
      const response = await salesmanService.getSalesmen();
      setSalesmen(response.results);
    } catch (error: any) {
      console.error('Error loading salesmen:', error);
      toast.error('Failed to load salesmen');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleStatus = async (id: number, currentStatus: boolean) => {
    try {
      await salesmanService.toggleSalesmanStatus(id, !currentStatus);
      toast.success(`Salesman ${!currentStatus ? 'activated' : 'deactivated'} successfully`);
      loadSalesmen();
    } catch (error: any) {
      console.error('Error toggling salesman status:', error);
      toast.error('Failed to update salesman status');
    }
  };

  // Only allow owners to access this page
  if (user?.role !== USER_ROLES.OWNER) {
    return (
      <Layout title="Access Denied">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Access Denied
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Only owners can manage salesmen.
          </p>
        </div>
      </Layout>
    );
  }

  if (isLoading) {
    return (
      <Layout title="Manage Salesmen">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Manage Salesmen">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Users className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Manage Salesmen
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                View and manage your sales team
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/salesmen/create')}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Salesman</span>
          </button>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Total Salesmen
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {salesmen.length}
                </p>
              </div>
              <Users className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Employees
                </p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {salesmen.filter(s => s.salesman_type === 'employee' || !s.salesman_type).length}
                </p>
              </div>
              <Users className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Agents
                </p>
                <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {salesmen.filter(s => s.salesman_type === 'agent').length}
                </p>
              </div>
              <Package className="h-8 w-8 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Active
                </p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {salesmen.filter(s => s.is_active).length}
                </p>
              </div>
              <ToggleRight className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Inactive
                </p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {salesmen.filter(s => !s.is_active).length}
                </p>
              </div>
              <ToggleLeft className="h-8 w-8 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by type:</span>
            </div>
            <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setFilterType('all')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  filterType === 'all'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterType('employee')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  filterType === 'employee'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Employees
              </button>
              <button
                onClick={() => setFilterType('agent')}
                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                  filterType === 'agent'
                    ? 'bg-orange-600 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Agents
              </button>
            </div>
          </div>
        </div>

        {/* Salesmen List */}
        {(() => {
          const filteredSalesmen = salesmen.filter(salesman => {
            if (filterType === 'all') return true;
            if (filterType === 'employee') return salesman.salesman_type === 'employee' || !salesman.salesman_type;
            if (filterType === 'agent') return salesman.salesman_type === 'agent';
            return true;
          });

          return filteredSalesmen.length === 0 ? (
          <div className="card p-12 text-center">
            <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Salesmen Found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              You haven't added any salesmen yet. Create your first salesman to get started.
            </p>
            <button
              onClick={() => navigate('/salesmen/create')}
              className="btn-primary"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add First Salesman
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredSalesmen.map((salesman) => (
              <div
                key={salesman.id}
                className="card p-6 hover:shadow-lg transition-shadow duration-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                      <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {salesman.name}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {salesman.user.username}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {/* Salesman Type Badge */}
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        salesman.salesman_type === 'agent'
                          ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                          : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                      }`}
                    >
                      {salesman.salesman_type === 'agent' ? (
                        <>
                          <Package className="h-3 w-3 mr-1" />
                          Agent
                        </>
                      ) : (
                        <>
                          <Users className="h-3 w-3 mr-1" />
                          Employee
                        </>
                      )}
                    </span>
                    {/* Active Status Badge */}
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        salesman.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      }`}
                    >
                      {salesman.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>

                <div className="space-y-3 mb-4">
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Mail className="h-4 w-4 mr-2" />
                    {salesman.user.email}
                  </div>
                  {salesman.user.phone && (
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <Phone className="h-4 w-4 mr-2" />
                      {salesman.user.phone}
                    </div>
                  )}
                  {salesman.user.address && (
                    <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                      <MapPin className="h-4 w-4 mr-2" />
                      {salesman.user.address}
                    </div>
                  )}
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <DollarSign className="h-4 w-4 mr-2" />
                    Profit Margin: {salesman.profit_margin}%
                  </div>
                  <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                    <Calendar className="h-4 w-4 mr-2" />
                    Joined: {new Date(salesman.created_at).toLocaleDateString()}
                  </div>
                </div>

                {salesman.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {salesman.description}
                  </p>
                )}

                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => navigate(`/salesmen/${salesman.id}/edit`)}
                    className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 text-sm font-medium flex items-center"
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleStatus(salesman.id, salesman.is_active)}
                    className={`text-sm font-medium flex items-center ${
                      salesman.is_active
                        ? 'text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300'
                        : 'text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300'
                    }`}
                  >
                    {salesman.is_active ? (
                      <>
                        <ToggleLeft className="h-4 w-4 mr-1" />
                        Deactivate
                      </>
                    ) : (
                      <>
                        <ToggleRight className="h-4 w-4 mr-1" />
                        Activate
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        );
        })()}
      </div>
    </Layout>
  );
};
