'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

interface AgentDecision {
    id: string;
    agent_type: 'orchestrator' | 'qualifier' | 'matcher' | 'explainer' | 'notifier';
    action: string;
    input_summary: string;
    output_summary: string;
    reasoning: string;
    timestamp: string;
    duration_ms: number;
    borrower_session_id?: string;
    algorithm_version: string;
    success: boolean;
}

interface AuditFilters {
    agent_type?: string;
    start_date?: string;
    end_date?: string;
    success?: boolean;
}

const AGENT_TYPES = [
    { value: 'all', label: 'All Agents' },
    { value: 'orchestrator', label: '🎭 Orchestrator' },
    { value: 'qualifier', label: '✅ Qualifier' },
    { value: 'matcher', label: '🎯 Matcher' },
    { value: 'explainer', label: '💬 Explainer' },
    { value: 'notifier', label: '📧 Notifier' },
];

const agentIcons: Record<string, string> = {
    orchestrator: '🎭',
    qualifier: '✅',
    matcher: '🎯',
    explainer: '💬',
    notifier: '📧',
};

export default function AgenticAuditPage() {
    const [decisions, setDecisions] = useState<AgentDecision[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filters, setFilters] = useState<AuditFilters>({});
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const fetchDecisions = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            params.set('page', page.toString());
            params.set('per_page', '20');
            if (filters.agent_type && filters.agent_type !== 'all') {
                params.set('agent_type', filters.agent_type);
            }
            if (filters.start_date) params.set('start_date', filters.start_date);
            if (filters.end_date) params.set('end_date', filters.end_date);
            if (filters.success !== undefined) params.set('success', filters.success.toString());

            const response = await apiClient.get(`/api/v1/agentic/audit?${params}`);
            setDecisions(response.data.decisions || []);
            setTotalPages(response.data.total_pages || 1);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch agent audit:', err);
            // Use demo data for preview
            setDecisions(getDemoDecisions());
            setTotalPages(1);
        } finally {
            setLoading(false);
        }
    }, [filters, page]);

    useEffect(() => {
        fetchDecisions();
    }, [fetchDecisions]);

    const handleFilterChange = (key: keyof AuditFilters, value: string) => {
        setFilters(prev => ({ ...prev, [key]: value || undefined }));
        setPage(1);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">
                        🤖 Agent Audit Log
                    </h1>
                    <p className="text-gray-500 mt-1">
                        Full transparency into AI agent decisions and reasoning
                    </p>
                </div>

                {/* Filters */}
                <div className="bg-white rounded-lg shadow-sm p-4 mb-6 flex flex-wrap gap-4">
                    <div className="flex-1 min-w-[200px]">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Agent Type
                        </label>
                        <select
                            value={filters.agent_type || 'all'}
                            onChange={(e) => handleFilterChange('agent_type', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                        >
                            {AGENT_TYPES.map(type => (
                                <option key={type.value} value={type.value}>{type.label}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex-1 min-w-[150px]">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Date
                        </label>
                        <input
                            type="date"
                            value={filters.start_date || ''}
                            onChange={(e) => handleFilterChange('start_date', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                        />
                    </div>

                    <div className="flex-1 min-w-[150px]">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            End Date
                        </label>
                        <input
                            type="date"
                            value={filters.end_date || ''}
                            onChange={(e) => handleFilterChange('end_date', e.target.value)}
                            className="w-full border border-gray-300 rounded-md px-3 py-2"
                        />
                    </div>

                    <div className="flex items-end">
                        <button
                            onClick={() => {
                                setFilters({});
                                setPage(1);
                            }}
                            className="px-4 py-2 text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md"
                        >
                            Clear Filters
                        </button>
                    </div>
                </div>

                {/* Stats Bar */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    {AGENT_TYPES.slice(1).map(type => {
                        const count = decisions.filter(d => d.agent_type === type.value).length;
                        return (
                            <div
                                key={type.value}
                                className="bg-white rounded-lg shadow-sm p-4 text-center"
                            >
                                <div className="text-2xl">{agentIcons[type.value]}</div>
                                <div className="text-2xl font-bold text-gray-900">{count}</div>
                                <div className="text-sm text-gray-500">{type.label.split(' ')[1]}</div>
                            </div>
                        );
                    })}
                </div>

                {/* Decisions List */}
                <div className="bg-white rounded-lg shadow-sm overflow-hidden">
                    {loading ? (
                        <div className="p-8 text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                            <p className="text-gray-500 mt-2">Loading audit log...</p>
                        </div>
                    ) : error ? (
                        <div className="p-8 text-center text-red-600">{error}</div>
                    ) : decisions.length === 0 ? (
                        <div className="p-8 text-center text-gray-500">
                            No agent decisions found matching your filters.
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {decisions.map(decision => (
                                <DecisionRow
                                    key={decision.id}
                                    decision={decision}
                                    expanded={expandedId === decision.id}
                                    onToggle={() => setExpandedId(
                                        expandedId === decision.id ? null : decision.id
                                    )}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex justify-center gap-2 mt-6">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-4 py-2 border rounded-md disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="px-4 py-2 text-gray-600">
                            Page {page} of {totalPages}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-4 py-2 border rounded-md disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

function DecisionRow({
    decision,
    expanded,
    onToggle
}: {
    decision: AgentDecision;
    expanded: boolean;
    onToggle: () => void;
}) {
    const icon = agentIcons[decision.agent_type] || '🤖';
    const formattedTime = new Date(decision.timestamp).toLocaleString();

    return (
        <div className={`${expanded ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
            <button
                onClick={onToggle}
                className="w-full text-left p-4 flex items-center gap-4"
            >
                <span className="text-2xl">{icon}</span>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900">{decision.action}</span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${decision.success
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                            {decision.success ? 'Success' : 'Failed'}
                        </span>
                        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">
                            v{decision.algorithm_version}
                        </span>
                    </div>
                    <p className="text-sm text-gray-600 truncate">{decision.input_summary}</p>
                </div>

                <div className="text-right text-sm text-gray-500 shrink-0">
                    <div>{formattedTime}</div>
                    <div>{decision.duration_ms}ms</div>
                </div>

                <svg
                    className={`w-5 h-5 text-gray-400 transform transition-transform ${expanded ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {expanded && (
                <div className="px-4 pb-4 pl-16">
                    <div className="bg-white rounded-lg p-4 shadow-sm space-y-4">
                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-1">Input</h4>
                            <pre className="text-sm bg-gray-50 p-3 rounded overflow-x-auto">
                                {decision.input_summary}
                            </pre>
                        </div>

                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-1">Output</h4>
                            <pre className="text-sm bg-gray-50 p-3 rounded overflow-x-auto">
                                {decision.output_summary}
                            </pre>
                        </div>

                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-1">Reasoning</h4>
                            <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
                                {decision.reasoning}
                            </p>
                        </div>

                        {decision.borrower_session_id && (
                            <div className="text-xs text-gray-500 pt-2 border-t">
                                Session: {decision.borrower_session_id}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function getDemoDecisions(): AgentDecision[] {
    return [
        {
            id: 'dec_001',
            agent_type: 'qualifier',
            action: 'Validate Borrower Profile',
            input_summary: '{"state": "CA", "credit_score": 720, "dti": 35}',
            output_summary: '{"valid": true, "eligible_loan_types": ["conventional", "fha", "va"]}',
            reasoning: 'Credit score exceeds 620 threshold for conventional. DTI of 35% is within 43% limit. CA is a supported state with 47 licensed LOs.',
            timestamp: new Date(Date.now() - 300000).toISOString(),
            duration_ms: 45,
            algorithm_version: '2.0.0',
            success: true,
            borrower_session_id: 'sess_abc123',
        },
        {
            id: 'dec_002',
            agent_type: 'matcher',
            action: 'Rank Loan Officers',
            input_summary: '{"session_id": "sess_abc123", "profile": {"state": "CA", "timeline": "immediate"}}',
            output_summary: '{"matches": 12, "top_match": "John at LoanPro", "score": 94}',
            reasoning: 'Prioritized LOs with avg pickup < 30s due to immediate timeline. Filtered to CA-licensed. Weighted: response_time 0.35, rating 0.25, volume 0.20, proximity 0.20.',
            timestamp: new Date(Date.now() - 295000).toISOString(),
            duration_ms: 128,
            algorithm_version: '2.0.0',
            success: true,
            borrower_session_id: 'sess_abc123',
        },
        {
            id: 'dec_003',
            agent_type: 'explainer',
            action: 'Generate Match Explanation',
            input_summary: '{"lo_id": "lo_john", "borrower_profile": {...}}',
            output_summary: '{"reasons": ["Licensed in CA", "First-time buyer specialist", "12s avg pickup"]}',
            reasoning: 'Generated 3 human-readable reasons. All reasons cite verified data sources: NMLS for licensing, internal tags for specialty, call logs for pickup time.',
            timestamp: new Date(Date.now() - 290000).toISOString(),
            duration_ms: 32,
            algorithm_version: '2.0.0',
            success: true,
        },
        {
            id: 'dec_004',
            agent_type: 'notifier',
            action: 'Send Lead Alert',
            input_summary: '{"lo_id": "lo_john", "borrower_intent": "hot", "channel": "push"}',
            output_summary: '{"sent": true, "delivery_id": "push_xyz789"}',
            reasoning: 'Borrower intent is HOT with immediate timeline. LO has push notifications enabled. Sent push with 5s timeout.',
            timestamp: new Date(Date.now() - 280000).toISOString(),
            duration_ms: 156,
            algorithm_version: '2.0.0',
            success: true,
        },
        {
            id: 'dec_005',
            agent_type: 'orchestrator',
            action: 'Coordinate Matching Flow',
            input_summary: '{"session_id": "sess_def456", "flow": "quick_match"}',
            output_summary: '{"steps_completed": 4, "total_time_ms": 361, "result": "success"}',
            reasoning: 'Executed quick_match flow: Qualifier → Matcher → Explainer → Notifier. All agents completed successfully within SLA.',
            timestamp: new Date(Date.now() - 200000).toISOString(),
            duration_ms: 361,
            algorithm_version: '2.0.0',
            success: true,
            borrower_session_id: 'sess_def456',
        },
    ];
}
