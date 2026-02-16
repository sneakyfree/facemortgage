'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
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
    type MatchingResult,
    type LOMatch,
} from '@/hooks/useMatching';

const TOTAL_STEPS = 6;
const STORAGE_KEY = 'facemortgage_intake_progress';

// Icons for loan purposes
const PURPOSE_ICONS: Record<LoanPurpose, string> = {
    purchase: '🏡',
    refinance: '🔄',
    cash_out: '💰',
    heloc: '🏦',
};

// Icons for property types
const PROPERTY_ICONS: Record<PropertyType, string> = {
    single_family: '🏠',
    condo: '🏢',
    townhouse: '🏘️',
    multi_unit: '🏗️',
    manufactured: '🏕️',
};

// Timeline icons
const TIMELINE_ICONS: Record<Timeline, string> = {
    immediate: '⚡',
    '30_days': '📅',
    exploring: '🔍',
};

/**
 * TurboTax-Style Borrower Intake Wizard
 * 
 * Premium 6-step guided wizard with:
 * - Animated slide transitions
 * - LocalStorage persistence
 * - Keyboard navigation (Enter/Escape)
 * - Progress bar with step labels
 * - Loan amount slider (Step 5)
 * - Review step (Step 6)
 */
export default function BorrowerIntakeForm() {
    const [step, setStep] = useState(1);
    const [direction, setDirection] = useState<'forward' | 'back'>('forward');
    const { profile, updateProfile, toggleSpecialNeed, uncertainties, markUncertain, isValid } = useBorrowerIntake();
    const { findMatches, loading, error, results } = useMatching();
    const containerRef = useRef<HTMLDivElement>(null);

    // Persist progress to localStorage
    useEffect(() => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const { step: savedStep, profile: savedProfile } = JSON.parse(saved);
                if (savedStep && savedProfile) {
                    setStep(savedStep);
                    updateProfile(savedProfile);
                }
            }
        } catch { /* ignore parse errors */ }
    }, []);

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({ step, profile }));
        } catch { /* ignore storage errors */ }
    }, [step, profile]);

    const handleSubmit = async () => {
        if (isValid()) {
            await findMatches(profile);
            localStorage.removeItem(STORAGE_KEY);
        }
    };

    const nextStep = useCallback(() => {
        setDirection('forward');
        setStep(prev => Math.min(prev + 1, TOTAL_STEPS));
    }, []);

    const prevStep = useCallback(() => {
        setDirection('back');
        setStep(prev => Math.max(prev - 1, 1));
    }, []);

    // Keyboard navigation
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.key === 'Enter' && step < TOTAL_STEPS) {
                e.preventDefault();
                nextStep();
            } else if (e.key === 'Escape' && step > 1) {
                e.preventDefault();
                prevStep();
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [step, nextStep, prevStep]);

    // Show results
    if (results) {
        return <MatchResults results={results} onReset={() => {
            localStorage.removeItem(STORAGE_KEY);
            window.location.reload();
        }} />;
    }

    const stepLabels = ['Location', 'Purpose', 'Property', 'Needs', 'Amount', 'Review'];

    const canProceed = (): boolean => {
        switch (step) {
            case 1: return !!profile.state;
            case 2: return !!profile.loan_purpose;
            case 3: return !!profile.property_type && !!profile.timeline;
            case 4: return true; // Optional step
            case 5: return true; // Optional step (amount)
            case 6: return isValid();
            default: return false;
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6" ref={containerRef} data-testid="intake-wizard">
            {/* Premium progress bar */}
            <div className="mb-8" role="progressbar" aria-valuenow={step} aria-valuemin={1} aria-valuemax={TOTAL_STEPS}>
                <div className="flex justify-between mb-3">
                    {stepLabels.map((label, i) => (
                        <div key={label} className="flex flex-col items-center gap-1">
                            <div
                                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${i + 1 < step
                                        ? 'bg-green-500 text-white shadow-md shadow-green-200'
                                        : i + 1 === step
                                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-200 scale-110'
                                            : 'bg-gray-200 text-gray-400'
                                    }`}
                            >
                                {i + 1 < step ? '✓' : i + 1}
                            </div>
                            <span className={`text-xs font-medium ${i + 1 === step ? 'text-blue-600' : 'text-gray-400'
                                }`}>
                                {label}
                            </span>
                        </div>
                    ))}
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
                        style={{ width: `${((step - 1) / (TOTAL_STEPS - 1)) * 100}%` }}
                    />
                </div>
            </div>

            {/* Step content with slide animation */}
            <div className="overflow-hidden">
                <div
                    className={`bg-white rounded-2xl shadow-xl p-8 border border-gray-100 transition-all duration-300 ${direction === 'forward' ? 'animate-slide-in-right' : 'animate-slide-in-left'
                        }`}
                    key={step}
                >
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
                            onChange={(loan_purpose) => {
                                updateProfile({ loan_purpose });
                                setTimeout(nextStep, 300);
                            }}
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
                    {step === 5 && (
                        <Step5LoanAmount
                            value={profile.loan_amount_estimate}
                            onChange={(loan_amount_estimate) => updateProfile({ loan_amount_estimate })}
                        />
                    )}
                    {step === 6 && (
                        <Step6Review profile={profile} />
                    )}

                    {/* Error display */}
                    {error && (
                        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center gap-2">
                            <span>⚠️</span> {error}
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="mt-8 flex justify-between items-center">
                        <button
                            onClick={prevStep}
                            disabled={step === 1}
                            className="px-6 py-2.5 text-gray-600 hover:text-gray-900 disabled:opacity-30 transition-all flex items-center gap-1"
                            data-testid="intake-back"
                        >
                            ← Back
                        </button>

                        {step < TOTAL_STEPS ? (
                            <button
                                onClick={nextStep}
                                disabled={!canProceed()}
                                className="px-8 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed font-medium transition-all shadow-md hover:shadow-lg flex items-center gap-2"
                                data-testid="intake-next"
                            >
                                Continue <span>→</span>
                            </button>
                        ) : (
                            <button
                                onClick={handleSubmit}
                                disabled={loading || !isValid()}
                                className="px-8 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:from-green-600 hover:to-green-700 disabled:opacity-50 font-semibold flex items-center gap-2 shadow-lg hover:shadow-xl transition-all"
                                data-testid="intake-submit"
                            >
                                {loading && (
                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                    </svg>
                                )}
                                {loading ? 'Finding your perfect match...' : '🔍 Find My Loan Officer'}
                            </button>
                        )}
                    </div>

                    {/* Keyboard hint */}
                    <div className="mt-4 text-center text-xs text-gray-400">
                        Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Enter</kbd> to continue
                        {step > 1 && <> or <kbd className="px-1.5 py-0.5 bg-gray-100 rounded text-gray-500 font-mono">Esc</kbd> to go back</>}
                    </div>
                </div>
            </div>

            {/* CSS animations */}
            <style jsx>{`
                @keyframes slideInRight {
                    from { opacity: 0; transform: translateX(40px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                @keyframes slideInLeft {
                    from { opacity: 0; transform: translateX(-40px); }
                    to { opacity: 1; transform: translateX(0); }
                }
                .animate-slide-in-right { animation: slideInRight 0.3s ease-out; }
                .animate-slide-in-left { animation: slideInLeft 0.3s ease-out; }
            `}</style>
        </div>
    );
}

// ==================== Step Components ====================

function Step1Location({
    value, onChange, onUncertain
}: {
    value: string;
    onChange: (v: string) => void;
    onUncertain: () => void;
}) {
    return (
        <div data-testid="step-location">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">📍</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Where are you buying?</h2>
                <p className="text-gray-500">We&apos;ll match you with loan officers licensed in your state.</p>
            </div>

            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all"
                data-testid="state-select"
                aria-label="Select your state"
            >
                <option value="">Select your state...</option>
                {US_STATES.map(state => (
                    <option key={state.code} value={state.code}>{state.name}</option>
                ))}
            </select>

            <button
                onClick={onUncertain}
                className="mt-4 text-sm text-gray-400 hover:text-gray-600 underline block mx-auto transition-colors"
            >
                I&apos;m not sure yet
            </button>
        </div>
    );
}

function Step2Purpose({
    value, onChange
}: {
    value: LoanPurpose;
    onChange: (v: LoanPurpose) => void;
}) {
    return (
        <div data-testid="step-purpose">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">🎯</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">What are you looking to do?</h2>
                <p className="text-gray-500">Different loan types require different expertise.</p>
            </div>

            <div className="space-y-3">
                {(Object.entries(LOAN_PURPOSE_LABELS) as [LoanPurpose, string][]).map(([key, label]) => (
                    <button
                        key={key}
                        onClick={() => onChange(key)}
                        className={`w-full p-5 text-left rounded-xl border-2 transition-all duration-200 flex items-center gap-4 ${value === key
                                ? 'border-blue-600 bg-blue-50 shadow-md shadow-blue-100'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                            }`}
                        data-testid={`purpose-${key}`}
                    >
                        <span className="text-2xl">{PURPOSE_ICONS[key]}</span>
                        <span className="font-medium text-lg">{label}</span>
                        {value === key && <span className="ml-auto text-blue-600">✓</span>}
                    </button>
                ))}
            </div>
        </div>
    );
}

function Step3Details({
    propertyType, timeline, onPropertyChange, onTimelineChange,
}: {
    propertyType: PropertyType;
    timeline: Timeline;
    onPropertyChange: (v: PropertyType) => void;
    onTimelineChange: (v: Timeline) => void;
}) {
    return (
        <div data-testid="step-details">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">🏠</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Tell us more</h2>
            </div>

            <div className="mb-8">
                <label className="block text-sm font-semibold text-gray-700 mb-3">Property Type</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {(Object.entries(PROPERTY_TYPE_LABELS) as [PropertyType, string][]).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => onPropertyChange(key)}
                            className={`p-4 text-center rounded-xl border-2 transition-all ${propertyType === key
                                    ? 'border-blue-600 bg-blue-50 shadow-md'
                                    : 'border-gray-200 hover:border-blue-300'
                                }`}
                            data-testid={`property-${key}`}
                        >
                            <span className="text-2xl block mb-1">{PROPERTY_ICONS[key]}</span>
                            <span className="text-sm font-medium">{label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">Timeline</label>
                <div className="space-y-2">
                    {(Object.entries(TIMELINE_LABELS) as [Timeline, string][]).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => onTimelineChange(key)}
                            className={`w-full p-4 text-left rounded-xl border-2 transition-all flex items-center gap-3 ${timeline === key
                                    ? 'border-blue-600 bg-blue-50 shadow-md'
                                    : 'border-gray-200 hover:border-blue-300'
                                }`}
                            data-testid={`timeline-${key}`}
                        >
                            <span className="text-xl">{TIMELINE_ICONS[key]}</span>
                            <span className="font-medium">{label}</span>
                            {timeline === key && <span className="ml-auto text-blue-600">✓</span>}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

function Step4SpecialNeeds({
    selected, onToggle
}: {
    selected: SpecialNeed[];
    onToggle: (v: SpecialNeed) => void;
}) {
    return (
        <div data-testid="step-needs">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">✨</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Any special circumstances?</h2>
                <p className="text-gray-500">Select all that apply — or skip if none.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(Object.entries(SPECIAL_NEED_LABELS) as [SpecialNeed, { label: string; description: string }][]).map(([key, { label, description }]) => (
                    <button
                        key={key}
                        onClick={() => onToggle(key)}
                        className={`p-4 text-left rounded-xl border-2 transition-all ${selected.includes(key)
                                ? 'border-blue-600 bg-blue-50 shadow-md'
                                : 'border-gray-200 hover:border-blue-300'
                            }`}
                        data-testid={`need-${key}`}
                    >
                        <div className="flex items-start gap-3">
                            <div className={`w-5 h-5 rounded border-2 flex items-center justify-center mt-0.5 transition-all ${selected.includes(key)
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

            <p className="mt-6 text-sm text-gray-400 text-center">
                Your matched loan officer can discuss any unique needs during your call.
            </p>
        </div>
    );
}

// NEW: Step 5 — Loan Amount
function Step5LoanAmount({
    value, onChange
}: {
    value?: number;
    onChange: (v: number | undefined) => void;
}) {
    const [displayValue, setDisplayValue] = useState(value || 300000);

    const formatCurrency = (num: number) => {
        if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
        return `$${(num / 1000).toFixed(0)}K`;
    };

    return (
        <div data-testid="step-amount">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">💵</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Estimated loan amount</h2>
                <p className="text-gray-500">This helps us find LOs with the right experience. (Optional)</p>
            </div>

            <div className="text-center mb-6">
                <span className="text-5xl font-bold text-blue-600">
                    {formatCurrency(displayValue)}
                </span>
            </div>

            <div className="px-4">
                <input
                    type="range"
                    min={50000}
                    max={5000000}
                    step={25000}
                    value={displayValue}
                    onChange={(e) => {
                        const val = parseInt(e.target.value);
                        setDisplayValue(val);
                        onChange(val);
                    }}
                    className="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    data-testid="amount-slider"
                    aria-label="Loan amount slider"
                />
                <div className="flex justify-between text-sm text-gray-400 mt-2">
                    <span>$50K</span>
                    <span>$5M+</span>
                </div>
            </div>

            <div className="mt-6">
                <label className="block text-sm font-medium text-gray-600 mb-2">Or enter exact amount:</label>
                <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg">$</span>
                    <input
                        type="number"
                        value={displayValue}
                        onChange={(e) => {
                            const val = parseInt(e.target.value) || 0;
                            const clamped = Math.min(Math.max(val, 10000), 10000000);
                            setDisplayValue(clamped);
                            onChange(clamped);
                        }}
                        className="w-full pl-10 pr-4 py-3 border-2 border-gray-200 rounded-xl text-lg focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all"
                        placeholder="300,000"
                        data-testid="amount-input"
                    />
                </div>
            </div>

            <button
                onClick={() => onChange(undefined)}
                className="mt-4 text-sm text-gray-400 hover:text-gray-600 underline block mx-auto transition-colors"
            >
                Skip — I&apos;m not sure yet
            </button>
        </div>
    );
}

// NEW: Step 6 — Review
function Step6Review({ profile }: { profile: any }) {
    const getStateLabel = (code: string) => {
        const state = US_STATES.find(s => s.code === code);
        return state ? state.name : code;
    };

    const formatAmount = (num?: number) => {
        if (!num) return 'Not specified';
        if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
        return `$${(num / 1000).toFixed(0)}K`;
    };

    const reviewItems = [
        { label: 'Location', value: getStateLabel(profile.state), icon: '📍' },
        { label: 'Loan Purpose', value: LOAN_PURPOSE_LABELS[profile.loan_purpose as LoanPurpose] || profile.loan_purpose, icon: '🎯' },
        { label: 'Property Type', value: PROPERTY_TYPE_LABELS[profile.property_type as PropertyType] || profile.property_type, icon: '🏠' },
        { label: 'Timeline', value: TIMELINE_LABELS[profile.timeline as Timeline] || profile.timeline, icon: '📅' },
        {
            label: 'Special Needs', value: profile.special_needs.length > 0
                ? profile.special_needs.map((n: SpecialNeed) => SPECIAL_NEED_LABELS[n]?.label || n).join(', ')
                : 'None specified', icon: '✨'
        },
        { label: 'Loan Amount', value: formatAmount(profile.loan_amount_estimate), icon: '💵' },
    ];

    return (
        <div data-testid="step-review">
            <div className="text-center mb-6">
                <span className="text-4xl mb-3 block">📋</span>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Review your information</h2>
                <p className="text-gray-500">Make sure everything looks right before we find your match.</p>
            </div>

            <div className="space-y-4">
                {reviewItems.map(item => (
                    <div key={item.label} className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
                        <span className="text-xl">{item.icon}</span>
                        <div className="flex-grow">
                            <div className="text-xs font-medium text-gray-400 uppercase tracking-wider">{item.label}</div>
                            <div className="text-gray-900 font-medium">{item.value}</div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl text-center">
                <p className="text-green-800 font-medium">✨ Ready to find your perfect match!</p>
                <p className="text-green-600 text-sm mt-1">Our AI will analyze your needs and rank the best loan officers for you.</p>
            </div>
        </div>
    );
}


// ==================== Match Results Display ====================

function MatchResults({
    results, onReset
}: {
    results: MatchingResult;
    onReset: () => void;
}) {
    return (
        <div className="max-w-4xl mx-auto p-6" data-testid="match-results">
            <div className="mb-8 text-center">
                <div className="text-5xl mb-3">🎉</div>
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
                <div className="text-center py-16 bg-gray-50 rounded-2xl">
                    <span className="text-4xl block mb-4">🔍</span>
                    <p className="text-gray-600 mb-4 text-lg">No loan officers found matching your criteria right now.</p>
                    <button
                        onClick={onReset}
                        className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium"
                        data-testid="adjust-search"
                    >
                        Adjust your search
                    </button>
                </div>
            )}

            <div className="mt-8 text-center">
                <button
                    onClick={onReset}
                    className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                    ← Start over
                </button>
                <p className="mt-2 text-xs text-gray-400">
                    Algorithm version: {results.algorithm_version}
                </p>
            </div>
        </div>
    );
}

function MatchCard({ match, rank }: { match: LOMatch; rank: number }) {
    const [showReasons, setShowReasons] = useState(rank <= 3);

    return (
        <div
            className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow"
            data-testid={`match-card-${rank}`}
        >
            <div className="flex items-start gap-4">
                {/* Rank badge */}
                <div className={`flex-shrink-0 w-11 h-11 rounded-full flex items-center justify-center font-bold text-white shadow-md ${rank === 1 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' :
                        rank === 2 ? 'bg-gradient-to-br from-gray-400 to-gray-500' :
                            rank === 3 ? 'bg-gradient-to-br from-orange-600 to-orange-700' :
                                'bg-gradient-to-br from-blue-500 to-blue-600'
                    }`}>
                    {rank}
                </div>

                <div className="flex-grow min-w-0">
                    <div className="flex items-start justify-between gap-3">
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
                                <p className="text-gray-500">{match.company_name}</p>
                            )}
                        </div>

                        <div className="text-right flex-shrink-0">
                            <div className="text-3xl font-bold text-blue-600">{match.match_score}%</div>
                            <div className="text-xs font-medium text-gray-400 uppercase">match</div>
                        </div>
                    </div>

                    {/* Stats row */}
                    <div className="mt-4 flex flex-wrap gap-4 text-sm">
                        <div className="flex items-center gap-1">
                            <span className="text-yellow-500">★</span>
                            <span className="font-semibold">{match.avg_rating.toFixed(1)}</span>
                            <span className="text-gray-400">({match.total_reviews})</span>
                        </div>
                        {match.years_experience && (
                            <div className="text-gray-500">{match.years_experience}y exp</div>
                        )}
                        {match.avg_pickup_seconds && (
                            <div className="text-gray-500">⚡ ~{Math.round(match.avg_pickup_seconds)}s response</div>
                        )}
                        <div className={`font-medium ${match.availability === 'online_now' ? 'text-green-600' :
                                match.availability === 'busy' ? 'text-orange-500' : 'text-gray-400'
                            }`}>
                            {match.availability === 'online_now' ? '🟢 Online' :
                                match.availability === 'busy' ? '🟡 Busy' : '⚫ Offline'}
                        </div>
                    </div>

                    {/* Specialties */}
                    {match.specialty_names.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                            {match.specialty_names.map(s => (
                                <span key={s} className="px-2 py-1 bg-blue-50 text-blue-700 rounded-lg text-xs font-medium">{s}</span>
                            ))}
                        </div>
                    )}

                    {/* Why this LO? */}
                    <div className="mt-4">
                        <button
                            onClick={() => setShowReasons(!showReasons)}
                            className="text-sm text-blue-600 hover:text-blue-800 font-medium transition-colors"
                            data-testid={`why-button-${rank}`}
                        >
                            {showReasons ? '▼ Why this loan officer?' : '▶ Why this loan officer?'}
                        </button>

                        {showReasons && (
                            <ul className="mt-2 space-y-1.5 pl-1">
                                {match.match_reasons.map((reason, i) => (
                                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                                        <span className="text-green-500 mt-0.5">✓</span>
                                        <span>
                                            {reason.reason}
                                            {reason.verified && (
                                                <span className="ml-1 text-xs text-blue-500 font-medium">(verified)</span>
                                            )}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="mt-5 flex gap-3">
                        <button
                            className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 font-medium transition-colors shadow-md"
                            data-testid={`connect-${rank}`}
                        >
                            {match.has_video ? '📹 Watch Intro' : '📞 Connect Now'}
                        </button>
                        <button
                            className="px-4 py-2.5 border-2 border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all font-medium"
                            data-testid={`schedule-${rank}`}
                        >
                            📅 Schedule
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
