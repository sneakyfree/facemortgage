'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api/client';

interface WalletBalance {
    available_credits: number;
    reserved_credits: number;
    total_deposited: number;
    total_spent: number;
}

interface Transaction {
    id: string;
    amount: number;
    transaction_type: string;
    description: string | null;
    created_at: string;
}

interface PlacementBid {
    id: string;
    daily_budget: number;
    bid_per_impression: number | null;
    bid_per_click: number | null;
    target_counties: string[] | null;
    target_languages: string[] | null;
    target_specialties: string[] | null;
    daily_spent: number;
    total_spent: number;
    is_active: boolean;
}

interface PositionPreview {
    bid_amount: number;
    estimated_position: number;
    competing_bids: number;
    position_percentile: number;
}

export default function BidWalletPage() {
    const [wallet, setWallet] = useState<WalletBalance | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [bids, setBids] = useState<PlacementBid[]>([]);
    const [preview, setPreview] = useState<PositionPreview | null>(null);
    const [loading, setLoading] = useState(true);
    const [depositAmount, setDepositAmount] = useState('50');
    const [showDepositModal, setShowDepositModal] = useState(false);
    const [showBidModal, setShowBidModal] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // New bid form state
    const [newBid, setNewBid] = useState({
        daily_budget: '',
        bid_per_click: '',
    });
    const [previewBidAmount, setPreviewBidAmount] = useState('10');

    useEffect(() => {
        fetchData();
    }, []);

    async function fetchData() {
        try {
            const [walletRes, txRes, bidsRes] = await Promise.all([
                apiClient.get('/bid/wallet'),
                apiClient.get('/bid/wallet/transactions'),
                apiClient.get('/bid/placement'),
            ]);
            setWallet(walletRes.data);
            setTransactions(txRes.data);
            setBids(bidsRes.data);
        } catch (error) {
            console.error('Failed to fetch bid wallet data:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleDeposit() {
        try {
            const response = await apiClient.post('/bid/wallet/deposit', {
                amount: parseFloat(depositAmount),
            });
            // Redirect to Stripe checkout
            if (response.data.client_secret) {
                // In production, use Stripe.js Elements
                window.location.href = `/checkout?payment_intent=${response.data.payment_intent_id}&client_secret=${response.data.client_secret}`;
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to create deposit' });
        }
        setShowDepositModal(false);
    }

    async function handleCreateBid() {
        try {
            await apiClient.post('/bid/placement', {
                daily_budget: parseFloat(newBid.daily_budget),
                bid_per_click: newBid.bid_per_click ? parseFloat(newBid.bid_per_click) : null,
            });
            setMessage({ type: 'success', text: 'Placement bid created!' });
            setShowBidModal(false);
            fetchData();
        } catch (error: any) {
            setMessage({ type: 'error', text: error.response?.data?.detail || 'Failed to create bid' });
        }
    }

    async function handleCancelBid(bidId: string) {
        if (!confirm('Are you sure you want to cancel this bid?')) return;
        try {
            await apiClient.delete(`/bid/placement/${bidId}`);
            setMessage({ type: 'success', text: 'Bid cancelled and credits refunded' });
            fetchData();
        } catch (error) {
            setMessage({ type: 'error', text: 'Failed to cancel bid' });
        }
    }

    async function handlePreviewPosition() {
        try {
            const response = await apiClient.post('/bid/placement/preview', {
                bid_amount: parseFloat(previewBidAmount),
            });
            setPreview(response.data);
        } catch (error) {
            console.error('Failed to get position preview:', error);
        }
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-6xl mx-auto animate-pulse space-y-6">
                    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
                    <div className="grid grid-cols-3 gap-6">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-6xl mx-auto space-y-8">
                {/* Header with Back Link */}
                <div className="flex items-center justify-between">
                    <div>
                        <Link href="/dashboard/billing" className="text-blue-600 hover:underline text-sm mb-2 inline-block">
                            ← Back to Billing
                        </Link>
                        <h1 className="text-3xl font-bold text-gray-900">Bid Wallet & Placement</h1>
                        <p className="text-gray-600 mt-1">
                            Manage your credits and bid for premium grid positioning
                        </p>
                    </div>
                    <button
                        onClick={() => setShowDepositModal(true)}
                        className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                    >
                        + Add Funds
                    </button>
                </div>

                {/* Messages */}
                {message && (
                    <div
                        className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}
                    >
                        {message.text}
                        <button onClick={() => setMessage(null)} className="float-right font-bold">×</button>
                    </div>
                )}

                {/* Wallet Balance Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-green-500">
                        <p className="text-sm text-gray-600 mb-1">Available Credits</p>
                        <p className="text-3xl font-bold text-green-600">
                            ${Number(wallet?.available_credits ?? 0).toFixed(2)}
                        </p>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-yellow-500">
                        <p className="text-sm text-gray-600 mb-1">Reserved (Active Bids)</p>
                        <p className="text-3xl font-bold text-yellow-600">
                            ${Number(wallet?.reserved_credits ?? 0).toFixed(2)}
                        </p>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-blue-500">
                        <p className="text-sm text-gray-600 mb-1">Total Deposited</p>
                        <p className="text-3xl font-bold text-blue-600">
                            ${Number(wallet?.total_deposited ?? 0).toFixed(2)}
                        </p>
                    </div>
                    <div className="bg-white rounded-xl shadow-sm p-6 border-l-4 border-gray-500">
                        <p className="text-sm text-gray-600 mb-1">Total Spent</p>
                        <p className="text-3xl font-bold text-gray-600">
                            ${Number(wallet?.total_spent ?? 0).toFixed(2)}
                        </p>
                    </div>
                </div>

                {/* Position Preview Tool */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6 text-white">
                    <h2 className="text-xl font-semibold mb-4">🎯 Position Preview</h2>
                    <p className="text-blue-100 mb-4">
                        See where your bid would place you in the grid before committing.
                    </p>
                    <div className="flex items-end gap-4">
                        <div className="flex-1">
                            <label className="block text-sm text-blue-100 mb-2">Daily Budget ($)</label>
                            <input
                                type="number"
                                min="1"
                                max="1000"
                                value={previewBidAmount}
                                onChange={(e) => setPreviewBidAmount(e.target.value)}
                                className="w-full px-4 py-3 rounded-lg text-gray-900 font-medium"
                                placeholder="Enter bid amount"
                            />
                        </div>
                        <button
                            onClick={handlePreviewPosition}
                            className="px-6 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50"
                        >
                            Preview Position
                        </button>
                    </div>

                    {preview && (
                        <div className="mt-6 bg-blue-700/50 rounded-lg p-4 grid grid-cols-3 gap-4 text-center">
                            <div>
                                <p className="text-3xl font-bold">#{preview.estimated_position}</p>
                                <p className="text-sm text-blue-200">Estimated Position</p>
                            </div>
                            <div>
                                <p className="text-3xl font-bold">{preview.competing_bids}</p>
                                <p className="text-sm text-blue-200">Active Bidders</p>
                            </div>
                            <div>
                                <p className="text-3xl font-bold">{preview.position_percentile}%</p>
                                <p className="text-sm text-blue-200">Top Percentile</p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Active Bids */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold">Active Placement Bids</h2>
                        <button
                            onClick={() => setShowBidModal(true)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                            + Create Bid
                        </button>
                    </div>

                    {bids.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <p className="text-lg mb-2">No active bids</p>
                            <p className="text-sm">Create a placement bid to improve your grid position</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b">
                                        <th className="text-left py-3 px-4 text-gray-600">Daily Budget</th>
                                        <th className="text-left py-3 px-4 text-gray-600">Bid/Click</th>
                                        <th className="text-left py-3 px-4 text-gray-600">Today Spent</th>
                                        <th className="text-left py-3 px-4 text-gray-600">Total Spent</th>
                                        <th className="text-left py-3 px-4 text-gray-600">Status</th>
                                        <th className="text-right py-3 px-4 text-gray-600">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {bids.map((bid) => (
                                        <tr key={bid.id} className="border-b hover:bg-gray-50">
                                            <td className="py-4 px-4 font-medium">${Number(bid.daily_budget ?? 0).toFixed(2)}</td>
                                            <td className="py-4 px-4">${bid.bid_per_click != null ? Number(bid.bid_per_click).toFixed(2) : '—'}</td>
                                            <td className="py-4 px-4">${Number(bid.daily_spent ?? 0).toFixed(2)}</td>
                                            <td className="py-4 px-4">${Number(bid.total_spent ?? 0).toFixed(2)}</td>
                                            <td className="py-4 px-4">
                                                <span
                                                    className={`px-2 py-1 rounded-full text-xs font-medium ${bid.is_active
                                                            ? 'bg-green-100 text-green-800'
                                                            : 'bg-gray-100 text-gray-600'
                                                        }`}
                                                >
                                                    {bid.is_active ? 'Active' : 'Cancelled'}
                                                </span>
                                            </td>
                                            <td className="py-4 px-4 text-right">
                                                {bid.is_active && (
                                                    <button
                                                        onClick={() => handleCancelBid(bid.id)}
                                                        className="text-red-600 hover:underline text-sm"
                                                    >
                                                        Cancel
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

                {/* Transaction History */}
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <h2 className="text-xl font-semibold mb-6">Transaction History</h2>

                    {transactions.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            <p>No transactions yet</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {transactions.map((tx) => (
                                <div
                                    key={tx.id}
                                    className="flex items-center justify-between py-3 border-b last:border-0"
                                >
                                    <div className="flex items-center gap-4">
                                        <div
                                            className={`w-10 h-10 rounded-full flex items-center justify-center ${tx.transaction_type === 'deposit'
                                                    ? 'bg-green-100 text-green-600'
                                                    : tx.transaction_type === 'charge'
                                                        ? 'bg-red-100 text-red-600'
                                                        : 'bg-blue-100 text-blue-600'
                                                }`}
                                        >
                                            {tx.transaction_type === 'deposit' ? '↓' : tx.transaction_type === 'charge' ? '↑' : '↺'}
                                        </div>
                                        <div>
                                            <p className="font-medium capitalize">{tx.transaction_type}</p>
                                            <p className="text-sm text-gray-500">{tx.description || '—'}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p
                                            className={`font-medium ${tx.transaction_type === 'deposit' ? 'text-green-600' : 'text-gray-900'
                                                }`}
                                        >
                                            {tx.transaction_type === 'deposit' ? '+' : '-'}${Math.abs(Number(tx.amount) || 0).toFixed(2)}
                                        </p>
                                        <p className="text-xs text-gray-400">
                                            {new Date(tx.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Deposit Modal */}
                {showDepositModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-xl p-6 w-full max-w-md">
                            <h3 className="text-xl font-semibold mb-4">Add Funds to Wallet</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Select Amount
                                    </label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {['25', '50', '100', '250', '500', '1000'].map((amount) => (
                                            <button
                                                key={amount}
                                                onClick={() => setDepositAmount(amount)}
                                                className={`py-3 rounded-lg font-medium ${depositAmount === amount
                                                        ? 'bg-blue-600 text-white'
                                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                                    }`}
                                            >
                                                ${amount}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button
                                        onClick={() => setShowDepositModal(false)}
                                        className="flex-1 py-3 border rounded-lg hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleDeposit}
                                        className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                                    >
                                        Deposit ${depositAmount}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Create Bid Modal */}
                {showBidModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-xl p-6 w-full max-w-md">
                            <h3 className="text-xl font-semibold mb-4">Create Placement Bid</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Daily Budget ($) *
                                    </label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="1000"
                                        value={newBid.daily_budget}
                                        onChange={(e) => setNewBid({ ...newBid, daily_budget: e.target.value })}
                                        className="w-full px-4 py-3 border rounded-lg"
                                        placeholder="e.g., 50"
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        This amount will be reserved from your available credits
                                    </p>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Bid Per Click ($)
                                    </label>
                                    <input
                                        type="number"
                                        min="0.10"
                                        max="50"
                                        step="0.10"
                                        value={newBid.bid_per_click}
                                        onChange={(e) => setNewBid({ ...newBid, bid_per_click: e.target.value })}
                                        className="w-full px-4 py-3 border rounded-lg"
                                        placeholder="e.g., 2.50"
                                    />
                                </div>
                                <div className="flex gap-3 pt-4">
                                    <button
                                        onClick={() => setShowBidModal(false)}
                                        className="flex-1 py-3 border rounded-lg hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={handleCreateBid}
                                        disabled={!newBid.daily_budget}
                                        className="flex-1 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50"
                                    >
                                        Create Bid
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
