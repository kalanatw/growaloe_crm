import React, { useState, useEffect } from 'react';
import { X, Package, DollarSign, CheckCircle, ArrowRight, ArrowLeft, Calculator, TrendingUp, AlertCircle } from 'lucide-react';
import { deliveryService } from '../services/apiServices';
import toast from 'react-hot-toast';

interface DeliverySettlementModalProps {
    salesman: any;
    isOpen: boolean;
    onClose: () => void;
    onSettle: (salesmanId: number, settlementData: SettlementData) => void;
    isSettling: boolean;
}

interface SettlementData {
    settlement_notes: string;
    cash_settlement_amount: number;
    settlement_method: 'full_cash' | 'partial_cash' | 'balance_carry';
    return_all_stock: boolean;
    create_settlement_record: boolean;
}

interface DeliverySettlementPreview {
    delivery: {
        id: number;
        delivery_number: string;
        salesman_name: string;
        delivery_date: string;
    };
    products: Array<{
        product_name: string;
        delivered_quantity: number;
        sold_quantity: number;
        returned_quantity: number;
        outstanding_quantity: number;
        unit_price: number;
        delivered_value: number;
        sold_value: number;
        outstanding_value: number;
    }>;
    cash_breakdown: {
        invoice_collections: number;
        delivery_expenses: number;
        return_value: number;
        net_cash_available: number;
        payment_methods: Array<{
            method: string;
            amount: number;
            reference?: string;
            bank?: string;
        }>;
    };
    salesman_balance: {
        current_balance: number;
        balance_after_settlement: number;
    };
}

type SettlementStep = 'products' | 'cash_breakdown' | 'collection';

