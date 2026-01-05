'use client';

import { useState } from 'react';
import { X, Calendar, Clock, CheckCircle } from 'lucide-react';
import { scheduledCallsApi, ScheduleCallRequest } from '@/lib/api/endpoints';

interface ScheduleCallModalProps {
  professional: {
    id: string;
    name: string;
    avatar?: string;
  };
  onClose: () => void;
}

export default function ScheduleCallModal({
  professional,
  onClose,
}: ScheduleCallModalProps) {
  const [step, setStep] = useState<'time' | 'info' | 'success'>('time');
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    name: '',
    email: '',
    phone: '',
    loan_purpose: '',
    notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate available dates (next 7 days, excluding today)
  const getAvailableDates = () => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 1; i <= 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date.toISOString().split('T')[0]);
    }
    return dates;
  };

  // Time slots from 9am to 5pm
  const timeSlots = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
    '15:00', '15:30', '16:00', '16:30', '17:00'
  ];

  const formatTimeDisplay = (time: string) => {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const handleSubmit = async () => {
    if (step === 'time') {
      if (!formData.date || !formData.time) {
        setError('Please select a date and time');
        return;
      }
      setError(null);
      setStep('info');
      return;
    }

    if (!formData.name || !formData.email) {
      setError('Please fill in required fields');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const scheduledFor = new Date(`${formData.date}T${formData.time}:00`);
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

      const request: ScheduleCallRequest = {
        professional_id: professional.id,
        scheduled_for: scheduledFor.toISOString(),
        timezone,
        name: formData.name,
        email: formData.email,
        phone: formData.phone || undefined,
        loan_purpose: formData.loan_purpose || undefined,
        notes: formData.notes || undefined,
      };

      await scheduledCallsApi.schedule(request);
      setStep('success');
    } catch (err) {
      setError('Failed to schedule call. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === 'success') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Call Scheduled!</h2>
          <p className="text-gray-600 mb-4">
            Your call with {professional.name} is scheduled for{' '}
            <strong>
              {new Date(`${formData.date}T${formData.time}`).toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
              })} at {formatTimeDisplay(formData.time)}
            </strong>
          </p>
          <p className="text-sm text-gray-500 mb-6">
            You&apos;ll receive a confirmation email with details.
          </p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-white rounded-2xl p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Schedule a Call
            </h2>
            <p className="text-gray-600">
              with {professional.name}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress indicator */}
        <div className="flex gap-2 mb-6">
          <div className={`flex-1 h-1 rounded ${step === 'time' ? 'bg-blue-600' : 'bg-blue-200'}`} />
          <div className={`flex-1 h-1 rounded ${step === 'info' ? 'bg-blue-600' : 'bg-gray-200'}`} />
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {step === 'time' && (
          <div className="space-y-4">
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 mr-1" />
                Select a Date
              </label>
              <div className="grid grid-cols-3 gap-2">
                {getAvailableDates().map((date) => (
                  <button
                    key={date}
                    type="button"
                    onClick={() => setFormData({ ...formData, date })}
                    className={`p-2 text-sm rounded-lg border transition-colors ${
                      formData.date === date
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {new Date(date).toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 mr-1" />
                Select a Time
              </label>
              <div className="grid grid-cols-4 gap-2 max-h-48 overflow-y-auto">
                {timeSlots.map((time) => (
                  <button
                    key={time}
                    type="button"
                    onClick={() => setFormData({ ...formData, time })}
                    className={`p-2 text-sm rounded-lg border transition-colors ${
                      formData.time === time
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {formatTimeDisplay(time)}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 'info' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Your Name *
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="(555) 123-4567"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                What would you like to discuss?
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="I'm looking to refinance my home..."
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 mt-6">
          {step === 'info' && (
            <button
              type="button"
              onClick={() => setStep('time')}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Back
            </button>
          )}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Scheduling...' : step === 'time' ? 'Next' : 'Schedule Call'}
          </button>
        </div>
      </div>
    </div>
  );
}
