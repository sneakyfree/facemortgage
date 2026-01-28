'use client';

import { useState } from 'react';
import {
    useBorrowerIntake,
    useMatching,
    LOAN_PURPOSE_LABELS,
    PROPERTY_TYPE_LABELS,
    TIMELINE_LABELS,
    SPECIAL_NEED_LABELS,
    US_STATES,
    type LoanPurpose,
    type PropertyType,
    type Timeline,
    type SpecialNeed,
} from '@/hooks/useMatching';

/**
 * TurboTax-Style Borrower Intake Form
 * 
 * Multi-step guided form that collects borrower preferences
 * and triggers the agentic matching engine.
 */
export default function BorrowerIntakeForm() {
    const [step, setStep] = useState(1);
    const { profile, updateProfile, toggleSpecialNeed, uncertainties, markUncertain, isValid } = useBorrowerIntake();
    const { findMatches, loading, error, results } = useMatching();

    const handleSubmit = async () => {
        if (isValid()) {
            await findMatches(profile);
        }
    };

    const nextStep = () => setStep(prev => Math.min(prev + 1, 4));
    const prevStep = () => setStep(prev => Math.max(prev - 1, 1));

    // Show results if we have them
    if (results) {
        return <MatchResults results={results} onReset={() => window.location.reload()} />;
    }

    return (
        <div className="max-w-2xl mx-auto p-6">
            {/* Progress indicator */}
            <div className="mb-8">
                <div className="flex justify-between mb-2">
                    {[1, 2, 3, 4].map(n => (
                        <div
                            key={n}
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${n <= step
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-200 text-gray-500'
                                }`}
                        >
                            {n}
                        </div>
                    ))}
                </div>
                <div className="h-2 bg-gray-200 rounded-full">
                    <div
                        className="h-full bg-blue-600 rounded-full transition-all"
                        style={{ width: `${(step / 4) * 100}%` }}
                    />
                </div>
            </div>

            {/* Step content */}
            <div className="bg-white rounded-xl shadow-lg p-8">
                {step === 1 && (
                    <Step1Location
                        value={profile.state}
                        onChange={(state) => updateProfile({ state })}
                        onUncertain={() => markUncertain('state')}
                    />
                )}
                {step === 2 && (
                    <Step2Purpose
                        value={profile.loan_purpose}
                        onChange={(loan_purpose) => updateProfile({ loan_purpose })}
                    />
                )}
                {step === 3 && (
                    <Step3Details
                        propertyType={profile.property_type}
                        timeline={profile.timeline}
                        onPropertyChange={(property_type) => updateProfile({ property_type })}
                        onTimelineChange={(timeline) => updateProfile({ timeline })}
                    />
                )}
                {step === 4 && (
                    <Step4SpecialNeeds
                        selected={profile.special_needs}
                        onToggle={toggleSpecialNeed}
                    />
                )}

                {/* Error display */}
                {error && (
                    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                        {error}
                    </div>
                )}

                {/* Navigation */}
                <div className="mt-8 flex justify-between">
                    <button
                        onClick={prevStep}
                        disabled={step === 1}
                        className="px-6 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50"
                    >
                        ← Back
                    </button>

                    {step < 4 ? (
                        <button
                            onClick={nextStep}
                            disabled={step === 1 && !profile.state}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                        >
                            Continue →
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            disabled={loading || !isValid()}
                            className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium flex items-center gap-2"
                        >
                            {loading && (
                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                            )}
                            {loading ? 'Finding matches...' : 'Find My Loan Officer'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

// Step 1: Location
function Step1Location({
    value,
    onChange,
    onUncertain
}: {
    value: string;
    onChange: (v: string) => void;
    onUncertain: () => void;
}) {
    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Where are you buying?
            </h2>
            <p className="text-gray-600 mb-6">
                We'll match you with loan officers licensed in your state.
            </p>

            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-lg text-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200"
            >
                <option value="">Select your state...</option>
                {US_STATES.map(state => (
                    <option key={state.code} value={state.code}>
                        {state.name}
                    </option>
                ))}
            </select>

            <button
                onClick={onUncertain}
                className="mt-4 text-sm text-gray-500 hover:text-gray-700 underline"
            >
                I'm not sure yet
            </button>
        </div>
    );
}

// Step 2: Loan Purpose
function Step2Purpose({
    value,
    onChange
}: {
    value: LoanPurpose;
    onChange: (v: LoanPurpose) => void;
}) {
    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                What are you looking to do?
            </h2>
            <p className="text-gray-600 mb-6">
                Different loan types require different expertise.
            </p>

            <div className="space-y-3">
                {(Object.entries(LOAN_PURPOSE_LABELS) as [LoanPurpose, string][]).map(([key, label]) => (
                    <button
                        key={key}
                        onClick={() => onChange(key)}
                        className={`w-full p-4 text-left rounded-lg border-2 transition-all ${value === key
                            ? 'border-blue-600 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                            }`}
                    >
                        <span className="font-medium">{label}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}

// Step 3: Property Details
function Step3Details({
    propertyType,
    timeline,
    onPropertyChange,
    onTimelineChange,
}: {
    propertyType: PropertyType;
    timeline: Timeline;
    onPropertyChange: (v: PropertyType) => void;
    onTimelineChange: (v: Timeline) => void;
}) {
    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Tell us more about your plans
            </h2>

            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Property Type
                </label>
                <select
                    value={propertyType}
                    onChange={(e) => onPropertyChange(e.target.value as PropertyType)}
                    className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-blue-500"
                >
                    {(Object.entries(PROPERTY_TYPE_LABELS) as [PropertyType, string][]).map(([key, label]) => (
                        <option key={key} value={key}>{label}</option>
                    ))}
                </select>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timeline
                </label>
                <div className="space-y-2">
                    {(Object.entries(TIMELINE_LABELS) as [Timeline, string][]).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => onTimelineChange(key)}
                            className={`w-full p-3 text-left rounded-lg border-2 transition-all ${timeline === key
                                ? 'border-blue-600 bg-blue-50'
                                : 'border-gray-200 hover:border-gray-300'
                                }`}
                        >
                            {label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// Step 4: Special Needs
function Step4SpecialNeeds({
    selected,
    onToggle
}: {
    selected: SpecialNeed[];
    onToggle: (v: SpecialNeed) => void;
}) {
    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Any special circumstances?
            </h2>
            <p className="text-gray-600 mb-6">
                Help us find specialists who understand your situation. Select all that apply.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(Object.entries(SPECIAL_NEED_LABELS) as [SpecialNeed, { label: string; description: string }][]).map(([key, { label, description }]) => (
                    <button
                        key={key}
                        onClick={() => onToggle(key)}
                        className={`p-4 text-left rounded-lg border-2 transition-all ${selected.includes(key)
                            ? 'border-blue-600 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                            }`}
                    >
                        <div className="flex items-start gap-3">
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 ${selected.includes(key)
                                ? 'border-blue-600 bg-blue-600'
                                : 'border-gray-300'
                                }`}>
                                {selected.includes(key) && (
                                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                )}
                            </div>
                            <div>
                                <div className="font-medium text-gray-900">{label}</div>
                                <div className="text-sm text-gray-500">{description}</div>
                            </div>
                        </div>
                    </button>
                ))}
            </div>

            <p className="mt-6 text-sm text-gray-500">
                Don't see your situation? No problem—your matched loan officer can discuss any unique needs during your call.
            </p>
        </div>
    );
}

// Match Results Display
import { type MatchingResult, type LOMatch } from '@/hooks/useMatching';

function MatchResults({
    results,
    onReset
}: {
    results: MatchingResult;
    onReset: () => void;
}) {
    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    We found {results.matches.length} matches for you
                </h1>
                <p className="text-gray-600">
                    from {results.total_eligible} eligible loan officers in your area
                </p>
            </div>

            <div className="space-y-4">
                {results.matches.map((match, index) => (
                    <MatchCard key={match.lo_id} match={match} rank={index + 1} />
                ))}
            </div>

            {results.matches.length === 0 && (
                <div className="text-center py-12 bg-gray-50 rounded-xl">
                    <p className="text-gray-600 mb-4">
                        No loan officers found matching your criteria right now.
                    </p>
                    <button
                        onClick={onReset}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Adjust your search
                    </button>
                </div>
            )}

            <div className="mt-8 text-center text-sm text-gray-500">
                Algorithm version: {results.algorithm_version}
            </div>
        </div>
    );
}

function MatchCard({ match, rank }: { match: LOMatch; rank: number }) {
    // Show reasons by default for better demo visibility
    const [showReasons, setShowReasons] = useState(true);

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-start gap-4">
                {/* Rank badge */}
                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                    {rank}
                </div>

                {/* Main content */}
                <div className="flex-grow">
                    <div className="flex items-start justify-between">
                        <div>
                            <h3 className="text-xl font-bold text-gray-900">
                                {match.lo_name}
                                {match.nmls_verified && (
                                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                        ✓ NMLS Verified
                                    </span>
                                )}
                            </h3>
                            {match.company_name && (
                                <p className="text-gray-600">{match.company_name}</p>
                            )}
                        </div>

                        {/* Match score */}
                        <div className="text-right">
                            <div className="text-3xl font-bold text-blue-600">
                                {match.match_score}%
                            </div>
                            <div className="text-sm text-gray-500">match</div>
                        </div>
                    </div>

                    {/* Stats row */}
                    <div className="mt-4 flex flex-wrap gap-4 text-sm">
                        <div className="flex items-center gap-1">
                            <span className="text-yellow-500">★</span>
                            <span className="font-medium">{match.avg_rating.toFixed(1)}</span>
                            <span className="text-gray-500">({match.total_reviews} reviews)</span>
                        </div>

                        {match.years_experience && (
                            <div className="text-gray-600">
                                {match.years_experience} years experience
                            </div>
                        )}

                        {match.avg_pickup_seconds && (
                            <div className="text-gray-600">
                                Responds in ~{Math.round(match.avg_pickup_seconds)}s
                            </div>
                        )}

                        <div className={`font-medium ${match.availability === 'online_now'
                            ? 'text-green-600'
                            : match.availability === 'busy'
                                ? 'text-orange-600'
                                : 'text-gray-500'
                            }`}>
                            {match.availability === 'online_now' ? '🟢 Online Now' :
                                match.availability === 'busy' ? '🟡 Busy' : '⚫ Offline'}
                        </div>
                    </div>

                    {/* Specialties */}
                    {match.specialty_names.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                            {match.specialty_names.map(specialty => (
                                <span
                                    key={specialty}
                                    className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm"
                                >
                                    {specialty}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Why this LO? */}
                    <div className="mt-4">
                        <button
                            onClick={() => setShowReasons(!showReasons)}
                            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                        >
                            {showReasons ? '▼ Hide' : '▶ Why this loan officer?'}
                        </button>

                        {showReasons && (
                            <ul className="mt-2 space-y-1">
                                {match.match_reasons.map((reason, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                                        <span className="text-green-500">✓</span>
                                        <span>
                                            {reason.reason}
                                            {reason.verified && (
                                                <span className="ml-1 text-gray-400">(verified)</span>
                                            )}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="mt-4 flex gap-3">
                        <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                            {match.has_video ? '📹 Watch Intro Video' : '📞 Connect Now'}
                        </button>
                        <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                            📅 Schedule Call
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
