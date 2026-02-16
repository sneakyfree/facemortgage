'use client';

import BorrowerIntakeForm from '@/components/matching/BorrowerIntakeForm';

export default function GetMatchedPage() {
    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
            {/* Header */}
            <header className="py-10 text-center relative overflow-hidden">
                {/* Decorative background */}
                <div className="absolute inset-0 opacity-5">
                    <div className="absolute top-10 left-1/4 w-64 h-64 bg-blue-400 rounded-full blur-3xl" />
                    <div className="absolute top-20 right-1/4 w-48 h-48 bg-indigo-400 rounded-full blur-3xl" />
                </div>

                <div className="relative z-10">
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-4">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        AI-Powered Matching
                    </div>
                    <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-3">
                        Find Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Perfect</span> Loan Officer
                    </h1>
                    <p className="text-lg text-gray-500 max-w-2xl mx-auto">
                        Answer a few quick questions and our AI matches you with licensed mortgage
                        professionals who specialize in <em>your exact situation</em>.
                    </p>
                </div>
            </header>

            {/* Intake Form */}
            <main className="pb-16 relative z-10">
                <BorrowerIntakeForm />
            </main>

            {/* Trust indicators */}
            <footer className="py-10 bg-white/60 backdrop-blur-sm border-t border-gray-100">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex flex-wrap justify-center gap-10 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center text-green-600 text-xs">✓</span>
                            <span>All loan officers are <strong>NMLS verified</strong></span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs">🔒</span>
                            <span>Your data is <strong>encrypted</strong></span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs">💯</span>
                            <span><strong>No obligation</strong> to proceed</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center text-orange-600 text-xs">⚡</span>
                            <span>Results in <strong>&lt; 30 seconds</strong></span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
