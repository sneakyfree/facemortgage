'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface AuditLog {
    id: string;
    user_id: string;
    user_email: string;
    action: string;
    entity_type: string;
    entity_id: string;
    details: Record<string, any>;
    ip_address: string;
    user_agent: string;
    created_at: string;
}

export default function AuditLogsPage() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [actionFilter, setActionFilter] = useState('');
    const [entityFilter, setEntityFilter] = useState('');

    useEffect(() => {
        loadLogs();
    }, [page, actionFilter, entityFilter]);

    const loadLogs = async () => {
        setLoading(true);
        try {
            const { data } = await apiClient.get('/audit/logs', {
                params: {
                    page,
                    limit: 20,
                    action: actionFilter || undefined,
                    entity_type: entityFilter || undefined,
                }
            });
            setLogs(data.logs || []);
            setTotalPages(data.total_pages || 1);
        } catch (err) {
            console.error('Failed to load audit logs:', err);
        } finally {
            setLoading(false);
        }
    };

    const actionColors: Record<string, string> = {
        create: 'bg-green-100 text-green-800',
        update: 'bg-blue-100 text-blue-800',
        delete: 'bg-red-100 text-red-800',
        login: 'bg-purple-100 text-purple-800',
        logout: 'bg-gray-100 text-gray-800',
        approve: 'bg-green-100 text-green-800',
        reject: 'bg-red-100 text-red-800',
    };

    return (
        <div className="p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
                <p className="mt-1 text-sm text-gray-500">
                    Track all administrative actions and system changes
                </p>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <select
                    value={actionFilter}
                    onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                    className="px-4 py-2 border border-gray-300 rounded-lg"
                    aria-label="Filter by action"
                >
                    <option value="">All Actions</option>
                    <option value="create">Create</option>
                    <option value="update">Update</option>
                    <option value="delete">Delete</option>
                    <option value="login">Login</option>
                    <option value="approve">Approve</option>
                    <option value="reject">Reject</option>
                </select>
                <select
                    value={entityFilter}
                    onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
                    className="px-4 py-2 border border-gray-300 rounded-lg"
                    aria-label="Filter by entity"
                >
                    <option value="">All Entities</option>
                    <option value="user">User</option>
                    <option value="video">Video</option>
                    <option value="review">Review</option>
                    <option value="lead">Lead</option>
                    <option value="subscription">Subscription</option>
                </select>
            </div>

            {/* Logs table */}
            <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
                {loading ? (
                    <div className="animate-pulse p-6 space-y-4">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="h-16 bg-gray-100 rounded" />
                        ))}
                    </div>
                ) : logs.length === 0 ? (
                    <div className="text-center py-12">
                        <p className="text-gray-500">No audit logs found</p>
                    </div>
                ) : (
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Timestamp</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">User</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Action</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Entity</th>
                                <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Details</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {logs.map(log => (
                                <tr key={log.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        {new Date(log.created_at).toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-medium text-gray-900">{log.user_email}</div>
                                        <div className="text-xs text-gray-500">{log.ip_address}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${actionColors[log.action] || 'bg-gray-100 text-gray-800'}`}>
                                            {log.action}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm text-gray-900">{log.entity_type}</div>
                                        <div className="text-xs text-gray-500 font-mono">{log.entity_id?.slice(0, 8)}...</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <pre className="text-xs text-gray-600 max-w-xs truncate">
                                            {JSON.stringify(log.details || {})}
                                        </pre>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-4 py-2 border rounded-lg disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="text-sm text-gray-600">
                            Page {page} of {totalPages}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-4 py-2 border rounded-lg disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
