'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  User,
  Camera,
  Save,
  Bell,
  Shield,
  CreditCard,
  Video,
  MapPin,
  Briefcase,
  Languages,
  Upload,
  X,
  Check,
  AlertCircle,
  Trash2,
  RefreshCw,
  Clock,
  CheckCircle,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/utils';

// Video upload component with drag-drop, progress, preview
function VideoUploadSection({ onSuccess, onError }: { onSuccess: () => void; onError: (msg: string) => void }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentVideo, setCurrentVideo] = useState<{
    url: string;
    status: 'pending' | 'approved' | 'rejected';
    rejection_reason?: string;
  } | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_SIZE_MB = 100;
  const MAX_DURATION_SEC = 60;
  const ALLOWED_TYPES = ['video/mp4', 'video/webm', 'video/quicktime'];

  useEffect(() => {
    fetchCurrentVideo();
  }, []);

  async function fetchCurrentVideo() {
    try {
      const res = await apiClient.get('/professionals/me/video');
      if (res.data?.video_url) {
        setCurrentVideo({
          url: res.data.video_url,
          status: res.data.moderation_status || 'pending',
          rejection_reason: res.data.rejection_reason,
        });
      }
    } catch {
      // No video yet
    }
  }

  const validateFile = useCallback(async (file: File): Promise<string | null> => {
    // Check type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Invalid file type. Please upload MP4, WebM, or MOV.';
    }

    // Check size
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File too large. Maximum size is ${MAX_SIZE_MB}MB.`;
    }

    // Check duration using video element
    return new Promise((resolve) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        URL.revokeObjectURL(video.src);
        if (video.duration > MAX_DURATION_SEC) {
          resolve(`Video too long. Maximum duration is ${MAX_DURATION_SEC} seconds.`);
        } else {
          resolve(null);
        }
      };
      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        resolve('Could not read video file. Please try a different format.');
      };
      video.src = URL.createObjectURL(file);
    });
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const file = e.dataTransfer.files[0];
    if (file) await handleFileSelect(file);
  }, []);

  const handleFileSelect = async (file: File) => {
    const error = await validateFile(file);
    if (error) {
      onError(error);
      return;
    }

    // Create preview
    setPreviewUrl(URL.createObjectURL(file));

    // Upload file
    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      await apiClient.post('/professionals/me/video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;
          setUploadProgress(percent);
        },
      });

      setCurrentVideo({ url: URL.createObjectURL(file), status: 'pending' });
      setPreviewUrl(null);
      onSuccess();
    } catch (err) {
      onError('Failed to upload video. Please try again.');
      setPreviewUrl(null);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleRemoveVideo = async () => {
    try {
      await apiClient.delete('/professionals/me/video');
      setCurrentVideo(null);
    } catch {
      onError('Failed to remove video.');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Pre-recorded Video</h3>
        <p className="text-gray-500 mt-1">
          Upload a short video that plays on your grid card when you&apos;re busy or away.
          This helps borrowers get to know you before you&apos;re available.
        </p>
      </div>

      {/* Current Video Status */}
      {currentVideo && (
        <div className="border rounded-xl overflow-hidden">
          <video
            src={currentVideo.url}
            controls
            className="w-full h-64 bg-black object-contain"
          />
          <div className="p-4 bg-gray-50 border-t flex items-center justify-between">
            <div className="flex items-center gap-2">
              {currentVideo.status === 'approved' && (
                <span className="flex items-center gap-1 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  Approved
                </span>
              )}
              {currentVideo.status === 'pending' && (
                <span className="flex items-center gap-1 text-yellow-600">
                  <Clock className="w-5 h-5" />
                  Pending Review
                </span>
              )}
              {currentVideo.status === 'rejected' && (
                <div>
                  <span className="flex items-center gap-1 text-red-600">
                    <X className="w-5 h-5" />
                    Rejected
                  </span>
                  {currentVideo.rejection_reason && (
                    <p className="text-sm text-red-500 mt-1">{currentVideo.rejection_reason}</p>
                  )}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 flex items-center gap-1"
              >
                <RefreshCw className="w-4 h-4" />
                Replace
              </button>
              <button
                onClick={handleRemoveVideo}
                className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 flex items-center gap-1"
              >
                <Trash2 className="w-4 h-4" />
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className="border rounded-xl p-6">
          <div className="flex items-center gap-4 mb-4">
            {previewUrl && (
              <video src={previewUrl} className="w-24 h-16 object-cover rounded" muted />
            )}
            <div className="flex-1">
              <p className="font-medium text-gray-900">Uploading video...</p>
              <p className="text-sm text-gray-500">{uploadProgress}% complete</p>
            </div>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Drop Zone */}
      {!currentVideo && !uploading && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
        >
          <Video className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            {isDragOver ? 'Drop your video here!' : 'Drag and drop a video file here, or'}
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Upload className="w-4 h-4 inline mr-2" />
            Select Video
          </button>
          <p className="text-xs text-gray-400 mt-4">
            MP4, WebM, or MOV • Maximum 100MB, 60 seconds
          </p>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="video/mp4,video/webm,video/quicktime"
        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
        className="hidden"
      />

      {/* Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Video Guidelines</h4>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Keep it professional and introduce yourself</li>
          <li>• Good lighting and clear audio recommended</li>
          <li>• 30-60 seconds is ideal</li>
          <li>• Videos are reviewed before being published</li>
        </ul>
      </div>
    </div>
  );
}

// Email verification banner component
function EmailVerificationBanner({
  email,
  onSuccess,
  onError
}: {
  email: string;
  onSuccess: () => void;
  onError: (msg: string) => void;
}) {
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleResend() {
    setSending(true);
    try {
      const res = await apiClient.post('/auth/resend-verification');
      if (res.data.success) {
        setSent(true);
        onSuccess();
      } else {
        onError(res.data.message);
      }
    } catch {
      onError('Failed to send verification email. Please try again later.');
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="font-medium text-yellow-800">Email not verified</p>
        <p className="text-sm text-yellow-700 mt-1">
          Please verify your email address ({email}) to access all features.
        </p>
        {!sent ? (
          <button
            onClick={handleResend}
            disabled={sending}
            className="mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900 underline disabled:opacity-50"
          >
            {sending ? 'Sending...' : 'Resend verification email'}
          </button>
        ) : (
          <p className="mt-2 text-sm text-green-600 font-medium">
            ✓ Verification email sent! Check your inbox.
          </p>
        )}
      </div>
    </div>
  );
}


type Tab = 'profile' | 'notifications' | 'security' | 'video';

interface ProfileFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  company_name: string;
  job_title: string;
  bio: string;
  years_experience: number;
  nmls_id: string;
  timezone: string;
}

interface NotificationSettings {
  email_notifications: boolean;
  sms_notifications: boolean;
  push_notifications: boolean;
  call_reminders: boolean;
  lead_alerts: boolean;
  marketing_emails: boolean;
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Profile form
  const [profileData, setProfileData] = useState<ProfileFormData>({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    company_name: '',
    job_title: '',
    bio: '',
    years_experience: 0,
    nmls_id: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  });

  // Notification settings
  const [notifications, setNotifications] = useState<NotificationSettings>({
    email_notifications: true,
    sms_notifications: false,
    push_notifications: true,
    call_reminders: true,
    lead_alerts: true,
    marketing_emails: false,
  });

  // Password change
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Avatar
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(user?.avatar_url || null);

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      // Fetch professional profile if available
      const profileRes = await apiClient.get('/professionals/me');
      if (profileRes.data) {
        const prof = profileRes.data;
        setProfileData((prev) => ({
          ...prev,
          company_name: prof.company_name || '',
          job_title: prof.job_title || '',
          bio: prof.bio || '',
          years_experience: prof.years_experience || 0,
          nmls_id: prof.nmls_id || '',
          timezone: prof.timezone || prev.timezone,
        }));
      }

      // Fetch notification settings
      const notifRes = await apiClient.get('/users/me/notification-settings');
      if (notifRes.data) {
        setNotifications(notifRes.data);
      }
    } catch (error) {
      logger.error('Failed to fetch settings:', error);
    }
  }

  async function handleProfileSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // Update user profile
      await apiClient.put('/users/me', {
        first_name: profileData.first_name,
        last_name: profileData.last_name,
        phone: profileData.phone,
      });

      // Update professional profile
      await apiClient.put('/professionals/me', {
        company_name: profileData.company_name,
        job_title: profileData.job_title,
        bio: profileData.bio,
        years_experience: profileData.years_experience,
        nmls_id: profileData.nmls_id,
        timezone: profileData.timezone,
      });

      setSuccess('Profile updated successfully!');
    } catch (err) {
      setError('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  async function handleNotificationsSave() {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.put('/users/me/notification-settings', notifications);
      setSuccess('Notification preferences saved!');
    } catch (err) {
      setError('Failed to save notification preferences.');
    } finally {
      setSaving(false);
    }
  }

  async function handlePasswordChange() {
    if (passwords.new_password !== passwords.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (passwords.new_password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.post('/users/me/password', {
        current_password: passwords.current_password,
        new_password: passwords.new_password,
      });

      setSuccess('Password changed successfully!');
      setPasswords({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } };
        setError(axiosError.response?.data?.detail || 'Failed to change password');
      } else {
        setError('Failed to change password');
      }
    } finally {
      setSaving(false);
    }
  }

  function handleAvatarClick() {
    fileInputRef.current?.click();
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setAvatarPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Upload
    const formData = new FormData();
    formData.append('file', file);

    try {
      await apiClient.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess('Avatar updated!');
    } catch (err) {
      setError('Avatar upload not yet available');
    }
  }

  const tabs = [
    { id: 'profile' as Tab, label: 'Profile', icon: User },
    { id: 'notifications' as Tab, label: 'Notifications', icon: Bell },
    { id: 'security' as Tab, label: 'Security', icon: Shield },
    { id: 'video' as Tab, label: 'Video', icon: Video },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-8 py-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Manage your profile and preferences</p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-6">
        {/* Alerts */}
        {success && (
          <div role="alert" className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
            <Check className="w-5 h-5 text-green-600" aria-hidden="true" />
            <p className="text-green-800">{success}</p>
            <button onClick={() => setSuccess(null)} className="ml-auto" aria-label="Dismiss success message">
              <X className="w-4 h-4 text-green-600" aria-hidden="true" />
            </button>
          </div>
        )}

        {error && (
          <div role="alert" className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600" aria-hidden="true" />
            <p className="text-red-800">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto" aria-label="Dismiss error message">
              <X className="w-4 h-4 text-red-600" aria-hidden="true" />
            </button>
          </div>
        )}

        <div className="flex gap-8">
          {/* Tabs */}
          <div className="w-48 flex-shrink-0">
            <nav role="tablist" aria-label="Settings sections" className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  role="tab"
                  id={`tab-${tab.id}`}
                  aria-selected={activeTab === tab.id}
                  aria-controls={`panel-${tab.id}`}
                  tabIndex={activeTab === tab.id ? 0 : -1}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition ${activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                    }`}
                >
                  <tab.icon className="w-5 h-5" aria-hidden="true" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div
            role="tabpanel"
            id={`panel-${activeTab}`}
            aria-labelledby={`tab-${activeTab}`}
            className="flex-1 bg-white rounded-xl border p-6"
          >
            {activeTab === 'profile' && (
              <div className="space-y-6">
                {/* Email Verification Banner */}
                {user && !user.email_verified && (
                  <EmailVerificationBanner
                    email={user.email}
                    onSuccess={() => setSuccess('Verification email sent! Please check your inbox.')}
                    onError={(msg) => setError(msg)}
                  />
                )}

                {/* Avatar */}
                <div className="flex items-center gap-6">
                  <div className="relative">
                    <div
                      className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden cursor-pointer"
                      onClick={handleAvatarClick}
                    >
                      {avatarPreview ? (
                        <img
                          src={avatarPreview}
                          alt="Avatar"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <User className="w-10 h-10 text-gray-400" />
                      )}
                    </div>
                    <button
                      onClick={handleAvatarClick}
                      className="absolute bottom-0 right-0 p-2 bg-blue-600 rounded-full text-white hover:bg-blue-700"
                    >
                      <Camera className="w-4 h-4" />
                    </button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className="hidden"
                    />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Profile Photo</h3>
                    <p className="text-sm text-gray-500">
                      Upload a professional photo. This will appear on your grid card.
                    </p>
                  </div>
                </div>

                {/* Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="profile-first-name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      id="profile-first-name"
                      type="text"
                      value={profileData.first_name}
                      onChange={(e) =>
                        setProfileData({ ...profileData, first_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="profile-last-name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      id="profile-last-name"
                      type="text"
                      value={profileData.last_name}
                      onChange={(e) =>
                        setProfileData({ ...profileData, last_name: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="profile-email" className="block text-sm font-medium text-gray-700 mb-1">
                      Email
                    </label>
                    <input
                      id="profile-email"
                      type="email"
                      value={profileData.email}
                      disabled
                      className="w-full px-3 py-2 border rounded-lg bg-gray-50 text-gray-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="profile-phone" className="block text-sm font-medium text-gray-700 mb-1">
                      Phone
                    </label>
                    <input
                      id="profile-phone"
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) =>
                        setProfileData({ ...profileData, phone: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Professional Info */}
                <div className="pt-4 border-t">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Professional Details</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="prof-company" className="block text-sm font-medium text-gray-700 mb-1">
                        Company Name
                      </label>
                      <input
                        id="prof-company"
                        type="text"
                        value={profileData.company_name}
                        onChange={(e) =>
                          setProfileData({ ...profileData, company_name: e.target.value })
                        }
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label htmlFor="prof-title" className="block text-sm font-medium text-gray-700 mb-1">
                        Job Title
                      </label>
                      <input
                        id="prof-title"
                        type="text"
                        value={profileData.job_title}
                        onChange={(e) =>
                          setProfileData({ ...profileData, job_title: e.target.value })
                        }
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-4">
                    <div>
                      <label htmlFor="prof-nmls" className="block text-sm font-medium text-gray-700 mb-1">
                        NMLS ID
                      </label>
                      <input
                        id="prof-nmls"
                        type="text"
                        value={profileData.nmls_id}
                        onChange={(e) =>
                          setProfileData({ ...profileData, nmls_id: e.target.value })
                        }
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="123456"
                      />
                    </div>
                    <div>
                      <label htmlFor="prof-experience" className="block text-sm font-medium text-gray-700 mb-1">
                        Years of Experience
                      </label>
                      <input
                        id="prof-experience"
                        type="number"
                        value={profileData.years_experience}
                        onChange={(e) =>
                          setProfileData({
                            ...profileData,
                            years_experience: parseInt(e.target.value) || 0,
                          })
                        }
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        min="0"
                      />
                    </div>
                  </div>

                  <div className="mt-4">
                    <label htmlFor="prof-bio" className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
                    <textarea
                      id="prof-bio"
                      value={profileData.bio}
                      onChange={(e) =>
                        setProfileData({ ...profileData, bio: e.target.value })
                      }
                      rows={4}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Tell borrowers about yourself and your expertise..."
                    />
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    onClick={handleProfileSave}
                    disabled={saving}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Notification Preferences</h3>

                <div className="space-y-4">
                  {[
                    { key: 'email_notifications', label: 'Email Notifications', desc: 'Receive email updates about your account' },
                    { key: 'sms_notifications', label: 'SMS Notifications', desc: 'Get text messages for important updates' },
                    { key: 'push_notifications', label: 'Push Notifications', desc: 'Browser notifications for real-time alerts' },
                    { key: 'call_reminders', label: 'Call Reminders', desc: 'Reminders for scheduled calls' },
                    { key: 'lead_alerts', label: 'Lead Alerts', desc: 'Get notified when you receive a new lead' },
                    { key: 'marketing_emails', label: 'Marketing Emails', desc: 'Tips, news, and promotional content' },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between py-3 border-b last:border-0">
                      <div>
                        <p className="font-medium text-gray-900">{item.label}</p>
                        <p className="text-sm text-gray-500">{item.desc}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notifications[item.key as keyof NotificationSettings]}
                          onChange={(e) =>
                            setNotifications({
                              ...notifications,
                              [item.key]: e.target.checked,
                            })
                          }
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600" />
                      </label>
                    </div>
                  ))}
                </div>

                <div className="pt-4 flex justify-end">
                  <button
                    onClick={handleNotificationsSave}
                    disabled={saving}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Save className="w-4 h-4" />
                    {saving ? 'Saving...' : 'Save Preferences'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900">Change Password</h3>

                <div className="max-w-md space-y-4">
                  <div>
                    <label htmlFor="sec-current-pwd" className="block text-sm font-medium text-gray-700 mb-1">
                      Current Password
                    </label>
                    <input
                      id="sec-current-pwd"
                      type="password"
                      value={passwords.current_password}
                      onChange={(e) =>
                        setPasswords({ ...passwords, current_password: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label htmlFor="sec-new-pwd" className="block text-sm font-medium text-gray-700 mb-1">
                      New Password
                    </label>
                    <input
                      id="sec-new-pwd"
                      type="password"
                      value={passwords.new_password}
                      onChange={(e) =>
                        setPasswords({ ...passwords, new_password: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="At least 8 characters"
                    />
                  </div>
                  <div>
                    <label htmlFor="sec-confirm-pwd" className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm New Password
                    </label>
                    <input
                      id="sec-confirm-pwd"
                      type="password"
                      value={passwords.confirm_password}
                      onChange={(e) =>
                        setPasswords({ ...passwords, confirm_password: e.target.value })
                      }
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    onClick={handlePasswordChange}
                    disabled={saving || !passwords.current_password || !passwords.new_password}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                  >
                    <Shield className="w-4 h-4" />
                    {saving ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'video' && (
              <VideoUploadSection
                onSuccess={() => setSuccess('Video uploaded successfully! It will be reviewed before appearing on your profile.')}
                onError={(msg) => setError(msg)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
