'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api/client';

interface CallRating {
    overall: number;  // 1-5 stars
    knowledge: number;
    responsiveness: number;
    professionalism: number;
    wouldRecommend: boolean;
    feedback?: string;
}

interface PostCallSurveyProps {
    callId: string;
    loName: string;
    onSubmit?: (rating: CallRating) => void;
    onClose?: () => void;
}

export function PostCallSurvey({ callId, loName, onSubmit, onClose }: PostCallSurveyProps) {
    const [rating, setRating] = useState<Partial<CallRating>>({
        overall: 0,
        knowledge: 0,
        responsiveness: 0,
        professionalism: 0,
        wouldRecommend: true,
    });
    const [feedback, setFeedback] = useState('');
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleStarClick = (field: keyof CallRating, value: number) => {
        setRating(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async () => {
        if (!rating.overall) return;

        setLoading(true);
        try {
            const fullRating: CallRating = {
                overall: rating.overall || 0,
                knowledge: rating.knowledge || 0,
                responsiveness: rating.responsiveness || 0,
                professionalism: rating.professionalism || 0,
                wouldRecommend: rating.wouldRecommend ?? true,
                feedback: feedback || undefined,
            };

            await apiClient.post(`/api/v1/calls/${callId}/rating`, fullRating);
            setSubmitted(true);
            onSubmit?.(fullRating);

            // Auto-close after 2 seconds
            setTimeout(() => onClose?.(), 2000);
        } catch (err) {
            console.error('Failed to submit rating:', err);
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg p-8 max-w-md text-center">
                    <div className="text-5xl mb-4">🎉</div>
                    <h2 className="text-xl font-bold text-gray-800 mb-2">Thank You!</h2>
                    <p className="text-gray-600">
                        Your feedback helps other borrowers find great loan officers.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 rounded-t-xl">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className="text-xl font-bold text-white">How was your call?</h2>
                            <p className="text-blue-100 text-sm">with {loName}</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-white/80 hover:text-white"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                <div className="p-6 space-y-6">
                    {/* Overall Rating */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Overall Experience
                        </label>
                        <StarRating
                            value={rating.overall || 0}
                            onChange={(v) => handleStarClick('overall', v)}
                            size="large"
                        />
                    </div>

                    {/* Category Ratings */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Knowledge</span>
                            <StarRating
                                value={rating.knowledge || 0}
                                onChange={(v) => handleStarClick('knowledge', v)}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Responsiveness</span>
                            <StarRating
                                value={rating.responsiveness || 0}
                                onChange={(v) => handleStarClick('responsiveness', v)}
                            />
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-600">Professionalism</span>
                            <StarRating
                                value={rating.professionalism || 0}
                                onChange={(v) => handleStarClick('professionalism', v)}
                            />
                        </div>
                    </div>

                    {/* Would Recommend */}
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-700">Would you recommend {loName}?</span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setRating(prev => ({ ...prev, wouldRecommend: true }))}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${rating.wouldRecommend
                                        ? 'bg-green-500 text-white'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                            >
                                👍 Yes
                            </button>
                            <button
                                onClick={() => setRating(prev => ({ ...prev, wouldRecommend: false }))}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${rating.wouldRecommend === false
                                        ? 'bg-red-500 text-white'
                                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                            >
                                👎 No
                            </button>
                        </div>
                    </div>

                    {/* Written Feedback */}
                    <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Any additional feedback? (optional)
                        </label>
                        <textarea
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                            placeholder="Share your experience..."
                            className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                            maxLength={500}
                        />
                        <p className="text-xs text-gray-400 text-right">
                            {feedback.length}/500
                        </p>
                    </div>

                    {/* Submit Button */}
                    <button
                        onClick={handleSubmit}
                        disabled={!rating.overall || loading}
                        className="w-full py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transition-shadow"
                    >
                        {loading ? 'Submitting...' : 'Submit Feedback'}
                    </button>

                    <p className="text-xs text-center text-gray-400">
                        Your feedback is anonymous and helps improve the platform.
                    </p>
                </div>
            </div>
        </div>
    );
}

function StarRating({
    value,
    onChange,
    size = 'default'
}: {
    value: number;
    onChange: (value: number) => void;
    size?: 'default' | 'large';
}) {
    const [hovered, setHovered] = useState(0);
    const starSize = size === 'large' ? 'text-3xl' : 'text-xl';

    return (
        <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
                <button
                    key={star}
                    onMouseEnter={() => setHovered(star)}
                    onMouseLeave={() => setHovered(0)}
                    onClick={() => onChange(star)}
                    className={`${starSize} transition-transform hover:scale-110`}
                >
                    {(hovered || value) >= star ? '⭐' : '☆'}
                </button>
            ))}
        </div>
    );
}

export default PostCallSurvey;