export const DeliverySettlementModal: React.FC<DeliverySettlementModalProps> = ({
    salesman,
    isOpen,
    onClose,
    onSettle,
    isSettling
}) => {
    const [currentStep, setCurrentStep] = useState<SettlementStep>('products');
    const [settlementData, setSettlementData] = useState<DeliverySettlementPreview | null>(null);
    const [collectedAmount, setCollectedAmount] = useState(0);
    const [settlementMethod, setSettlementMethod] = useState<'full_cash' | 'partial_cash' | 'balance_carry'>('full_cash');
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen && salesman) {
            loadSettlementPreview();
        }
    }, [isOpen, salesman]);

    const loadSettlementPreview = async () => {
        try {
            setLoading(true);
            const salesmanId = salesman.salesman_id || salesman.id;

            // Use the new settlement preview API service method
            const settlementPreviewData = await deliveryService.getDeliverySettlementPreview(salesmanId);

            setSettlementData(settlementPreviewData);
            setCollectedAmount(settlementPreviewData.cash_breakdown.net_cash_available);
        } catch (error) {
            console.error('Error loading settlement preview:', error);
            toast.error('Failed to load settlement data');
        } finally {
            setLoading(false);
        }
    };

    const handleNext = () => {
        if (currentStep === 'products') {
            setCurrentStep('cash_breakdown');
        } else if (currentStep === 'cash_breakdown') {
            setCurrentStep('collection');
        }
    };

    const handleBack = () => {
        if (currentStep === 'cash_breakdown') {
            setCurrentStep('products');
        } else if (currentStep === 'collection') {
            setCurrentStep('cash_breakdown');
        }
    };

    const handleSettle = () => {
        if (!settlementData) return;

        onSettle(salesman.salesman_id || salesman.id, {
            settlement_notes: notes,
            cash_settlement_amount: collectedAmount,
            settlement_method: settlementMethod,
            return_all_stock: true,
            create_settlement_record: true
        });
    };

    const handleClose = () => {
        setCurrentStep('products');
        setCollectedAmount(0);
        setSettlementMethod('full_cash');
        setNotes('');
        setSettlementData(null);
        onClose();
    };

    const getStepTitle = () => {
        switch (currentStep) {
            case 'products':
                return 'Step 1: Verify Products Delivered';
            case 'cash_breakdown':
                return 'Step 2: Cash Settlement Breakdown';
            case 'collection':
                return 'Step 3: Record Cash Collected';
            default:
                return '';
        }
    };

    const isStepCompleted = (step: SettlementStep) => {
        switch (step) {
            case 'products':
                return currentStep !== 'products';
            case 'cash_breakdown':
                return currentStep === 'collection';
            case 'collection':
                return false;
            default:
                return false;
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                            Settlement - {settlementData?.delivery.salesman_name || salesman?.salesman_name || salesman?.name}
                        </h2>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            {settlementData?.delivery.delivery_number && `Delivery: ${settlementData.delivery.delivery_number}`}
                        </p>
                    </div>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Progress Steps */}
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-4">
                        {(['products', 'cash_breakdown', 'collection'] as SettlementStep[]).map((step, index) => (
                            <div key={step} className="flex items-center">
                                <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${currentStep === step
                                    ? 'bg-blue-600 text-white'
                                    : isStepCompleted(step)
                                        ? 'bg-green-600 text-white'
                                        : 'bg-gray-200 text-gray-600'
                                    }`}>
                                    {isStepCompleted(step) ? (
                                        <CheckCircle className="w-4 h-4" />
                                    ) : (
                                        index + 1
                                    )}
                                </div>
                                {index < 2 && (
                                    <div className={`w-12 h-0.5 mx-2 ${isStepCompleted(step) ? 'bg-green-600' : 'bg-gray-200'
                                        }`} />
                                )}
                            </div>
                        ))}
                    </div>
                    <div className="mt-2">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                            {getStepTitle()}
                        </h3>
                    </div>
                </div>

                <div className="p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : settlementData ? (
                        <>
                            {/* Step 1: Products Verification */}
                            {currentStep === 'products' && (
                                <div className="space-y-6">
                                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <Package className="w-5 h-5 text-blue-600" />
                                            <h4 className="font-medium text-blue-900 dark:text-blue-100">Product Verification</h4>
                                        </div>
                                        <p className="text-sm text-blue-800 dark:text-blue-200">
                                            Review the products delivered, sold, and returned for this settlement.
                                        </p>
                                    </div>

                                    <div className="overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                                            <thead className="bg-gray-50 dark:bg-gray-700">
                                                <tr>
                                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Product Name
                                                    </th>
                                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Delivered
                                                    </th>
                                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Sold
                                                    </th>
                                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Returned
                                                    </th>
                                                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Outstanding
                                                    </th>
                                                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                                        Value (LKR)
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                                                {settlementData.products.map((product, index) => (
                                                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                                                            {product.product_name}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-center text-gray-600 dark:text-gray-400">
                                                            {product.delivered_quantity}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-center text-green-600">
                                                            {product.sold_quantity}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-center text-blue-600">
                                                            {product.returned_quantity}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-center text-orange-600">
                                                            {product.outstanding_quantity}
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-right font-medium text-gray-900 dark:text-white">
                                                            {product.delivered_value.toFixed(2)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                            <tfoot className="bg-gray-50 dark:bg-gray-700">
                                                <tr>
                                                    <td colSpan={5} className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white text-right">
                                                        Total Delivered Value:
                                                    </td>
                                                    <td className="px-4 py-3 text-sm font-bold text-gray-900 dark:text-white text-right">
                                                        LKR {settlementData.products.reduce((sum, p) => sum + p.delivered_value, 0).toFixed(2)}
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </div>

                                    <div className="flex items-center justify-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                                        <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                                        <span className="text-green-800 dark:text-green-200 font-medium">Products Verified</span>
                                    </div>
                                </div>
                            )}

                            {/* Step 2: Cash Breakdown */}
                            {currentStep === 'cash_breakdown' && (
                                <div className="space-y-6">
                                    <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <TrendingUp className="w-5 h-5 text-green-600" />
                                            <h4 className="font-medium text-green-900 dark:text-green-100">Cash Flow Breakdown</h4>
                                        </div>
                                        <p className="text-sm text-green-800 dark:text-green-200">
                                            Review the cash flow from this delivery settlement.
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Net Cash Calculation */}
                                        <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-900 dark:text-white mb-4">Net Cash to Collect</h5>
                                            <div className="space-y-3">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Invoice Collections:</span>
                                                    <span className="text-sm font-medium text-green-600">
                                                        +LKR {settlementData.cash_breakdown.invoice_collections.toFixed(2)}
                                                    </span>
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Delivery Expenses:</span>
                                                    <span className="text-sm font-medium text-red-600">
                                                        LKR {settlementData.cash_breakdown.delivery_expenses.toFixed(2)}
                                                    </span>
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Product Returns Value:</span>
                                                    <span className="text-sm font-medium text-blue-600">
                                                        +LKR {settlementData.cash_breakdown.return_value.toFixed(2)}
                                                    </span>
                                                </div>
                                                <div className="border-t border-gray-200 dark:border-gray-600 pt-2">
                                                    <div className="flex justify-between items-center">
                                                        <span className="font-medium text-gray-900 dark:text-white">Net Cash Available:</span>
                                                        <span className="font-bold text-lg text-blue-600">
                                                            LKR {settlementData.cash_breakdown.net_cash_available.toFixed(2)}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Payment Methods */}
                                        <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                                            <h5 className="font-medium text-gray-900 dark:text-white mb-4">Payment Methods Received</h5>
                                            <div className="space-y-3">
                                                {settlementData.cash_breakdown.payment_methods.map((payment, index) => (
                                                    <div key={index} className="flex justify-between items-center">
                                                        <div>
                                                            <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                                                                {payment.method}:
                                                            </span>
                                                            {payment.reference && (
                                                                <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                                                                    {payment.reference}
                                                                </span>
                                                            )}
                                                            {payment.bank && (
                                                                <span className="text-xs text-gray-500 dark:text-gray-400 ml-1">
                                                                    ({payment.bank})
                                                                </span>
                                                            )}
                                                        </div>
                                                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                                                            LKR {payment.amount.toFixed(2)}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Step 3: Collection Input */}
                            {currentStep === 'collection' && (
                                <div className="space-y-6">
                                    <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                                        <div className="flex items-center space-x-2 mb-2">
                                            <DollarSign className="w-5 h-5 text-orange-600" />
                                            <h4 className="font-medium text-orange-900 dark:text-orange-100">Record Cash Collection</h4>
                                        </div>
                                        <p className="text-sm text-orange-800 dark:text-orange-200">
                                            Enter the amount you collected from the salesman.
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Collection Input */}
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                    Available to Collect: LKR {settlementData.cash_breakdown.net_cash_available.toFixed(2)}
                                                </label>
                                                <div className="relative">
                                                    <input
                                                        type="number"
                                                        step="0.01"
                                                        value={collectedAmount}
                                                        onChange={(e) => setCollectedAmount(parseFloat(e.target.value) || 0)}
                                                        max={settlementData.cash_breakdown.net_cash_available}
                                                        className="w-full px-4 py-3 text-lg border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                                        placeholder="0.00"
                                                    />
                                                    <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                                                        <span className="text-gray-500 text-sm">LKR</span>
                                                    </div>
                                                </div>
                                                {collectedAmount > settlementData.cash_breakdown.net_cash_available && (
                                                    <p className="text-xs text-red-600 mt-1 flex items-center">
                                                        <AlertCircle className="w-3 h-3 mr-1" />
                                                        Amount exceeds available cash
                                                    </p>
                                                )}
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                    Settlement Method
                                                </label>
                                                <select
                                                    value={settlementMethod}
                                                    onChange={(e) => setSettlementMethod(e.target.value as any)}
                                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                                >
                                                    <option value="full_cash">Full Cash Settlement</option>
                                                    <option value="partial_cash">Partial Cash Settlement</option>
                                                    <option value="balance_carry">Carry Balance Forward</option>
                                                </select>
                                            </div>

                                            <div>
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                                    Notes
                                                </label>
                                                <textarea
                                                    value={notes}
                                                    onChange={(e) => setNotes(e.target.value)}
                                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                                                    rows={3}
                                                    placeholder="Add settlement notes..."
                                                />
                                            </div>
                                        </div>

                                        {/* Balance Impact */}
                                        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                                            <h5 className="font-medium text-gray-900 dark:text-white mb-4">Balance Impact</h5>
                                            <div className="space-y-3">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Current Balancee:</span>
                                                    <span className={`text-sm font-medium ${settlementData.salesman_balance.current_balance >= 0 ? 'text-red-600' : 'text-green-600'
                                                        }`}>
                                                        LKR {settlementData.salesman_balance.current_balance.toFixed(2)}
                                                    </span>
                                                </div>
                                                <div className="flex justify-between items-center">
                                                    <span className="text-sm text-gray-600 dark:text-gray-400">Settlement Amount:</span>
                                                    <span className="text-sm font-medium text-blue-600">
                                                        -LKR {collectedAmount.toFixed(2)}
                                                    </span>
                                                </div>
                                                <div className="border-t border-gray-200 dark:border-gray-600 pt-2">
                                                    <div className="flex justify-between items-center">
                                                        <span className="font-medium text-gray-900 dark:text-white">New Balance:</span>
                                                        <span className={`font-bold text-lg ${(settlementData.salesman_balance.current_balance - collectedAmount) >= 0 ? 'text-red-600' : 'text-green-600'
                                                            }`}>
                                                            LKR {(settlementData.salesman_balance.current_balance - collectedAmount).toFixed(2)}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                                        {(settlementData.salesman_balance.current_balance - collectedAmount) >= 0
                                                            ? 'Salesman owes owner'
                                                            : 'Owner owes salesman'
                                                        }
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-8">
                            <p className="text-gray-500 dark:text-gray-400">Failed to load settlement data</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-between items-center p-6 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex space-x-3">
                        {currentStep !== 'products' && (
                            <button
                                onClick={handleBack}
                                className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
                                disabled={isSettling}
                            >
                                <ArrowLeft className="w-4 h-4" />
                                <span>Back</span>
                            </button>
                        )}
                    </div>

                    <div className="flex space-x-3">
                        <button
                            onClick={handleClose}
                            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            disabled={isSettling}
                        >
                            Cancel
                        </button>

                        {currentStep === 'collection' ? (
                            <button
                                onClick={handleSettle}
                                disabled={isSettling || !settlementData || collectedAmount > (settlementData?.cash_breakdown.net_cash_available || 0)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                            >
                                {isSettling ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                        <span>Settling...</span>
                                    </>
                                ) : (
                                    <>
                                        <Calculator className="w-4 h-4" />
                                        <span>Complete Settlement</span>
                                    </>
                                )}
                            </button>
                        ) : (
                            <button
                                onClick={handleNext}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center space-x-2"
                            >
                                <span>Continue</span>
                                <ArrowRight className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};