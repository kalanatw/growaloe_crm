import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { RotateCcw, AlertTriangle, Package, ArrowRight, Clock, CheckCircle } from 'lucide-react';
import returnService, { PendingReturnsSummary } from '../services/returnService';
import toast from 'react-hot-toast';

interface ReturnsSummaryCardProps {
  salesmanId?: number;
  salesmanName?: string;
  className?: string;
}

export const ReturnsSummaryCard: React.FC<ReturnsSummaryCardProps> = ({ 
  salesmanId, 
  salesmanName,
  className = '' 
}) => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<PendingReturnsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReturnsSummary();
  }, [salesmanId]);

  const loadReturnsSummary = async () => {
    try {
      setLoading(true);
      const data = await returnService.getPendingReturnsSummary();
      setSummary(data);
    } catch (error) {
      console.error('Error loading returns summary:', error);
      toast.error('Failed to load returns summary');
    } finally {
      setLoading(false);
    }
  };

  const handleNavigateToReturns = () => {
    const params = new URLSearchParams();
    if (salesmanId) {
      params.append('salesman', salesmanId.toString());
    }
    params.append('status', 'pending');
    
    const url = `/returns${params.toString() ? `?${params.toString()}` : ''}`;
    navigate(url);
  };

  if (loading) {
    return (
      <div className={`card p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-gray-200 rounded-lg"></div>
            <div className="h-6 bg-gray-200 rounded w-32"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!summary || !summary.pending_returns || summary.pending_returns.total_pending === 0) {
    return (
      <div className={`card p-6 border-l-4 border-green-500 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Returns Status
              </h3>
              <p className="text-sm text-green-600">
                {salesmanName ? `${salesmanName} has no pending returns` : 'No pending returns'}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Filter summary for specific salesman if provided
  const salesmanReturns = salesmanId 
    ? summary.pending_returns.by_salesman.find((s: any) => s.salesman_id === salesmanId)
    : null;

  const displayData = salesmanReturns || {
    pending_count: summary.pending_returns.total_pending,
    pending_quantity: summary.pending_returns.total_quantity
  };

  const hasUrgentReturns = summary.pending_returns.by_reason.damaged?.count > 0 || summary.pending_returns.by_reason.expired?.count > 0;

  return (
    <div className={`card p-6 border-l-4 ${hasUrgentReturns ? 'border-red-500' : 'border-orange-500'} ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${hasUrgentReturns ? 'bg-red-100' : 'bg-orange-100'}`}>
            {hasUrgentReturns ? (
              <AlertTriangle className={`w-6 h-6 ${hasUrgentReturns ? 'text-red-600' : 'text-orange-600'}`} />
            ) : (
              <RotateCcw className="w-6 h-6 text-orange-600" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {salesmanName ? `${salesmanName} - Returns` : 'Pending Returns'}
            </h3>
            <p className={`text-sm ${hasUrgentReturns ? 'text-red-600' : 'text-orange-600'}`}>
              {hasUrgentReturns ? 'Urgent returns require attention' : 'Returns awaiting settlement'}
            </p>
          </div>
        </div>
        
        <button
          onClick={handleNavigateToReturns}
          className={`btn flex items-center space-x-2 ${
            hasUrgentReturns 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-orange-600 hover:bg-orange-700 text-white'
          }`}
        >
          <span>Settle Returns</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 uppercase tracking-wide">Pending</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {displayData.pending_count}
          </p>
        </div>

        <div className="text-center">
          <div className="flex items-center justify-center space-x-1 mb-1">
            <Package className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500 uppercase tracking-wide">Quantity</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {displayData.pending_quantity}
          </p>
        </div>

        {!salesmanId && (
          <>
            <div className="text-center">
              <div className="flex items-center justify-center space-x-1 mb-1">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span className="text-xs text-red-500 uppercase tracking-wide">Damaged</span>
              </div>
              <p className="text-2xl font-bold text-red-600">
                {summary.pending_returns.by_reason.damaged?.count || 0}
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center space-x-1 mb-1">
                <Package className="w-4 h-4 text-blue-500" />
                <span className="text-xs text-blue-500 uppercase tracking-wide">Unsold</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {summary.pending_returns.by_reason.unsold?.count || 0}
              </p>
            </div>
          </>
        )}
      </div>

      {salesmanId && summary.pending_returns.by_salesman.length > 1 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">
            Total system-wide: {summary.pending_returns.total_pending} pending returns from {summary.pending_returns.by_salesman.length} salesmen
          </p>
        </div>
      )}
    </div>
  );
};