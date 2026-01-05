'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { User, Mail, Phone, Home, DollarSign, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { softLeadsApi, GetMatchedRequest } from '@/lib/api/endpoints';

function EmbedGetMatchedPageContent() {
  const searchParams = useSearchParams();
  const partnerToken = searchParams.get('partner');
  const loanOfficerId = searchParams.get('lo');

  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<GetMatchedRequest>({
    name: '',
    email: '',
    phone: '',
    loan_purpose: '',
    estimated_amount: undefined,
    property_state: '',
    preferred_language: '',
    timeframe: '',
    utm_source: 'widget',
    utm_medium: 'embed',
    utm_campaign: partnerToken || '',
  });

  // US States for dropdown
  const states = [
    { code: 'AL', name: 'Alabama' }, { code: 'AK', name: 'Alaska' },
    { code: 'AZ', name: 'Arizona' }, { code: 'AR', name: 'Arkansas' },
    { code: 'CA', name: 'California' }, { code: 'CO', name: 'Colorado' },
    { code: 'CT', name: 'Connecticut' }, { code: 'DE', name: 'Delaware' },
    { code: 'FL', name: 'Florida' }, { code: 'GA', name: 'Georgia' },
    { code: 'HI', name: 'Hawaii' }, { code: 'ID', name: 'Idaho' },
    { code: 'IL', name: 'Illinois' }, { code: 'IN', name: 'Indiana' },
    { code: 'IA', name: 'Iowa' }, { code: 'KS', name: 'Kansas' },
    { code: 'KY', name: 'Kentucky' }, { code: 'LA', name: 'Louisiana' },
    { code: 'ME', name: 'Maine' }, { code: 'MD', name: 'Maryland' },
    { code: 'MA', name: 'Massachusetts' }, { code: 'MI', name: 'Michigan' },
    { code: 'MN', name: 'Minnesota' }, { code: 'MS', name: 'Mississippi' },
    { code: 'MO', name: 'Missouri' }, { code: 'MT', name: 'Montana' },
    { code: 'NE', name: 'Nebraska' }, { code: 'NV', name: 'Nevada' },
    { code: 'NH', name: 'New Hampshire' }, { code: 'NJ', name: 'New Jersey' },
    { code: 'NM', name: 'New Mexico' }, { code: 'NY', name: 'New York' },
    { code: 'NC', name: 'North Carolina' }, { code: 'ND', name: 'North Dakota' },
    { code: 'OH', name: 'Ohio' }, { code: 'OK', name: 'Oklahoma' },
    { code: 'OR', name: 'Oregon' }, { code: 'PA', name: 'Pennsylvania' },
    { code: 'RI', name: 'Rhode Island' }, { code: 'SC', name: 'South Carolina' },
    { code: 'SD', name: 'South Dakota' }, { code: 'TN', name: 'Tennessee' },
    { code: 'TX', name: 'Texas' }, { code: 'UT', name: 'Utah' },
    { code: 'VT', name: 'Vermont' }, { code: 'VA', name: 'Virginia' },
    { code: 'WA', name: 'Washington' }, { code: 'WV', name: 'West Virginia' },
    { code: 'WI', name: 'Wisconsin' }, { code: 'WY', name: 'Wyoming' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (step < 3) {
      setStep(step + 1);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await softLeadsApi.getMatched(formData);
      setIsSuccess(true);

      // Notify parent window if embedded in iframe
      if (window.parent !== window) {
        window.parent.postMessage({ type: 'fm-widget-success' }, '*');
      }
    } catch (err) {
      setError('Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            You&apos;re All Set!
          </h2>
          <p className="text-gray-600 mb-4">
            We&apos;re finding the perfect mortgage professional for you.
            Expect a call or email within 24 hours!
          </p>
          <p className="text-sm text-gray-500">
            Check your email for confirmation.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-md mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Get Pre-Approved
          </h1>
          <p className="text-gray-600">
            Connect with a licensed mortgage professional
          </p>
        </div>

        {/* Progress bar */}
        <div className="flex gap-1 mb-6">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`flex-1 h-1.5 rounded-full transition-colors ${
                s <= step ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Step 1: Contact Info */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Contact Information</h3>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <User className="inline w-4 h-4 mr-1" />
                  Full Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John Smith"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <Mail className="inline w-4 h-4 mr-1" />
                  Email Address *
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <Phone className="inline w-4 h-4 mr-1" />
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
          )}

          {/* Step 2: Loan Details */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">What are you looking for?</h3>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <Home className="inline w-4 h-4 mr-1" />
                  Loan Purpose
                </label>
                <select
                  value={formData.loan_purpose || ''}
                  onChange={(e) => setFormData({ ...formData, loan_purpose: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  <option value="purchase">Buying a Home</option>
                  <option value="refinance">Refinancing</option>
                  <option value="cash_out">Cash-Out Refinance</option>
                  <option value="pre_approval">Pre-Approval</option>
                  <option value="heloc">Home Equity Line</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <DollarSign className="inline w-4 h-4 mr-1" />
                  Estimated Loan Amount
                </label>
                <select
                  value={formData.estimated_amount?.toString() || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    estimated_amount: e.target.value ? parseInt(e.target.value) : undefined
                  })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  <option value="150000">Under $150,000</option>
                  <option value="250000">$150,000 - $300,000</option>
                  <option value="400000">$300,000 - $500,000</option>
                  <option value="650000">$500,000 - $750,000</option>
                  <option value="900000">$750,000 - $1,000,000</option>
                  <option value="1500000">Over $1,000,000</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Property State
                </label>
                <select
                  value={formData.property_state || ''}
                  onChange={(e) => setFormData({ ...formData, property_state: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select state...</option>
                  {states.map((state) => (
                    <option key={state.code} value={state.code}>
                      {state.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Preferences */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Your Preferences</h3>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  Preferred Language
                </label>
                <select
                  value={formData.preferred_language || ''}
                  onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Any language</option>
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="zh">Chinese</option>
                  <option value="vi">Vietnamese</option>
                  <option value="ko">Korean</option>
                  <option value="tl">Tagalog</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1">
                  <Clock className="inline w-4 h-4 mr-1" />
                  When do you need help?
                </label>
                <select
                  value={formData.timeframe || ''}
                  onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Select...</option>
                  <option value="immediately">Right away</option>
                  <option value="1_month">Within 1 month</option>
                  <option value="1_3_months">1-3 months</option>
                  <option value="3_6_months">3-6 months</option>
                  <option value="researching">Just researching</option>
                </select>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  By submitting, you agree to be contacted by a licensed mortgage professional.
                  Your information will be kept private and secure.
                </p>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex gap-3 mt-6">
            {step > 1 && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
            )}
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Submitting...
                </span>
              ) : step < 3 ? (
                'Next'
              ) : (
                'Get Matched'
              )}
            </button>
          </div>
        </form>

        {/* Footer */}
        <p className="text-xs text-gray-400 text-center mt-6">
          Powered by FaceMortgage
        </p>
      </div>
    </div>
  );
}

function EmbedLoadingFallback() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-6">
      <div className="animate-pulse max-w-md w-full">
        <div className="h-8 bg-gray-200 rounded w-1/2 mx-auto mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-8"></div>
        <div className="space-y-4">
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    </div>
  );
}

export default function EmbedGetMatchedPage() {
  return (
    <Suspense fallback={<EmbedLoadingFallback />}>
      <EmbedGetMatchedPageContent />
    </Suspense>
  );
}
