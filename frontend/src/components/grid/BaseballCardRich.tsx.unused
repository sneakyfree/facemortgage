'use client';

import React from 'react';

/**
 * Baseball Card Component (Row #10 Gap Fix)
 * 
 * Displays LO stats with letter grades (A+ to D)
 * Uses data from /api/v1/grid-enhanced/card/{id}
 */

interface BaseballCardProps {
    professionalId: string;
    name: string;
    company?: string;
    avatarUrl?: string;
    overallGrade: string;
    responsivenessGrade: string;
    experienceGrade: string;
    ratingGrade: string;
    avgRating: number;
    totalReviews: number;
    yearsExperience?: number;
    nmlsVerified: boolean;
    nmlsId?: string;
    specialties: string[];
    avgPickupSeconds?: number;
    onClose?: () => void;
}

const gradeColors: Record<string, string> = {
    'A+': 'bg-emerald-500 text-white',
    'A': 'bg-emerald-400 text-white',
    'A-': 'bg-green-400 text-white',
    'B+': 'bg-lime-400 text-gray-900',
    'B': 'bg-yellow-400 text-gray-900',
    'B-': 'bg-yellow-500 text-gray-900',
    'C+': 'bg-orange-400 text-white',
    'C': 'bg-orange-500 text-white',
    'C-': 'bg-red-400 text-white',
    'D': 'bg-red-600 text-white',
};

function GradeBadge({ grade, size = 'md' }: { grade: string; size?: 'sm' | 'md' | 'lg' }) {
    const sizeClasses = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-3 py-1 text-sm',
        lg: 'px-4 py-2 text-xl font-bold',
    };

    return (
        <span className={`rounded-full font-semibold ${gradeColors[grade] || 'bg-gray-400 text-white'} ${sizeClasses[size]}`}>
            {grade}
        </span>
    );
}

export function BaseballCard({
    professionalId,
    name,
    company,
    avatarUrl,
    overallGrade,
    responsivenessGrade,
    experienceGrade,
    ratingGrade,
    avgRating,
    totalReviews,
    yearsExperience,
    nmlsVerified,
    nmlsId,
    specialties,
    avgPickupSeconds,
    onClose,
}: BaseballCardProps) {
    return (
        <div className="bg-white rounded-2xl shadow-xl max-w-md mx-auto overflow-hidden">
            {/* Header with gradient */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-6 relative">
                {onClose && (
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 text-white/80 hover:text-white"
                        aria-label="Close"
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}

                <div className="flex items-center gap-4">
                    {/* Avatar */}
                    <div className="w-20 h-20 rounded-full bg-white/20 overflow-hidden flex-shrink-0">
                        {avatarUrl ? (
                            <img src={avatarUrl} alt={name} className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-white text-2xl font-bold">
                                {name.split(' ').map(n => n[0]).join('')}
                            </div>
                        )}
                    </div>

                    {/* Name and Company */}
                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-white">{name}</h3>
                        {company && <p className="text-white/80 text-sm">{company}</p>}
                        {nmlsVerified && nmlsId && (
                            <div className="flex items-center gap-1 mt-1">
                                <svg className="w-4 h-4 text-green-300" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                                <span className="text-green-200 text-xs">NMLS #{nmlsId}</span>
                            </div>
                        )}
                    </div>

                    {/* Overall Grade */}
                    <div className="text-center">
                        <GradeBadge grade={overallGrade} size="lg" />
                        <p className="text-white/60 text-xs mt-1">Overall</p>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="p-6">
                <div className="grid grid-cols-3 gap-4 mb-6">
                    {/* Rating */}
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <GradeBadge grade={ratingGrade} size="sm" />
                        <div className="mt-2">
                            <div className="text-2xl font-bold text-gray-900">{avgRating.toFixed(1)}</div>
                            <div className="text-xs text-gray-500">{totalReviews} reviews</div>
                        </div>
                    </div>

                    {/* Response Time */}
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <GradeBadge grade={responsivenessGrade} size="sm" />
                        <div className="mt-2">
                            <div className="text-2xl font-bold text-gray-900">
                                {avgPickupSeconds ? `${Math.round(avgPickupSeconds)}s` : 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">Avg Response</div>
                        </div>
                    </div>

                    {/* Experience */}
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <GradeBadge grade={experienceGrade} size="sm" />
                        <div className="mt-2">
                            <div className="text-2xl font-bold text-gray-900">
                                {yearsExperience || 'N/A'}
                            </div>
                            <div className="text-xs text-gray-500">Years Exp</div>
                        </div>
                    </div>
                </div>

                {/* Specialties */}
                {specialties.length > 0 && (
                    <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-500 mb-2">Specialties</h4>
                        <div className="flex flex-wrap gap-2">
                            {specialties.map((specialty, i) => (
                                <span key={i} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                    {specialty}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Action Button */}
                <button className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all">
                    Connect Now
                </button>
            </div>
        </div>
    );
}

/**
 * Hook to fetch baseball card data
 */
export function useBaseballCard(professionalId: string | null) {
    const [data, setData] = React.useState<BaseballCardProps | null>(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (!professionalId) {
            setData(null);
            return;
        }

        setLoading(true);
        fetch(`/api/v1/grid-enhanced/card/${professionalId}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load card');
                return res.json();
            })
            .then(json => {
                setData({
                    professionalId: json.professional_id,
                    name: json.name,
                    company: json.company_name,
                    avatarUrl: json.avatar_url,
                    overallGrade: json.overall_grade,
                    responsivenessGrade: json.responsiveness_grade,
                    experienceGrade: json.experience_grade,
                    ratingGrade: json.rating_grade,
                    avgRating: json.avg_rating || 0,
                    totalReviews: json.total_reviews || 0,
                    yearsExperience: json.years_experience,
                    nmlsVerified: json.nmls_verified || false,
                    nmlsId: json.nmls_id,
                    specialties: json.specialties || [],
                    avgPickupSeconds: json.avg_pickup_seconds,
                });
                setError(null);
            })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [professionalId]);

    return { data, loading, error };
}

