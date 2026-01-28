'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api/client';

/**
 * Enhanced Grid Hooks - Phase 2 Core Experience
 * 
 * Provides advanced filtering, baseball card stats,
 * and real-time presence features.
 */

// Filter types
export interface GridFilters {
    state?: string;
    specialties?: string[];
    languages?: string[];
    min_rating?: number;
    max_pickup_seconds?: number;
    nmls_verified_only?: boolean;
    online_only?: boolean;
    available_only?: boolean;
    has_video?: boolean;
}

// Pickup badge
export interface PickupBadge {
    text: string;
    color: 'green' | 'yellow' | 'orange' | 'gray';
    icon: string;
}

// Professional in grid
export interface GridProfessional {
    id: string;
    user_id: string;
    name: string;
    company_name: string | null;
    avatar_url: string | null;
    status: 'offline' | 'online_available' | 'online_busy' | 'in_call' | 'away';
    nmls_id: string | null;
    nmls_verified: boolean;
    avg_rating: number;
    total_reviews: number;
    years_experience: number | null;
    has_video: boolean;
    pickup_badge: PickupBadge;
    avg_pickup_seconds: number | null;
    specialties: string[];
    languages: string[];
}

// Baseball card stats
export interface BaseballCardStats {
    professional_id: string;
    name: string;
    company_name: string | null;
    avatar_url: string | null;
    nmls_id: string | null;
    nmls_verified: boolean;
    nmls_verified_at: string | null;
    avg_rating: number;
    total_reviews: number;
    total_calls_completed: number;
    years_experience: number | null;
    avg_pickup_seconds: number | null;
    pickup_category: string;
    current_status: string;
    time_online_today_seconds: number;
    is_featured: boolean;
    specialties: string[];
    languages: string[];
    service_areas: string[];
    subscription_tier: string;
    overall_grade: string;
    responsiveness_grade: string;
    experience_grade: string;
    rating_grade: string;
}

// Filter options metadata
export interface FilterOptions {
    specialties: {
        label: string;
        options: { value: string; label: string }[];
    };
    languages: {
        label: string;
        options: { value: string; label: string }[];
    };
    pickup_speed: {
        label: string;
        options: { value: number; label: string }[];
    };
    min_rating: {
        label: string;
        options: { value: number; label: string }[];
    };
}

/**
 * Hook for enhanced grid with advanced filtering
 */
export function useEnhancedGrid() {
    const [professionals, setProfessionals] = useState<GridProfessional[]>([]);
    const [filters, setFilters] = useState<GridFilters>({});
    const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load filter options on mount
    useEffect(() => {
        const loadFilterOptions = async () => {
            try {
                const response = await apiClient.get<FilterOptions>('/grid-enhanced/filters');
                setFilterOptions(response.data);
            } catch (err) {
                console.error('Failed to load filter options:', err);
            }
        };
        loadFilterOptions();
    }, []);

    // Apply filters
    const applyFilters = useCallback(async (newFilters: GridFilters) => {
        setLoading(true);
        setError(null);
        setFilters(newFilters);

        try {
            const response = await apiClient.post<{ professionals: GridProfessional[] }>(
                '/grid-enhanced/filter',
                { ...newFilters, limit: 50, offset: 0 }
            );
            setProfessionals(response.data.professionals);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to filter';
            setError(message);
        } finally {
            setLoading(false);
        }
    }, []);

    // Update single filter
    const updateFilter = useCallback((key: keyof GridFilters, value: unknown) => {
        const newFilters = { ...filters, [key]: value };
        applyFilters(newFilters);
    }, [filters, applyFilters]);

    // Clear all filters
    const clearFilters = useCallback(() => {
        setFilters({});
        applyFilters({});
    }, [applyFilters]);

    // Get online now
    const fetchOnlineNow = useCallback(async () => {
        setLoading(true);
        try {
            const response = await apiClient.get<{ professionals: GridProfessional[] }>(
                '/grid-enhanced/online-now'
            );
            setProfessionals(response.data.professionals);
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Failed to fetch';
            setError(message);
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        professionals,
        filters,
        filterOptions,
        loading,
        error,
        applyFilters,
        updateFilter,
        clearFilters,
        fetchOnlineNow,
    };
}

/**
 * Hook for baseball card stats
 */
export function useBaseballCard(professionalId?: string) {
    const [stats, setStats] = useState<BaseballCardStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!professionalId) return;

        const fetchCard = async () => {
            setLoading(true);
            try {
                const response = await apiClient.get<BaseballCardStats>(
                    `/grid-enhanced/card/${professionalId}`
                );
                setStats(response.data);
            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : 'Failed to fetch';
                setError(message);
            } finally {
                setLoading(false);
            }
        };

        fetchCard();
    }, [professionalId]);

    return { stats, loading, error };
}

/**
 * Hook for comparing professionals
 */
export function useCompare() {
    const [cards, setCards] = useState<BaseballCardStats[]>([]);
    const [loading, setLoading] = useState(false);

    const compare = useCallback(async (ids: string[]) => {
        if (ids.length < 2 || ids.length > 5) return;

        setLoading(true);
        try {
            const response = await apiClient.post<{ professionals: BaseballCardStats[] }>(
                '/grid-enhanced/compare',
                ids
            );
            setCards(response.data.professionals);
        } catch (err) {
            console.error('Comparison failed:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const clear = useCallback(() => setCards([]), []);

    return { cards, loading, compare, clear };
}

// Grade color helpers
export function getGradeColor(grade: string): string {
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-blue-600';
    if (grade.startsWith('C')) return 'text-yellow-600';
    return 'text-gray-500';
}

export function getGradeBgColor(grade: string): string {
    if (grade.startsWith('A')) return 'bg-green-100';
    if (grade.startsWith('B')) return 'bg-blue-100';
    if (grade.startsWith('C')) return 'bg-yellow-100';
    return 'bg-gray-100';
}

// Pickup badge color helper
export function getPickupBadgeClass(badge: PickupBadge): string {
    switch (badge.color) {
        case 'green': return 'bg-green-100 text-green-800';
        case 'yellow': return 'bg-yellow-100 text-yellow-800';
        case 'orange': return 'bg-orange-100 text-orange-800';
        default: return 'bg-gray-100 text-gray-600';
    }
}
