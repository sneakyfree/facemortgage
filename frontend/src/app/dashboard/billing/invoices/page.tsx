'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';
import { FileText, Download, ExternalLink, AlertCircle } from 'lucide-react';

interface Invoice {
    id: string;
    number: string;
    amount_due: number;
    amount_paid: number;
    currency: string;
    status: 'paid' | 'open' | 'void' | 'uncollectible' | 'draft';
    created: number;
    period_start: number;
    period_end: number;
    hosted_invoice_url: string;
    invoice_pdf: string;
}

const STATUS_CONFIG = {
    paid: { label: 'Paid', color: 'bg-green-100 text-green-800' },
    open: { label: 'Open', color: 'bg-yellow-100 text-yellow-800' },
    void: { label: 'Void', color: 'bg-gray-100 text-gray-600' },
    uncollectible: { label: 'Uncollectible', color: 'bg-red-100 text-red-800' },
    draft: { label: 'Draft', color: 'bg-blue-100 text-blue-800' },
};

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchInvoices();
    }, []);

    const fetchInvoices = async () => {
        try {
            const { data } = await apiClient.get('/billing/invoices');
            setInvoices(data.invoices || []);
        } catch {
            setError('Failed to load invoices');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (amount: number, currency: string) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency.toUpperCase(),
        }).format(amount / 100);
    };

    const formatDate = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    if (loading) {
        return (
            <div className="p-6 max-w-4xl mx-auto">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/4" />
                    <div className="h-4 bg-gray-200 rounded w-1/3" />
                    <div className="space-y-3 mt-6">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="h-16 bg-gray-200 rounded" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6 max-w-4xl mx-auto">
                <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
                    <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
                    <h2 className="text-lg font-semibold text-red-900">{error}</h2>
                    <button
                        onClick={fetchInvoices}
                        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Invoice History</h1>
                <p className="mt-1 text-gray-600">
                    View and download your past invoices
                </p>
            </div>

            {/* Empty State */}
            {invoices.length === 0 ? (
                <div className="bg-white border rounded-xl p-12 text-center">
                    <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                        No Invoices Yet
                    </h2>
                    <p className="text-gray-500 mb-6">
                        Your invoices will appear here after your first payment
                    </p>
                    <a
                        href="/subscribe"
                        className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        View Plans
                    </a>
                </div>
            ) : (
                <>
                    {/* Desktop Table */}
                    <div className="hidden md:block bg-white border rounded-xl overflow-hidden">
                        <table className="w-full">
                            <thead className="bg-gray-50 border-b">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        Invoice
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        Date
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        Amount
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {invoices.map((invoice) => (
                                    <tr key={invoice.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <FileText className="w-5 h-5 text-gray-400" />
                                                <span className="font-medium text-gray-900">
                                                    {invoice.number || `INV-${invoice.id.slice(-8)}`}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-600">
                                            {formatDate(invoice.created)}
                                        </td>
                                        <td className="px-6 py-4 font-medium text-gray-900">
                                            {formatCurrency(invoice.amount_due, invoice.currency)}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[invoice.status]?.color || 'bg-gray-100'
                                                }`}>
                                                {STATUS_CONFIG[invoice.status]?.label || invoice.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center justify-end gap-2">
                                                {invoice.hosted_invoice_url && (
                                                    <a
                                                        href={invoice.hosted_invoice_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                                                        title="View online"
                                                    >
                                                        <ExternalLink className="w-4 h-4" />
                                                    </a>
                                                )}
                                                {invoice.invoice_pdf && (
                                                    <a
                                                        href={invoice.invoice_pdf}
                                                        download
                                                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                                                        title="Download PDF"
                                                    >
                                                        <Download className="w-4 h-4" />
                                                    </a>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile Cards */}
                    <div className="md:hidden space-y-4">
                        {invoices.map((invoice) => (
                            <div key={invoice.id} className="bg-white border rounded-xl p-4">
                                <div className="flex items-start justify-between mb-3">
                                    <div>
                                        <p className="font-semibold text-gray-900">
                                            {invoice.number || `INV-${invoice.id.slice(-8)}`}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            {formatDate(invoice.created)}
                                        </p>
                                    </div>
                                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[invoice.status]?.color || 'bg-gray-100'
                                        }`}>
                                        {STATUS_CONFIG[invoice.status]?.label || invoice.status}
                                    </span>
                                </div>

                                <div className="flex items-center justify-between">
                                    <p className="text-lg font-bold text-gray-900">
                                        {formatCurrency(invoice.amount_due, invoice.currency)}
                                    </p>
                                    <div className="flex gap-2">
                                        {invoice.invoice_pdf && (
                                            <a
                                                href={invoice.invoice_pdf}
                                                download
                                                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
                                            >
                                                <Download className="w-4 h-4" />
                                                PDF
                                            </a>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
