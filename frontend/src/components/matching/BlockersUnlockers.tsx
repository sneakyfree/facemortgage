'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api/client';

interface Blocker {
    id: string;
    category: string;
    title: string;
    description: string;
    severity: number;
    priority: 'quick_win' | '30_days' | '90_days';
    can_proceed: boolean;
}

interface Unlocker {
    blocker_id: string;
    action: string;
    detailed_steps: string[];
    estimated_time: string;
    resources: string[];
    success_probability: number;
}

interface BlockerAnalysis {
    total_blockers: number;
    blocking_approval: number;
    limiting_options: number;
    blockers: Blocker[];
    unlockers: Unlocker[];
    quick_wins: Unlocker[];
    thirty_day_fixes: Unlocker[];
    ninety_day_fixes: Unlocker[];
    recommended_loan_types: string[];
    overall_readiness_score: number;
}

interface BlockerInputs {
    credit_score?: number;
    dti_ratio?: number;
    timeline_days?: number;
    employment_type?: 'w2' | 'self_employed' | 'retired';
    years_employment?: number;
    has_gift_funds?: boolean;
    property_type?: string;
}

const priorityColors = {
    quick_win: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-800', label: '🟢 Quick Win (24h)' },
    '30_days': { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-800', label: '🟡 30 Days' },
    '90_days': { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-800', label: '🔴 90+ Days' },
};

const categoryIcons: Record<string, string> = {
    credit: '💳',
    dti: '📊',
    timeline: '⏰',
    documentation: '📄',
    income: '💰',
    property: '🏠',
    state_license: '📋',
};

export function BlockersUnlockers({ inputs }: { inputs: BlockerInputs }) {
    const [analysis, setAnalysis] = useState<BlockerAnalysis | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [expandedBlocker, setExpandedBlocker] = useState<string | null>(null);

    useEffect(() => {
        async function fetchAnalysis() {
            if (!inputs.credit_score && !inputs.dti_ratio) return;

            setLoading(true);
            setError(null);

            try {
                const response = await apiClient.post('/api/v1/matching/blockers', inputs);
                setAnalysis(response.data);
            } catch (err) {
                setError('Unable to analyze blockers. Please try again.');
                console.error('Blockers analysis error:', err);
            } finally {
                setLoading(false);
            }
        }

        fetchAnalysis();
    }, [inputs]);

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600">{error}</p>
            </div>
        );
    }

    if (!analysis) {
        return null;
    }

    const getUnlockerForBlocker = (blockerId: string) => {
        return analysis.unlockers.find(u => u.blocker_id === blockerId);
    };

    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
            {/* Header with readiness score */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
                <div className="flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-bold">Your Loan Readiness Analysis</h2>
                        <p className="text-blue-100 mt-1">
                            {analysis.total_blockers === 0
                                ? "Great news! No blockers found."
                                : `${analysis.total_blockers} item${analysis.total_blockers > 1 ? 's' : ''} to address`}
                        </p>
                    </div>

                    {/* Readiness Score Circle */}
                    <div className="relative w-24 h-24">
                        <svg className="w-24 h-24 transform -rotate-90">
                            <circle
                                cx="48"
                                cy="48"
                                r="40"
                                stroke="rgba(255,255,255,0.3)"
                                strokeWidth="8"
                                fill="none"
                            />
                            <circle
                                cx="48"
                                cy="48"
                                r="40"
                                stroke="white"
                                strokeWidth="8"
                                fill="none"
                                strokeDasharray={`${analysis.overall_readiness_score * 2.51} 251`}
                                strokeLinecap="round"
                            />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-2xl font-bold">{analysis.overall_readiness_score}</span>
                        </div>
                    </div>
                </div>

                {/* Recommended loan types */}
                {analysis.recommended_loan_types.length > 0 && (
                    <div className="mt-4">
                        <p className="text-sm text-blue-100">Eligible loan types:</p>
                        <div className="flex flex-wrap gap-2 mt-1">
                            {analysis.recommended_loan_types.map(type => (
                                <span
                                    key={type}
                                    className="px-2 py-1 bg-white/20 rounded text-sm uppercase"
                                >
                                    {type}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Fix List by Priority */}
            <div className="p-6 space-y-6">
                {/* Quick Wins */}
                {analysis.quick_wins.length > 0 && (
                    <section>
                        <h3 className="flex items-center gap-2 text-lg font-semibold text-green-700 mb-3">
                            🟢 Quick Wins (Fix in 24 hours)
                        </h3>
                        <div className="space-y-3">
                            {analysis.blockers
                                .filter(b => b.priority === 'quick_win')
                                .map(blocker => (
                                    <BlockerCard
                                        key={blocker.id}
                                        blocker={blocker}
                                        unlocker={getUnlockerForBlocker(blocker.id)}
                                        expanded={expandedBlocker === blocker.id}
                                        onToggle={() => setExpandedBlocker(
                                            expandedBlocker === blocker.id ? null : blocker.id
                                        )}
                                    />
                                ))}
                        </div>
                    </section>
                )}

                {/* 30 Day Fixes */}
                {analysis.thirty_day_fixes.length > 0 && (
                    <section>
                        <h3 className="flex items-center gap-2 text-lg font-semibold text-yellow-700 mb-3">
                            🟡 30-Day Actions
                        </h3>
                        <div className="space-y-3">
                            {analysis.blockers
                                .filter(b => b.priority === '30_days')
                                .map(blocker => (
                                    <BlockerCard
                                        key={blocker.id}
                                        blocker={blocker}
                                        unlocker={getUnlockerForBlocker(blocker.id)}
                                        expanded={expandedBlocker === blocker.id}
                                        onToggle={() => setExpandedBlocker(
                                            expandedBlocker === blocker.id ? null : blocker.id
                                        )}
                                    />
                                ))}
                        </div>
                    </section>
                )}

                {/* 90 Day Fixes */}
                {analysis.ninety_day_fixes.length > 0 && (
                    <section>
                        <h3 className="flex items-center gap-2 text-lg font-semibold text-red-700 mb-3">
                            🔴 Long-Term Improvements (90+ days)
                        </h3>
                        <div className="space-y-3">
                            {analysis.blockers
                                .filter(b => b.priority === '90_days')
                                .map(blocker => (
                                    <BlockerCard
                                        key={blocker.id}
                                        blocker={blocker}
                                        unlocker={getUnlockerForBlocker(blocker.id)}
                                        expanded={expandedBlocker === blocker.id}
                                        onToggle={() => setExpandedBlocker(
                                            expandedBlocker === blocker.id ? null : blocker.id
                                        )}
                                    />
                                ))}
                        </div>
                    </section>
                )}

                {/* All Clear */}
                {analysis.total_blockers === 0 && (
                    <div className="text-center py-8">
                        <div className="text-5xl mb-4">🎉</div>
                        <h3 className="text-xl font-semibold text-gray-800">You're Ready!</h3>
                        <p className="text-gray-600 mt-2">
                            No blockers found. You're in great shape to proceed with your loan application.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

function BlockerCard({
    blocker,
    unlocker,
    expanded,
    onToggle
}: {
    blocker: Blocker;
    unlocker?: Unlocker;
    expanded: boolean;
    onToggle: () => void;
}) {
    const priority = priorityColors[blocker.priority];
    const icon = categoryIcons[blocker.category] || '⚠️';

    return (
        <div className={`border-l-4 ${priority.border} ${priority.bg} rounded-r-lg overflow-hidden`}>
            <button
                onClick={onToggle}
                className="w-full text-left p-4 flex items-start gap-3 hover:bg-opacity-80 transition-colors"
            >
                <span className="text-2xl">{icon}</span>
                <div className="flex-1">
                    <div className="flex items-center gap-2">
                        <h4 className={`font-semibold ${priority.text}`}>{blocker.title}</h4>
                        {!blocker.can_proceed && (
                            <span className="text-xs bg-red-600 text-white px-2 py-0.5 rounded-full">
                                Blocking
                            </span>
                        )}
                    </div>
                    <p className="text-gray-600 text-sm mt-1">{blocker.description}</p>
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

            {expanded && unlocker && (
                <div className="px-4 pb-4 pt-0 ml-11">
                    <div className="bg-white rounded-lg p-4 shadow-sm">
                        <h5 className="font-semibold text-gray-800 mb-2">
                            ✨ How to Fix: {unlocker.action}
                        </h5>

                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                            <span>⏱️ {unlocker.estimated_time}</span>
                            <span>📈 {Math.round(unlocker.success_probability * 100)}% success rate</span>
                        </div>

                        <ol className="space-y-2">
                            {unlocker.detailed_steps.map((step, idx) => (
                                <li key={idx} className="flex gap-2 text-sm text-gray-700">
                                    <span className="flex-shrink-0 w-5 h-5 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-semibold">
                                        {idx + 1}
                                    </span>
                                    {step}
                                </li>
                            ))}
                        </ol>

                        {unlocker.resources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-100">
                                <p className="text-xs text-gray-500 mb-1">Resources:</p>
                                <div className="flex flex-wrap gap-2">
                                    {unlocker.resources.map((resource, idx) => (
                                        <span key={idx} className="text-xs text-blue-600 hover:underline cursor-pointer">
                                            {resource}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default BlockersUnlockers;
