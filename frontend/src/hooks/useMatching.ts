'use client';

import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

/**
 * Borrower Matching Hooks
 * 
 * Provides React hooks for the agentic matching system,
 * including intake form state and matching results.
 */

// Types matching backend schemas
export type LoanPurpose = 'purchase' | 'refinance' | 'cash_out' | 'heloc';
export type PropertyType = 'single_family' | 'condo' | 'townhouse' | 'multi_unit' | 'manufactured';
export type Timeline = 'immediate' | '30_days' | 'exploring';
export type SpecialNeed =
    | 'first_time'
    | 'self_employed'
    | 'jumbo'
    | 'va_eligible'
    | 'fha'
    | 'low_down'
    | 'investment'
    | 'poor_credit';

export interface BorrowerProfile {
    state: string;
    loan_purpose: LoanPurpose;
    property_type: PropertyType;
    timeline: Timeline;
    special_needs: SpecialNeed[];
    preferred_language?: string;
    loan_amount_estimate?: number;
}

export interface MatchReason {
    category: string;
    reason: string;
    weight: number;
    verified: boolean;
}

export interface LOMatch {
    lo_id: string;
    lo_name: string;
    company_name: string | null;
    avatar_url: string | null;
    nmls_id: string | null;
    nmls_verified: boolean;
    match_score: number;
    match_reasons: MatchReason[];
    availability: 'online_now' | 'busy' | 'offline';
    avg_pickup_seconds: number | null;
    avg_rating: number;
    total_reviews: number;
    years_experience: number | null;
    has_video: boolean;
    specialty_names: string[];
    language_codes: string[];
}

export interface MatchingResult {
    borrower_profile: BorrowerProfile;
    matches: LOMatch[];
    total_eligible: number;
    algorithm_version: string;
    computed_at: string;
    input_hash: string;
    session_id: string | null;
}

// Initial state for borrower intake form
const initialBorrowerState: BorrowerProfile = {
    state: '',
    loan_purpose: 'purchase',
    property_type: 'single_family',
    timeline: 'exploring',
    special_needs: [],
    preferred_language: 'en',
};

/**
 * Hook for managing borrower intake form state
 */
export function useBorrowerIntake() {
    const [profile, setProfile] = useState<BorrowerProfile>(initialBorrowerState);
    const [uncertainties, setUncertainties] = useState<string[]>([]);

    const updateProfile = useCallback((updates: Partial<BorrowerProfile>) => {
        setProfile(prev => ({ ...prev, ...updates }));
    }, []);

    const toggleSpecialNeed = useCallback((need: SpecialNeed) => {
        setProfile(prev => ({
            ...prev,
            special_needs: prev.special_needs.includes(need)
                ? prev.special_needs.filter(n => n !== need)
                : [...prev.special_needs, need]
        }));
    }, []);

    const markUncertain = useCallback((field: string) => {
        setUncertainties(prev =>
            prev.includes(field) ? prev : [...prev, field]
        );
    }, []);

    const clearUncertain = useCallback((field: string) => {
        setUncertainties(prev => prev.filter(f => f !== field));
    }, []);

    const isValid = useCallback(() => {
        return Boolean(profile.state.length === 2 && profile.loan_purpose);
    }, [profile]);

    const reset = useCallback(() => {
        setProfile(initialBorrowerState);
        setUncertainties([]);
    }, []);

    return {
        profile,
        uncertainties,
        updateProfile,
        toggleSpecialNeed,
        markUncertain,
        clearUncertain,
        isValid,
        reset,
    };
}

/**
 * Hook for fetching matching results
 */
