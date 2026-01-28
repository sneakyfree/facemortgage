'use client';

import React, { useState, useEffect } from 'react';

/**
 * Bid Wallet Component (Row #15 Gap Fix)
 * 
 * Displays bid wallet balance and allows LOs to:
 * - View current balance
 * - Add funds
 * - Place bids for grid position
 */

interface BidWalletProps {
    className?: string;
}

interface WalletData {
    balance: number;
    pendingBids: number;
    lastTopUp: string | null;
    currentPosition?: number;
    positionScore?: number;
    bidHistory?: {
        id: string;
        amount: number;
        created_at: string;
        status: 'active' | 'outbid' | 'expired';
    }[];
    outbidNotification?: {
        previousPosition: number;
        newPosition: number;
        outbidBy: number;
    } | null;
}

export default function BidWallet({ className = '' }: BidWalletProps) {
    const [wallet, setWallet] = useState<WalletData | null>(null);
    const [loading, setLoading] = useState(true);
    const [showAddFunds, setShowAddFunds] = useState(false);
    const [showPlaceBid, setShowPlaceBid] = useState(false);
    const [amount, setAmount] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchWallet();
    }, []);

    const fetchWallet = async () => {
        try {
            const res = await fetch('/api/v1/billing/wallet');
            if (res.ok) {
                const data = await res.json();
                setWallet({
                    balance: data.balance || 0,
                    pendingBids: data.pending_bids || 0,
                    lastTopUp: data.last_top_up,
                });
            }
        } catch (e) {
            setError('Failed to load wallet');
        } finally {
            setLoading(false);
        }
    };

    const handleAddFunds = async () => {
        const amountNum = parseFloat(amount);
        if (isNaN(amountNum) || amountNum <= 0) {
            setError('Please enter a valid amount');
            return;
        }

        try {
            const res = await fetch('/api/v1/billing/wallet/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: Math.round(amountNum * 100) }), // cents
            });

            if (res.ok) {
                await fetchWallet();
                setShowAddFunds(false);
                setAmount('');
            } else {
                setError('Failed to add funds');
            }
        } catch (e) {
            setError('Failed to add funds');
        }
    };

    const handlePlaceBid = async () => {
        const bidAmount = parseFloat(amount);
        if (isNaN(bidAmount) || bidAmount <= 0) {
            setError('Please enter a valid bid amount');
            return;
        }

        if (wallet && bidAmount > wallet.balance) {
            setError('Insufficient balance');
            return;
        }

        try {
            const res = await fetch('/api/v1/billing/bid', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: Math.round(bidAmount * 100) }),
            });

            if (res.ok) {
                await fetchWallet();
                setShowPlaceBid(false);
                setAmount('');
            } else {
                setError('Failed to place bid');
            }
        } catch (e) {
            setError('Failed to place bid');
        }
    };

    if (loading) {
        return (
            <div className={`bg-white rounded-xl shadow p-6 ${className}`}>
                <div className="animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-10 bg-gray-200 rounded w-full"></div>
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-white rounded-xl shadow overflow-hidden ${className}`}>
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 p-6 text-white">
                <h3 className="text-lg font-semibold mb-1">Bid Wallet</h3>
                <p className="text-white/70 text-sm">Boost your grid position with bids</p>
            </div>

            {/* Balance */}
            <div className="p-6">
                <div className="text-center mb-6">
                    <p className="text-sm text-gray-500 mb-1">Available Balance</p>
                    <p className="text-4xl font-bold text-gray-900">
                        ${((wallet?.balance || 0) / 100).toFixed(2)}
                    </p>
                    {wallet?.pendingBids ? (
                        <p className="text-sm text-orange-600 mt-1">
                            ${(wallet.pendingBids / 100).toFixed(2)} in active bids
                        </p>
                    ) : null}
                </div>

                {/* Error display */}
                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                        {error}
                        <button onClick={() => setError(null)} className="float-right text-red-500">×</button>
                    </div>
                )}

                {/* Actions */}
                {!showAddFunds && !showPlaceBid && (
                    <div className="flex gap-3">
                        <button
                            onClick={() => setShowAddFunds(true)}
                            className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-800 py-3 rounded-lg font-medium transition-colors"
                        >
                            Add Funds
                        </button>
                        <button
                            onClick={() => setShowPlaceBid(true)}
                            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg font-medium transition-colors"
                        >
                            Place Bid
                        </button>
                    </div>
                )}

                {/* Add Funds Form */}
                {showAddFunds && (
                    <div className="space-y-3">
                        <label className="block">
                            <span className="text-sm text-gray-600">Amount to add</span>
                            <div className="relative mt-1">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                                <input
                                    type="number"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="50.00"
                                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    min="1"
                                    step="0.01"
                                />
                            </div>
                        </label>
                        <div className="flex gap-3">
                            <button
                                onClick={() => { setShowAddFunds(false); setAmount(''); }}
                                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAddFunds}
                                className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg"
                            >
                                Add ${amount || '0'}
                            </button>
                        </div>
                    </div>
                )}

                {/* Place Bid Form */}
                {showPlaceBid && (
                    <div className="space-y-3">
                        <label className="block">
                            <span className="text-sm text-gray-600">Bid amount (per impression)</span>
                            <div className="relative mt-1">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                                <input
                                    type="number"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    placeholder="0.10"
                                    className="w-full pl-8 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    min="0.01"
                                    step="0.01"
                                />
                            </div>
                        </label>
                        <p className="text-xs text-gray-500">
                            Higher bids = higher grid position. You&apos;re charged only when shown.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => { setShowPlaceBid(false); setAmount(''); }}
                                className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handlePlaceBid}
                                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg"
                            >
                                Place Bid
                            </button>
                        </div>
                    </div>
                )}

                {/* Current Grid Position */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-600">Your Grid Position</span>
                        <span className="text-lg font-bold text-purple-600">
                            #{wallet?.currentPosition || '—'}
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className="bg-purple-600 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(100, (wallet?.positionScore || 0))}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                        Based on your bid, rating, and response time
                    </p>
                </div>

                {/* Outbid Notification */}
                {wallet?.outbidNotification && (
                    <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg flex items-start gap-3">
                        <span className="text-xl">⚠️</span>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-orange-800">
                                You've been outbid!
                            </p>
                            <p className="text-xs text-orange-600 mt-1">
                                Increase your bid to maintain position #{wallet.outbidNotification.previousPosition}
                            </p>
                            <button
                                onClick={() => setShowPlaceBid(true)}
                                className="mt-2 text-xs bg-orange-500 text-white px-3 py-1 rounded-full hover:bg-orange-600"
                            >
                                Increase Bid
                            </button>
                        </div>
                    </div>
                )}

                {/* Bid History */}
                <div className="mt-6">
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">Bid History</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                        {(wallet?.bidHistory || []).length > 0 ? (
                            wallet?.bidHistory?.map((bid: { id: string; amount: number; created_at: string; status: string }) => (
                                <div key={bid.id} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
                                    <div>
                                        <span className="font-medium">${(bid.amount / 100).toFixed(2)}</span>
                                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${bid.status === 'active' ? 'bg-green-100 text-green-700' :
                                            bid.status === 'outbid' ? 'bg-orange-100 text-orange-700' :
                                                'bg-gray-100 text-gray-600'
                                            }`}>
                                            {bid.status}
                                        </span>
                                    </div>
                                    <span className="text-gray-500 text-xs">
                                        {new Date(bid.created_at).toLocaleDateString()}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <p className="text-sm text-gray-400 text-center py-4">
                                No bids placed yet
                            </p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
