'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface ModerationItem {
    id: string;
    professional_id: string;
    professional_name: string;
    video_url: string;
    status: 'pending' | 'approved' | 'rejected';
    created_at: string;
    rejection_reason?: string;
}

export default function ModerationPage() {
    const [items, setItems] = useState<ModerationItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'pending' | 'all'>('pending');
    const [rejectingId, setRejectingId] = useState<string | null>(null);
    const [rejectReason, setRejectReason] = useState('');
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    useEffect(() => {
        loadItems();
    }, [filter]);

    const loadItems = async () => {
        setLoading(true);
        try {
            const { data } = await apiClient.get('/moderation/pending', {
                params: { status: filter === 'all' ? undefined : 'pending' }
            });
            setItems(data.items || []);
        } catch (err) {
            console.error('Failed to load moderation queue:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (id: string) => {
        setActionLoading(id);
        try {
            await apiClient.post(`/moderation/${id}/approve`);
            await loadItems();
        } catch (err) {
            alert('Failed to approve video');
        } finally {
            setActionLoading(null);
        }
    };

    const handleReject = async (id: string) => {
        if (!rejectReason.trim()) {
            alert('Please enter a rejection reason');
            return;
        }
        setActionLoading(id);
        try {
            await apiClient.post(`/moderation/${id}/reject`, { reason: rejectReason });
            setRejectingId(null);
            setRejectReason('');
            await loadItems();
        } catch (err) {
            alert('Failed to reject video');
        } finally {
            setActionLoading(null);
        }
    };

    if (loading) {
        return (
            <div className="p-6">
                <div className="animate-pulse space-y-6">
                    <div className="h-10 bg-gray-200 rounded w-1/4" />
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-48 bg-gray-200 rounded-lg" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Video Moderation</h1>
                    <p className="mt-1 text-sm text-gray-500">
                        Review and approve professional introduction videos
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-600">
                        {items.length} video{items.length !== 1 ? 's' : ''} to review
                    </span>
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value as any)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        aria-label="Filter videos"
                    >
                        <option value="pending">Pending Only</option>
                        <option value="all">All Videos</option>
                    </select>
                </div>
            </div>

            {/* Empty state */}
            {items.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-gray-200">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">All Caught Up!</h3>
                    <p className="text-gray-600 max-w-sm mx-auto">
                        There are no videos pending review. Check back later or switch to "All Videos" to see history.
                    </p>
                </div>
            ) : (
                <div className="space-y-6">
                    {items.map(item => (
                        <div key={item.id} className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
                                {/* Video player */}
                                <div className="relative">
                                    <video
                                        src={item.video_url}
                                        controls
                                        className="w-full rounded-lg bg-gray-900"
                                        style={{ maxHeight: '320px' }}
                                    >
                                        Your browser does not support the video tag.
                                    </video>
                                </div>

                                {/* Details and actions */}
                                <div className="flex flex-col justify-between">
                                    <div>
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-xl font-semibold text-gray-900">
                                                {item.professional_name || 'Unknown Professional'}
                                            </h3>
                                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${item.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                                    item.status === 'approved' ? 'bg-green-100 text-green-800' :
                                                        'bg-red-100 text-red-800'
                                                }`}>
                                                {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-500 mb-4">
                                            Submitted {new Date(item.created_at).toLocaleDateString('en-US', {
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </p>

                                        {/* Guidelines */}
                                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                                            <p className="text-sm font-medium text-gray-700 mb-2">Review Criteria:</p>
                                            <ul className="text-sm text-gray-600 space-y-1">
                                                <li className="flex items-start">
                                                    <span className="mr-2">•</span>
                                                    Professional appearance and setting
                                                </li>
                                                <li className="flex items-start">
                                                    <span className="mr-2">•</span>
                                                    Clear audio and video quality
                                                </li>
                                                <li className="flex items-start">
                                                    <span className="mr-2">•</span>
                                                    No inappropriate or misleading content
                                                </li>
                                                <li className="flex items-start">
                                                    <span className="mr-2">•</span>
                                                    Accurate representation of services
                                                </li>
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Action buttons */}
                                    {item.status === 'pending' && (
                                        <div className="space-y-3">
                                            {rejectingId === item.id ? (
                                                <>
                                                    <textarea
                                                        value={rejectReason}
                                                        onChange={(e) => setRejectReason(e.target.value)}
                                                        placeholder="Enter rejection reason..."
                                                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                                                        rows={3}
                                                        aria-label="Rejection reason"
                                                    />
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => { setRejectingId(null); setRejectReason(''); }}
                                                            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
                                                        >
                                                            Cancel
                                                        </button>
                                                        <button
                                                            onClick={() => handleReject(item.id)}
                                                            disabled={actionLoading === item.id}
                                                            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50"
                                                        >
                                                            {actionLoading === item.id ? 'Rejecting...' : 'Confirm Reject'}
                                                        </button>
                                                    </div>
                                                </>
                                            ) : (
                                                <div className="flex gap-3">
                                                    <button
                                                        onClick={() => handleApprove(item.id)}
                                                        disabled={actionLoading === item.id}
                                                        className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold transition-colors disabled:opacity-50 flex items-center justify-center"
                                                    >
                                                        {actionLoading === item.id ? (
                                                            <>
                                                                <svg className="animate-spin -ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24">
                                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                                </svg>
                                                                Approving...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                                </svg>
                                                                Approve
                                                            </>
                                                        )}
                                                    </button>
                                                    <button
                                                        onClick={() => setRejectingId(item.id)}
                                                        className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold transition-colors flex items-center justify-center"
                                                    >
                                                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                                        </svg>
                                                        Reject
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Show rejection reason if already rejected */}
                                    {item.status === 'rejected' && item.rejection_reason && (
                                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                            <p className="text-sm font-medium text-red-800">Rejection Reason:</p>
                                            <p className="text-sm text-red-700 mt-1">{item.rejection_reason}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
