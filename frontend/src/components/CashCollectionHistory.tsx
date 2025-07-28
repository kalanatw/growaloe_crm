import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';

interface CashCollection {
    id: number;
    salesman: number;
    salesman_name: string;
    amount: number;
    collection_date: string;
    collection_method: string;
    reference_number: string | null;
    notes: string | null;
    salesman_balance_before: number;
    salesman_balance_after: number;
    collected_by: number;
    collected_by_name: string;
    status: string;
    created_at: string;
}

interface CashCollectionHistoryProps {
    salesmanId: number;
    salesmanName: string;
}

export const CashCollectionHistory: React.FC<CashCollectionHistoryProps> = ({
    salesmanId,
    salesmanName
}) => {
    const [collections, setCollections] = useState<CashCollection[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchCollectionHistory = async () => {
        try {
            setIsLoading(true);
            const response = await apiClient.get<CashCollection[]>(`/api/accounts/salesmen/${salesmanId}/cash-collections/`);
            setCollections(response);
        } catch (error) {
            console.error('Error fetching collection history:', error);
            toast.error('Failed to fetch collection history');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchCollectionHistory();
    }, [salesmanId]);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    const formatDateTime = (dateString: string) => {
        return new Date(dateString).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getMethodBadgeColor = (method: string) => {
        switch (method) {
            case 'physical_handover':
                return 'bg-green-100 text-green-800';
            case 'bank_deposit':
                return 'bg-blue-100 text-blue-800';
            case 'digital_transfer':
                return 'bg-purple-100 text-purple-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getMethodLabel = (method: string) => {
        switch (method) {
            case 'physical_handover':
                return 'Physical Handover';
            case 'bank_deposit':
                return 'Bank Deposit';
            case 'digital_transfer':
                return 'Digital Transfer';
            default:
                return method;
        }
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Cash Collection History - {salesmanName}
                </h3>
                <div className="animate-pulse space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="border rounded-lg p-4">
                            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Cash Collection History - {salesmanName}
            </h3>

            {collections.length === 0 ? (
                <div className="text-center py-8">
                    <div className="text-gray-400 mb-2">
                        <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                        </svg>
                    </div>
                    <p className="text-gray-500">No cash collections yet</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {collections.map((collection) => (
                        <div key={collection.id} className="border rounded-lg p-4 hover:bg-gray-50">
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <div className="flex items-center space-x-2">
                                        <span className="text-lg font-semibold text-green-600">
                                            LKR {collection.amount.toFixed(2)}
                                        </span>
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getMethodBadgeColor(collection.collection_method)}`}>
                                            {getMethodLabel(collection.collection_method)}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 mt-1">
                                        Collected on {formatDate(collection.collection_date)}
                                    </p>
                                </div>
                                <div className="text-right text-sm text-gray-500">
                                    {formatDateTime(collection.created_at)}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-600">Balance Before:</span>
                                    <span className="ml-2 font-medium">LKR {collection.salesman_balance_before.toFixed(2)}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Balance After:</span>
                                    <span className="ml-2 font-medium">LKR {collection.salesman_balance_after.toFixed(2)}</span>
                                </div>
                            </div>

                            {collection.reference_number && (
                                <div className="mt-2 text-sm">
                                    <span className="text-gray-600">Reference:</span>
                                    <span className="ml-2 font-mono text-gray-900">{collection.reference_number}</span>
                                </div>
                            )}

                            {collection.notes && (
                                <div className="mt-2 text-sm">
                                    <span className="text-gray-600">Notes:</span>
                                    <p className="ml-2 text-gray-900 italic">{collection.notes}</p>
                                </div>
                            )}

                            <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                                Collected by {collection.collected_by_name}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};