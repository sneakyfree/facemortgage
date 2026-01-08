'use client';

import { useState, useCallback } from 'react';
import { X, UserPlus, CheckCircle } from 'lucide-react';
import { partnershipsApi, InvitePartnerRequest } from '@/lib/api/endpoints';
import { useFocusTrap, useEscapeKey } from '@/hooks/useFocusTrap';

interface InvitePartnerModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function InvitePartnerModal({
  onClose,
  onSuccess,
}: InvitePartnerModalProps) {
  const [formData, setFormData] = useState<InvitePartnerRequest>({
    realtor_name: '',
    realtor_email: '',
    realtor_phone: '',
    realtor_company: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Accessibility: Focus trap and escape key handling
  const modalRef = useFocusTrap<HTMLDivElement>(true);
  const handleEscape = useCallback(() => onClose(), [onClose]);
  useEscapeKey(true, handleEscape);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await partnershipsApi.invitePartner(formData);
      setIsSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send invitation';
      setError(errorMessage);
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
          aria-labelledby="invite-success-title"
          className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 text-center"
        >
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" aria-hidden="true" />
          <h2 id="invite-success-title" className="text-2xl font-bold text-gray-900 mb-2">Invitation Sent!</h2>
          <p className="text-gray-600">
            {formData.realtor_name} will receive an email with instructions to join your partnership.
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
        aria-labelledby="invite-modal-title"
        className="bg-white rounded-2xl p-6 max-w-md w-full mx-4"
      >
        <div className="flex justify-between items-start mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <UserPlus className="w-6 h-6 text-blue-600" aria-hidden="true" />
            </div>
            <div>
              <h2 id="invite-modal-title" className="text-xl font-bold text-gray-900">Invite Partner</h2>
              <p className="text-sm text-gray-600">Add a realtor to your network</p>
            </div>
          </div>
          <button
            onClick={onClose}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Realtor Name *
            </label>
            <input
              type="text"
              required
              value={formData.realtor_name}
              onChange={(e) => setFormData({ ...formData, realtor_name: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Jane Smith"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              required
              value={formData.realtor_email}
              onChange={(e) => setFormData({ ...formData, realtor_email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="jane@realty.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone Number
            </label>
            <input
              type="tel"
              value={formData.realtor_phone || ''}
              onChange={(e) => setFormData({ ...formData, realtor_phone: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="(555) 123-4567"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company/Brokerage
            </label>
            <input
              type="text"
              value={formData.realtor_company || ''}
              onChange={(e) => setFormData({ ...formData, realtor_company: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ABC Realty"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Sending...' : 'Send Invitation'}
            </button>
          </div>
        </form>

        <p className="text-xs text-gray-500 text-center mt-4">
          They&apos;ll receive an email with a link to accept the partnership.
        </p>
      </div>
    </div>
  );
}
