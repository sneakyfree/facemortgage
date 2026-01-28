'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface CallRecord {
    id: string;
    borrower_name: string;
    started_at: string;
    ended_at: string;
    duration_seconds: number;
    status: 'completed' | 'missed' | 'declined' | 'no_answer';
    quality_score?: number;
    quality_metrics?: {
        video_quality: number;
        audio_quality: number;
        connection_stability: number;
        latency_ms: number;
        packet_loss_percent: number;
    };
}

export default function CallHistoryPage() {
    const [calls, setCalls] = useState<CallRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'completed' | 'missed'>('all');
    const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);

    useEffect(() => {
        loadCalls();
    }, [filter]);

    const loadCalls = async () => {
        setLoading(true);
        try {
            const { data } = await apiClient.get('/calls/history', {
                params: { status: filter === 'all' ? undefined : filter }
            });
            setCalls(data.calls || []);
        } catch (err) {
            console.error('Failed to load calls:', err);
        } finally {
            setLoading(false);
        }
    };

    const missedCount = calls.filter(c => c.status === 'missed' || c.status === 'no_answer').length;

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getQualityColor = (score: number) => {
        if (score >= 80) return 'text-green-600';
        if (score >= 60) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getQualityLabel = (score: number) => {
        if (score >= 80) return 'Excellent';
        if (score >= 60) return 'Good';
        if (score >= 40) return 'Fair';
        return 'Poor';
    };

    if (loading) {
        return (
            <div className="p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-10 bg-gray-200 rounded w-1/4" />
                    {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-20 bg-gray-200 rounded-lg" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-5xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Call History</h1>
                    <p className="mt-1 text-gray-600">View your past calls and quality metrics</p>
                </div>
                <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value as any)}
                    className="px-4 py-2 border rounded-lg"
                >
                    <option value="all">All Calls</option>
                    <option value="completed">Completed</option>
                    <option value="missed">Missed ({missedCount})</option>
                </select>
            </div>

            {/* Missed calls alert */}
            {missedCount > 0 && filter === 'all' && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center">
                        <svg className="w-6 h-6 text-red-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" />
                        </svg>
                        <div>
                            <p className="font-medium text-red-800">You have {missedCount} missed call{missedCount !== 1 ? 's' : ''}</p>
                            <p className="text-sm text-red-600">Consider following up with these borrowers</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setFilter('missed')}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                    >
                        View Missed Calls
                    </button>
                </div>
            )}

            {/* Call list */}
            <div className="bg-white rounded-xl border overflow-hidden">
                {calls.length === 0 ? (
                    <div className="text-center py-12">
                        <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Calls Yet</h3>
                        <p className="text-gray-600">Your call history will appear here</p>
                    </div>
                ) : (
                    <div className="divide-y">
                        {calls.map(call => (
                            <div
                                key={call.id}
                                className="p-4 hover:bg-gray-50 cursor-pointer"
                                onClick={() => setSelectedCall(call)}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-4 ${call.status === 'completed' ? 'bg-green-100' :
                                                call.status === 'missed' || call.status === 'no_answer' ? 'bg-red-100' :
                                                    'bg-gray-100'
                                            }`}>
                                            {call.status === 'completed' ? (
                                                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                            ) : (
                                                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                                                </svg>
                                            )}
                                        </div>
                                        <div>
                                            <p className="font-medium text-gray-900">{call.borrower_name}</p>
                                            <p className="text-sm text-gray-500">
                                                {new Date(call.started_at).toLocaleDateString()} at {new Date(call.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        {call.status === 'completed' && (
                                            <>
                                                <p className="text-gray-900">{formatDuration(call.duration_seconds)}</p>
                                                {call.quality_score !== undefined && (
                                                    <p className={`text-sm ${getQualityColor(call.quality_score)}`}>
                                                        {getQualityLabel(call.quality_score)} ({call.quality_score}%)
                                                    </p>
                                                )}
                                            </>
                                        )}
                                        {(call.status === 'missed' || call.status === 'no_answer') && (
                                            <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">Missed</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Quality metrics modal */}
            {selectedCall && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl max-w-md w-full p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-gray-900">Call Details</h2>
                            <button
                                onClick={() => setSelectedCall(null)}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-500">Caller</p>
                                <p className="font-medium text-gray-900">{selectedCall.borrower_name}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Date & Time</p>
                                <p className="font-medium text-gray-900">
                                    {new Date(selectedCall.started_at).toLocaleString()}
                                </p>
                            </div>
                            {selectedCall.status === 'completed' && (
                                <>
                                    <div>
                                        <p className="text-sm text-gray-500">Duration</p>
                                        <p className="font-medium text-gray-900">{formatDuration(selectedCall.duration_seconds)}</p>
                                    </div>
                                    {selectedCall.quality_metrics && (
                                        <div>
                                            <p className="text-sm text-gray-500 mb-3">Call Quality</p>
                                            <div className="space-y-3">
                                                <QualityBar label="Video Quality" value={selectedCall.quality_metrics.video_quality} />
                                                <QualityBar label="Audio Quality" value={selectedCall.quality_metrics.audio_quality} />
                                                <QualityBar label="Connection" value={selectedCall.quality_metrics.connection_stability} />
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-gray-500">Latency</span>
                                                    <span className="text-gray-900">{selectedCall.quality_metrics.latency_ms}ms</span>
                                                </div>
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-gray-500">Packet Loss</span>
                                                    <span className="text-gray-900">{selectedCall.quality_metrics.packet_loss_percent}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>

                        <button
                            onClick={() => setSelectedCall(null)}
                            className="w-full mt-6 px-4 py-2 border rounded-lg hover:bg-gray-50"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

function QualityBar({ label, value }: { label: string; value: number }) {
    const getColor = (v: number) => {
        if (v >= 80) return 'bg-green-500';
        if (v >= 60) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    return (
        <div>
            <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-500">{label}</span>
                <span className="text-gray-900">{value}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full ${getColor(value)}`}
                    style={{ width: `${value}%` }}
                />
            </div>
        </div>
    );
}