export function useMatching() {
    const [results, setResults] = useState<MatchingResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const findMatches = useCallback(async (profile: BorrowerProfile) => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<MatchingResult>('/matching/find', profile);
            setResults(response.data);
            return response.data;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to find matches';
            setError(message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const quickMatch = useCallback(async (state: string, loanPurpose: LoanPurpose = 'purchase') => {
        setLoading(true);
        setError(null);

        try {
            const response = await apiClient.post<MatchingResult>('/matching/quick', {
                state,
                loan_purpose: loanPurpose,
            });
            setResults(response.data);
            return response.data;
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to find matches';
            setError(message);
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const clearResults = useCallback(() => {
        setResults(null);
        setError(null);
    }, []);

    return {
        results,
        loading,
        error,
        findMatches,
        quickMatch,
        clearResults,
    };
}

// Human-readable labels for form fields
export const LOAN_PURPOSE_LABELS: Record<LoanPurpose, string> = {
    purchase: 'Buy a home',
    refinance: 'Refinance existing mortgage',
    cash_out: 'Cash-out refinance',
    heloc: 'Home equity line of credit',
};

export const PROPERTY_TYPE_LABELS: Record<PropertyType, string> = {
    single_family: 'Single-family home',
    condo: 'Condominium',
    townhouse: 'Townhouse',
    multi_unit: 'Multi-unit property (2-4 units)',
    manufactured: 'Manufactured / mobile home',
};

export const TIMELINE_LABELS: Record<Timeline, string> = {
    immediate: 'Ready now (within 1 week)',
    '30_days': 'Soon (1-4 weeks)',
    exploring: 'Just exploring options',
};

export const SPECIAL_NEED_LABELS: Record<SpecialNeed, { label: string; description: string }> = {
    first_time: {
        label: 'First-time homebuyer',
        description: 'Never owned a home before'
    },
    self_employed: {
        label: 'Self-employed',
        description: 'Income from own business'
    },
    jumbo: {
        label: 'Jumbo loan',
        description: 'Loan above $766,550'
    },
    va_eligible: {
        label: 'VA eligible',
        description: 'Veteran or active military'
    },
    fha: {
        label: 'FHA loan',
        description: 'Lower down payment option'
    },
    low_down: {
        label: 'Low down payment',
        description: 'Less than 20% down'
    },
    investment: {
        label: 'Investment property',
        description: 'Rental or second home'
    },
    poor_credit: {
        label: 'Credit challenges',
        description: 'Score below 620'
    },
};

export const US_STATES = [
    { code: 'AL', name: 'Alabama' },
    { code: 'AK', name: 'Alaska' },
    { code: 'AZ', name: 'Arizona' },
    { code: 'AR', name: 'Arkansas' },
    { code: 'CA', name: 'California' },
    { code: 'CO', name: 'Colorado' },
    { code: 'CT', name: 'Connecticut' },
    { code: 'DE', name: 'Delaware' },
    { code: 'FL', name: 'Florida' },
    { code: 'GA', name: 'Georgia' },
    { code: 'HI', name: 'Hawaii' },
    { code: 'ID', name: 'Idaho' },
    { code: 'IL', name: 'Illinois' },
    { code: 'IN', name: 'Indiana' },
    { code: 'IA', name: 'Iowa' },
    { code: 'KS', name: 'Kansas' },
    { code: 'KY', name: 'Kentucky' },
    { code: 'LA', name: 'Louisiana' },
    { code: 'ME', name: 'Maine' },
    { code: 'MD', name: 'Maryland' },
    { code: 'MA', name: 'Massachusetts' },
    { code: 'MI', name: 'Michigan' },
    { code: 'MN', name: 'Minnesota' },
    { code: 'MS', name: 'Mississippi' },
    { code: 'MO', name: 'Missouri' },
    { code: 'MT', name: 'Montana' },
    { code: 'NE', name: 'Nebraska' },
    { code: 'NV', name: 'Nevada' },
    { code: 'NH', name: 'New Hampshire' },
    { code: 'NJ', name: 'New Jersey' },
    { code: 'NM', name: 'New Mexico' },
    { code: 'NY', name: 'New York' },
    { code: 'NC', name: 'North Carolina' },
    { code: 'ND', name: 'North Dakota' },
    { code: 'OH', name: 'Ohio' },
    { code: 'OK', name: 'Oklahoma' },
    { code: 'OR', name: 'Oregon' },
    { code: 'PA', name: 'Pennsylvania' },
    { code: 'RI', name: 'Rhode Island' },
    { code: 'SC', name: 'South Carolina' },
    { code: 'SD', name: 'South Dakota' },
    { code: 'TN', name: 'Tennessee' },
    { code: 'TX', name: 'Texas' },
    { code: 'UT', name: 'Utah' },
    { code: 'VT', name: 'Vermont' },
    { code: 'VA', name: 'Virginia' },
    { code: 'WA', name: 'Washington' },
    { code: 'WV', name: 'West Virginia' },
    { code: 'WI', name: 'Wisconsin' },
    { code: 'WY', name: 'Wyoming' },
    { code: 'DC', name: 'Washington D.C.' },
];
