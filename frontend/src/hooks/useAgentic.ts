'use client';

import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

/**
 * Agentic Intelligence Hooks - Phase 4
 * 
 * Provides hooks for AI-powered features:
 * - Intent classification
 * - Smart LO recommendations  
 * - Follow-up suggestions
 * - Conversation summarization
 */

// Intent types
export type BorrowerIntent = 'hot' | 'warm' | 'exploring' | 'refinance' | 'preapproval' | 'unknown';

export interface IntentSignal {
    signal_type: string;
    value: string;
    weight: number;
    explanation: string;
}

export interface IntentClassification {
    intent: BorrowerIntent;
    confidence: number;
    signals: IntentSignal[];
    recommended_actions: string[];
    urgency_score: number;
}

// Smart recommendation types
export interface SmartRecommendation {
    lo_id: string;
    lo_name: string;
    recommendation_score: number;
    reasons: string[];
    success_pattern_match: string | null;
    predicted_conversion_rate: number;
}

// Follow-up types
export interface FollowUpSuggestion {
    action_type: 'email' | 'sms' | 'call' | 'in_app';
    suggested_time: string;
    priority: number;
    subject: string;
    message_template: string;
    reason: string;
}

// Conversation summary types
export interface ConversationSummary {
    call_id: string;
    duration_seconds: number;
    key_topics: string[];
    borrower_questions: string[];
    lo_commitments: string[];
    next_steps: string[];
    sentiment: 'positive' | 'neutral' | 'negative';
    summary_text: string;
}

/**
 * Hook for classifying borrower intent
 */
export function useIntentClassifier() {
    const [result, setResult] = useState<IntentClassification | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const classifyIntent = useCallback(async (params: {
        timeline: string;
        loan_purpose: string;
        property_identified?: boolean;
        has_agent?: boolean;
        notes?: string;
    }) => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<IntentClassification>(
                '/agentic/classify-intent',
                params
            );
            setResult(response.data);
            return response.data;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Classification failed';
            setError(message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return { result, loading, error, classifyIntent };
}

/**
 * Hook for smart LO recommendations
 */
export function useSmartRecommendations() {
    const [recommendations, setRecommendations] = useState<SmartRecommendation[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getRecommendations = useCallback(async (params: {
        state: string;
        first_time_buyer?: boolean;
        preferred_language?: string;
        loan_amount?: number;
        limit?: number;
    }) => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<{ recommendations: SmartRecommendation[] }>(
                '/agentic/smart-recommend',
                params
            );
            setRecommendations(response.data.recommendations);
            return response.data.recommendations;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Recommendations failed';
            setError(message);
            return [];
        } finally {
            setLoading(false);
        }
    }, []);

    return { recommendations, loading, error, getRecommendations };
}

/**
 * Hook for follow-up suggestions
 */
export function useFollowUpSuggestions() {
    const [suggestions, setSuggestions] = useState<FollowUpSuggestion[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getSuggestions = useCallback(async (params: {
        borrower_id?: string;
        last_activity_iso?: string;
        intent?: string;
        calls_completed?: number;
        has_email?: boolean;
        has_phone?: boolean;
    }) => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<{ suggestions: FollowUpSuggestion[] }>(
                '/agentic/suggest-followups',
                params
            );
            setSuggestions(response.data.suggestions);
            return response.data.suggestions;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to get suggestions';
            setError(message);
            return [];
        } finally {
            setLoading(false);
        }
    }, []);

    return { suggestions, loading, error, getSuggestions };
}

/**
 * Hook for conversation summarization
 */
export function useConversationSummary() {
    const [summary, setSummary] = useState<ConversationSummary | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const summarize = useCallback(async (params: {
        call_id: string;
        duration_seconds: number;
        lo_notes?: string;
    }) => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<ConversationSummary>(
                '/agentic/summarize-call',
                params
            );
            setSummary(response.data);
            return response.data;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Summarization failed';
            setError(message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    return { summary, loading, error, summarize };
}

// Helper functions
export function getIntentColor(intent: BorrowerIntent): string {
    switch (intent) {
        case 'hot': return 'text-red-600';
        case 'warm': return 'text-orange-500';
        case 'exploring': return 'text-blue-500';
        case 'refinance': return 'text-purple-600';
        case 'preapproval': return 'text-green-600';
        default: return 'text-gray-500';
    }
}

export function getIntentBadgeClass(intent: BorrowerIntent): string {
    switch (intent) {
        case 'hot': return 'bg-red-100 text-red-800';
        case 'warm': return 'bg-orange-100 text-orange-800';
        case 'exploring': return 'bg-blue-100 text-blue-800';
        case 'refinance': return 'bg-purple-100 text-purple-800';
        case 'preapproval': return 'bg-green-100 text-green-800';
        default: return 'bg-gray-100 text-gray-600';
    }
}

export function getUrgencyLabel(score: number): string {
    if (score >= 8) return 'Critical';
    if (score >= 6) return 'High';
    if (score >= 4) return 'Medium';
    return 'Low';
}

export function getSentimentIcon(sentiment: string): string {
    switch (sentiment) {
        case 'positive': return '😊';
        case 'negative': return '😟';
        default: return '😐';
    }
}

export function getPriorityLabel(priority: number): string {
    switch (priority) {
        case 1: return 'Urgent';
        case 2: return 'High';
        case 3: return 'Medium';
        case 4: return 'Low';
        default: return 'Normal';
    }
}
