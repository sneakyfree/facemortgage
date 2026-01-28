'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

/**
 * Billing & Analytics Hooks - Phase 3 Monetization
 * 
 * Provides hooks for:
 * - Invoice history from Stripe
 * - Bid transaction history
 * - Usage analytics dashboard
 * - Billing summary
 */

// Invoice types
export interface InvoiceItem {
    id: string;
    invoice_id: string;
    amount: number;
    currency: string;
    description: string;
    date: string;
    status: 'paid' | 'unpaid' | 'void';
    pdf_url: string | null;
    hosted_url: string | null;
}

export interface InvoiceHistoryResponse {
    invoices: InvoiceItem[];
    total_count: number;
    has_more: boolean;
}

// Transaction types
export interface BidTransaction {
    id: string;
    type: string;
    amount: number;
    description: string;
    created_at: string;
}

// Usage stats types
export interface UsageStats {
    total_calls: number;
    calls_this_month: number;
    avg_call_duration_seconds: number;
    total_leads: number;
    leads_this_month: number;
    lead_conversion_rate: number;
    profile_views: number;
    click_through_rate: number;
    avg_grid_position: number;
    total_bid_spent: number;
    bid_spent_this_month: number;
    cost_per_lead: number;
    cost_per_call: number;
    time_online_today_seconds: number;
    time_online_this_month_hours: number;
}

// Billing summary types
export interface BillingSummary {
    subscription: {
        tier: string;
        status: string;
        current_period_end: string | null;
        cancel_at_period_end: boolean;
    };
    wallet: {
        balance: number;
        reserved: number;
        current_bid: number;
        daily_budget: number | null;
    };
}

/**
 * Hook for invoice history
 */
export function useInvoices() {
    const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [hasMore, setHasMore] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchInvoices = useCallback(async (startingAfter?: string) => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (startingAfter) params.set('starting_after', startingAfter);

            const response = await apiClient.get<InvoiceHistoryResponse>(
                `/billing-enhanced/invoices?${params.toString()}`
            );

            if (startingAfter) {
                setInvoices(prev => [...prev, ...response.data.invoices]);
            } else {
                setInvoices(response.data.invoices);
            }
            setHasMore(response.data.has_more);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to load invoices');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchInvoices();
    }, [fetchInvoices]);

    const loadMore = useCallback(() => {
        if (invoices.length > 0 && hasMore) {
            fetchInvoices(invoices[invoices.length - 1].id);
        }
    }, [invoices, hasMore, fetchInvoices]);

    return { invoices, loading, hasMore, loadMore, error };
}

/**
 * Hook for bid transaction history
 */
export function useTransactions() {
    const [transactions, setTransactions] = useState<BidTransaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchTransactions = async () => {
            try {
                const response = await apiClient.get<{ transactions: BidTransaction[] }>(
                    '/billing-enhanced/transactions'
                );
                setTransactions(response.data.transactions);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Failed to load transactions');
            } finally {
                setLoading(false);
            }
        };
        fetchTransactions();
    }, []);

    return { transactions, loading, error };
}

/**
 * Hook for usage analytics
 */
export function useUsageAnalytics() {
    const [stats, setStats] = useState<UsageStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get<UsageStats>('/billing-enhanced/usage');
            setStats(response.data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to load usage stats');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    return { stats, loading, error, refresh };
}

/**
 * Hook for billing summary (dashboard card)
 */
export function useBillingSummary() {
    const [summary, setSummary] = useState<BillingSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchSummary = async () => {
            try {
                const response = await apiClient.get<BillingSummary>('/billing-enhanced/summary');
                setSummary(response.data);
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : 'Failed to load billing summary');
            } finally {
                setLoading(false);
            }
        };
        fetchSummary();
    }, []);

    return { summary, loading, error };
}

// Formatting helpers
export function formatCurrency(amount: number, currency = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency,
    }).format(amount);
}

export function formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
}

export function getStatusColor(status: string): string {
    switch (status) {
        case 'paid': return 'text-green-600';
        case 'active': return 'text-green-600';
        case 'unpaid': return 'text-yellow-600';
        case 'void': return 'text-gray-500';
        case 'canceled': return 'text-red-600';
        default: return 'text-gray-600';
    }
}

export function getTierBadgeClass(tier: string): string {
    switch (tier) {
        case 'premium': return 'bg-purple-100 text-purple-800';
        case 'professional': return 'bg-blue-100 text-blue-800';
        case 'basic': return 'bg-green-100 text-green-800';
        default: return 'bg-gray-100 text-gray-600';
    }
}
