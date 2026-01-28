'use client';

import { useState, useEffect } from 'react';

interface AgentStatus {
    name: 'Qualifier' | 'Matcher' | 'Explainer' | 'Notifier';
    status: 'idle' | 'processing' | 'complete' | 'error';
    lastAction?: string;
    confidence?: number;
    duration_ms?: number;
}

interface CrewStatus {
    session_id: string;
    orchestrator_status: 'idle' | 'active' | 'complete';
    agents: AgentStatus[];
    started_at?: string;
    completed_at?: string;
}

interface AgenticCrewStatusProps {
    sessionId: string;
    pollInterval?: number;
    className?: string;
}

const AGENT_ICONS: Record<string, string> = {
    Qualifier: '🔍',
    Matcher: '🎯',
    Explainer: '💡',
    Notifier: '📧',
};

const AGENT_DESCRIPTIONS: Record<string, string> = {
    Qualifier: 'Validates borrower information',
    Matcher: 'Finds best LO matches',
    Explainer: 'Generates match explanations',
    Notifier: 'Sends notifications',
};

export function AgenticCrewStatus({ sessionId, pollInterval = 2000, className = '' }: AgenticCrewStatusProps) {
    const [crewStatus, setCrewStatus] = useState<CrewStatus | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;

        async function fetchStatus() {
            try {
                const response = await fetch(`/api/v1/agentic/crew/status/${sessionId}`);
                if (!response.ok) throw new Error('Failed to fetch crew status');
                const data = await response.json();
                if (isMounted) {
                    setCrewStatus(data);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    setError('Unable to load crew status');
                }
            }
        }

        fetchStatus();

        // Poll for updates if crew is still active
        const interval = setInterval(() => {
            if (crewStatus?.orchestrator_status !== 'complete') {
                fetchStatus();
            }
        }, pollInterval);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, [sessionId, pollInterval, crewStatus?.orchestrator_status]);

    if (error) {
        return (
            <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
                <p className="text-red-600 text-sm">{error}</p>
            </div>
        );
    }

    if (!crewStatus) {
        return (
            <div className={`bg-gray-50 rounded-lg p-6 animate-pulse ${className}`}>
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className={`bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${crewStatus.orchestrator_status === 'active'
                            ? 'bg-green-500 animate-pulse'
                            : crewStatus.orchestrator_status === 'complete'
                                ? 'bg-blue-500'
                                : 'bg-gray-400'
                        }`} />
                    <h3 className="text-lg font-semibold text-gray-800">
                        AI Matching Crew
                    </h3>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${crewStatus.orchestrator_status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : crewStatus.orchestrator_status === 'complete'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-600'
                    }`}>
                    {crewStatus.orchestrator_status === 'active' ? 'Processing...' :
                        crewStatus.orchestrator_status === 'complete' ? 'Complete' : 'Idle'}
                </span>
            </div>

            {/* Agent Pipeline */}
            <div className="grid grid-cols-4 gap-4">
                {crewStatus.agents.map((agent, index) => (
                    <div key={agent.name} className="relative">
                        {/* Connection line */}
                        {index < crewStatus.agents.length - 1 && (
                            <div className={`absolute top-1/2 -right-2 w-4 h-0.5 ${agent.status === 'complete' ? 'bg-green-400' : 'bg-gray-300'
                                }`} />
                        )}

                        {/* Agent Card */}
                        <div className={`bg-white rounded-lg p-4 border-2 transition-all duration-300 ${agent.status === 'processing'
                                ? 'border-indigo-400 shadow-lg shadow-indigo-100 scale-105'
                                : agent.status === 'complete'
                                    ? 'border-green-400'
                                    : agent.status === 'error'
                                        ? 'border-red-400'
                                        : 'border-gray-200'
                            }`}>
                            {/* Agent Icon */}
                            <div className="text-2xl mb-2">
                                {AGENT_ICONS[agent.name]}
                            </div>

                            {/* Agent Name */}
                            <h4 className="font-medium text-gray-800 text-sm">{agent.name}</h4>

                            {/* Description */}
                            <p className="text-xs text-gray-500 mb-2">
                                {AGENT_DESCRIPTIONS[agent.name]}
                            </p>

                            {/* Status Indicator */}
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${agent.status === 'processing' ? 'bg-indigo-500 animate-pulse' :
                                        agent.status === 'complete' ? 'bg-green-500' :
                                            agent.status === 'error' ? 'bg-red-500' :
                                                'bg-gray-300'
                                    }`} />
                                <span className={`text-xs ${agent.status === 'processing' ? 'text-indigo-600' :
                                        agent.status === 'complete' ? 'text-green-600' :
                                            agent.status === 'error' ? 'text-red-600' :
                                                'text-gray-400'
                                    }`}>
                                    {agent.status === 'processing' ? 'Working...' :
                                        agent.status === 'complete' ? 'Done' :
                                            agent.status === 'error' ? 'Error' :
                                                'Waiting'}
                                </span>
                            </div>

                            {/* Confidence Score */}
                            {agent.confidence !== undefined && agent.status === 'complete' && (
                                <div className="mt-2">
                                    <div className="flex justify-between text-xs text-gray-500">
                                        <span>Confidence</span>
                                        <span>{Math.round(agent.confidence * 100)}%</span>
                                    </div>
                                    <div className="w-full h-1 bg-gray-200 rounded-full mt-1">
                                        <div
                                            className="h-full bg-green-500 rounded-full transition-all duration-500"
                                            style={{ width: `${agent.confidence * 100}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* Duration */}
                            {agent.duration_ms !== undefined && (
                                <p className="text-xs text-gray-400 mt-1">
                                    {agent.duration_ms}ms
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Last Action */}
            {crewStatus.agents.find(a => a.lastAction) && (
                <div className="mt-4 text-xs text-gray-500 bg-white/50 rounded-lg p-3">
                    <span className="font-medium">Last Action: </span>
                    {crewStatus.agents.find(a => a.status === 'processing')?.lastAction ||
                        crewStatus.agents.filter(a => a.lastAction).pop()?.lastAction}
                </div>
            )}
        </div>
    );
}

export default AgenticCrewStatus;
