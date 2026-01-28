'use client';

import BorrowerIntakeForm from '@/components/matching/BorrowerIntakeForm';

export default function GetMatchedPage() {
    return (
        <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
            {/* Header */}
            <header className="py-8 text-center">
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    Find Your Perfect Loan Officer
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                    Answer a few questions and we'll match you with licensed professionals
                    who specialize in your situation.
                </p>
            </header>

            {/* Intake Form */}
            <main className="pb-16">
                <BorrowerIntakeForm />
            </main>

            {/* Trust indicators */}
            <footer className="py-8 bg-gray-50 border-t">
                <div className="max-w-4xl mx-auto px-6 text-center">
                    <div className="flex flex-wrap justify-center gap-8 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                            <span className="text-green-500 text-lg">✓</span>
                            <span>All loan officers are NMLS verified</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-500 text-lg">✓</span>
                            <span>No obligation to proceed</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-500 text-lg">✓</span>
                            <span>Your data is secure</span>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
