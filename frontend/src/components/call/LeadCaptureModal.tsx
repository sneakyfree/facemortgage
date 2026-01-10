'use client';

import { useState, useCallback } from 'react';
import { X, User, Mail, Phone, CheckCircle } from 'lucide-react';
import { callsApi, CaptureLeadData } from '@/lib/api/endpoints';
import { useFocusTrap, useEscapeKey } from '@/hooks/useFocusTrap';

interface LeadCaptureModalProps {
  callId: string;
  professionalName: string;
  onClose: () => void;
  onSkip: () => void;
}

export default function LeadCaptureModal({
  callId,
  professionalName,
  onClose,
  onSkip,
}: LeadCaptureModalProps) {
  const [formData, setFormData] = useState<CaptureLeadData>({
    name: '',
    email: '',
    phone: '',
    loan_purpose: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Accessibility: Focus trap and escape key handling
  const modalRef = useFocusTrap<HTMLDivElement>(true);
  const handleEscape = useCallback(() => onSkip(), [onSkip]);
  useEscapeKey(true, handleEscape);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await callsApi.captureLead(callId, formData);
      setIsSuccess(true);
      setTimeout(onClose, 2000);
    } catch (err) {
      setError('Failed to save your information. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="success-title"
          className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 text-center"
        >
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" aria-hidden="true" />
          <h2 id="success-title" className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h2>
          <p className="text-gray-600">
            {professionalName} will follow up with you shortly.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="lead-capture-title"
        className="bg-white rounded-2xl p-8 max-w-md w-full mx-4"
      >
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 id="lead-capture-title" className="text-2xl font-bold text-gray-900">
              Stay Connected
            </h2>
            <p className="text-gray-600 mt-1">
              Share your info so {professionalName} can follow up
            </p>
          </div>
          <button
            onClick={onSkip}
            aria-label="Close modal"
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" aria-hidden="true" />
          </button>
        </div>

        {error && (
          <div role="alert" className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="lead-name" className="block text-sm font-medium text-gray-700 mb-1">
              Your Name *
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
              <input
                id="lead-name"
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="John Smith"
              />
            </div>
          </div>

          <div>
            <label htmlFor="lead-email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address *
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
              <input
                id="lead-email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="john@example.com"
              />
            </div>
          </div>

          <div>
            <label htmlFor="lead-phone" className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" aria-hidden="true" />
              <input
                id="lead-phone"
                type="tel"
                value={formData.phone || ''}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="(555) 123-4567"
              />
            </div>
          </div>

          <div>
            <label htmlFor="lead-purpose" className="block text-sm font-medium text-gray-700 mb-1">
              What are you looking for?
            </label>
            <select
              id="lead-purpose"
              value={formData.loan_purpose || ''}
              onChange={(e) => setFormData({ ...formData, loan_purpose: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select...</option>
              <option value="purchase">Buying a Home</option>
              <option value="refinance">Refinancing</option>
              <option value="cash_out">Cash-Out Refinance</option>
              <option value="pre_approval">Pre-Approval</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onSkip}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Skip for Now
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Saving...' : 'Submit'}
            </button>
          </div>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          Your information is secure and will only be shared with {professionalName}.
        </p>
      </div>
    </div>
  );
}
