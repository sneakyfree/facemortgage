'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface Dispute {
    id: string;
    review_id: string;
    complainant_id: string;
    complainant_name: string;
    complainant_type: 'professional' | 'borrower';
    reason: string;
    status: 'open' | 'under_review' | 'resolved' | 'dismissed';
    resolution?: string;
    created_at: string;
    review_content?: string;
    review_rating?: number;
}

export default function DisputesPage() {
    const [disputes, setDisputes] = useState<Dispute[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'open' | 'all'>('open');
    const [selectedDispute, setSelectedDispute] = useState<Dispute | null>(null);
    const [resolution, setResolution] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadDisputes();
    }, [filter]);

    const loadDisputes = async () => {
        setLoading(true);
        try {
            const { data } = await apiClient.get('/disputes', {
                params: { status: filter === 'all' ? undefined : 'open' }
            });
            setDisputes(data.disputes || []);
        } catch (err) {
            console.error('Failed to load disputes:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleResolve = async (action: 'uphold' | 'dismiss') => {
        if (!selectedDispute) return;
        if (action === 'uphold' && !resolution.trim()) {
            alert('Please enter a resolution note');
            return;
        }

        setActionLoading(true);
        try {
            const endpoint = action === 'uphold'
                ? `/disputes/${selectedDispute.id}/resolve`
                : `/disputes/${selectedDispute.id}/dismiss`;

            await apiClient.post(endpoint, { resolution: resolution || 'Dispute dismissed' });
            setSelectedDispute(null);
            setResolution('');
            await loadDisputes();
        } catch (err) {
            alert('Failed to resolve dispute');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-10 bg-gray-200 rounded w-1/4" />
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-32 bg-gray-200 rounded-lg" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dispute Resolution</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Review and resolve user disputes about reviews or charges
                    </p>
                </div>
                <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value as any)}
                    className="px-4 py-2 border border-gray-300 rounded-lg"
                    aria-label="Filter disputes"
                >
                    <option value="open">Open Disputes</option>
                    <option value="all">All Disputes</option>
                </select>
            </div>

            {/* Empty state */}
            {disputes.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-gray-200">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Open Disputes</h3>
                    <p className="text-gray-600">All disputes have been resolved.</p>
                </div>
            ) : (
                <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Complainant</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Reason</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Status</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Date</th>
                                <th className="px-6 py-4 text-right text-sm font-semibold text-gray-900">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {disputes.map(dispute => (
                                <tr key={dispute.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-gray-900">{dispute.complainant_name}</div>
                                        <div className="text-sm text-gray-500">{dispute.complainant_type}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <p className="text-gray-900 line-clamp-2">{dispute.reason}</p>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${dispute.status === 'open' ? 'bg-yellow-100 text-yellow-800' :
                                                dispute.status === 'under_review' ? 'bg-blue-100 text-blue-800' :
                                                    dispute.status === 'resolved' ? 'bg-green-100 text-green-800' :
                                                        'bg-gray-100 text-gray-800'
                                            }`}>
                                            {dispute.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(dispute.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        {dispute.status === 'open' || dispute.status === 'under_review' ? (
                                            <button
                                                onClick={() => setSelectedDispute(dispute)}
                                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                                            >
                                                Review
                                            </button>
                                        ) : (
                                            <span className="text-sm text-gray-500">Closed</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Resolution Modal */}
            {selectedDispute && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-2xl font-bold text-gray-900">Review Dispute</h2>
                                <button
                                    onClick={() => { setSelectedDispute(null); setResolution(''); }}
                                    className="text-gray-400 hover:text-gray-600"
                                    aria-label="Close modal"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>

                            {/* Dispute details */}
                            <div className="space-y-4 mb-6">
                                <div>
                                    <label className="text-sm font-medium text-gray-500">Complainant</label>
                                    <p className="text-gray-900">{selectedDispute.complainant_name} ({selectedDispute.complainant_type})</p>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-gray-500">Complaint Reason</label>
                                    <p className="text-gray-900">{selectedDispute.reason}</p>
                                </div>
                                {selectedDispute.review_content && (
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Original Review</label>
                                        <div className="bg-gray-50 rounded-lg p-4">
                                            <div className="flex items-center mb-2">
                                                {[1, 2, 3, 4, 5].map(i => (
                                                    <svg
                                                        key={i}
                                                        className={`w-5 h-5 ${i <= (selectedDispute.review_rating || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                                                        fill="currentColor"
                                                        viewBox="0 0 20 20"
                                                    >
                                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                                    </svg>
                                                ))}
                                            </div>
                                            <p className="text-gray-900">{selectedDispute.review_content}</p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Resolution input */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Resolution Notes
                                </label>
                                <textarea
                                    value={resolution}
                                    onChange={(e) => setResolution(e.target.value)}
                                    placeholder="Enter your resolution notes..."
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                    rows={4}
                                />
                            </div>

                            {/* Action buttons */}
                            <div className="flex gap-3">
                                <button
                                    onClick={() => handleResolve('uphold')}
                                    disabled={actionLoading}
                                    className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold disabled:opacity-50"
                                >
                                    {actionLoading ? 'Processing...' : 'Uphold (Remove Review)'}
                                </button>
                                <button
                                    onClick={() => handleResolve('dismiss')}
                                    disabled={actionLoading}
                                    className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-semibold disabled:opacity-50"
                                >
                                    {actionLoading ? 'Processing...' : 'Dismiss Complaint'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
