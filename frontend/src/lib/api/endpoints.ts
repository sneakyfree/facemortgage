import apiClient from './client';
import type {
  User,
  Professional,
  ProfessionalGridResponse,
  GridFilters,
  LoginRequest,
  RegisterRequest,
  TokenPair,
  Specialty,
  Language,
  County,
  InitiateCallResponse,
  CallStateResponse,
  RateCallRequest,
  RateCallResponse,
  EndCallResponse,
  Lead,
  LeadListResponse,
  LeadStats,
  LeadCreate,
  LeadUpdate,
  LeadActivity,
  LeadActivityCreate,
  LeadStatus,
  SubscriptionPlan,
  Subscription,
  CreateSubscriptionResponse,
  BidWallet,
  DepositResponse,
  BillingPortalResponse,
  SubscriptionTier,
  VideoUploadResponse,
  AnalyticsOverview,
  GeoLocationData,
  USState,
} from '@/types';

// Auth
export const authApi = {
  login: async (data: LoginRequest): Promise<TokenPair> => {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post('/auth/register', data);
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenPair> => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    try {
      const response = await apiClient.get('/auth/me');
      return response.data;
    } catch (error) {
      // If normal /me fails, try mock endpoint (for development)
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // Decode the JWT to get the user ID
          const payload = JSON.parse(atob(token.split('.')[1]));
          const userId = payload.sub;
          const mockResponse = await apiClient.get(`/auth/me/mock/${userId}`);
          return mockResponse.data;
        } catch {
          // If mock also fails, rethrow original error
        }
      }
      throw error;
    }
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },
};

// Professionals
export const professionalsApi = {
  getGrid: async (
    filters?: GridFilters,
    limit = 50,
    offset = 0
  ): Promise<ProfessionalGridResponse> => {
    const params = new URLSearchParams();
    if (filters?.language) params.append('language', filters.language);
    if (filters?.specialty) params.append('specialty', filters.specialty.toString());
    if (filters?.county) params.append('county', filters.county.toString());
    // Backend uses 'state' parameter, frontend uses 'state_code'
    if (filters?.state_code) params.append('state', filters.state_code);
    if (filters?.user_type) params.append('user_type', filters.user_type);
    if (filters?.min_rating) params.append('min_rating', filters.min_rating.toString());
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await apiClient.get(`/professionals?${params.toString()}`);
    return response.data;
  },

  getById: async (id: string): Promise<Professional> => {
    const response = await apiClient.get(`/professionals/${id}`);
    return response.data;
  },

  updateMyProfile: async (data: Partial<Professional>): Promise<Professional> => {
    const response = await apiClient.put('/professionals/me', data);
    return response.data;
  },

  updateMyStatus: async (status: string): Promise<void> => {
    await apiClient.patch('/professionals/me/status', { status });
  },
};

// Lookups
export const lookupsApi = {
  getSpecialties: async (category?: string): Promise<Specialty[]> => {
    const params = category ? `?category=${category}` : '';
    const response = await apiClient.get(`/lookups/specialties${params}`);
    return response.data;
  },

  getLanguages: async (): Promise<Language[]> => {
    const response = await apiClient.get('/lookups/languages');
    return response.data;
  },

  getCounties: async (stateCode?: string): Promise<County[]> => {
    const params = stateCode ? `?state_code=${stateCode}` : '';
    const response = await apiClient.get(`/lookups/counties${params}`);
    return response.data;
  },

  getStates: async (): Promise<USState[]> => {
    const response = await apiClient.get('/lookups/states');
    return response.data;
  },

  /**
   * Get geo-location based on coordinates or IP address.
   * If lat/lon are provided, performs reverse geocoding.
   * Otherwise, uses the client's IP address.
   */
  getGeoLocation: async (options?: {
    lat?: number;
    lon?: number;
    ip?: string;
  }): Promise<GeoLocationData> => {
    const params = new URLSearchParams();
    if (options?.lat !== undefined) params.append('lat', options.lat.toString());
    if (options?.lon !== undefined) params.append('lon', options.lon.toString());
    if (options?.ip) params.append('ip', options.ip);

    const queryString = params.toString();
    const response = await apiClient.get(`/lookups/geo${queryString ? `?${queryString}` : ''}`);
    return response.data;
  },
};

// Calls
export interface CaptureLeadData {
  name: string;
  email: string;
  phone?: string;
  loan_purpose?: string;
  estimated_amount?: number;
  notes?: string;
}

export interface CaptureLeadResponse {
  success: boolean;
  lead_id: string;
}

export const callsApi = {
  initiate: async (
    professionalId: string,
    options?: {
      anonymous_session_id?: string;
      device_fingerprint?: string;
    }
  ): Promise<InitiateCallResponse> => {
    const payload: Record<string, unknown> = { professional_id: professionalId };

    if (options?.anonymous_session_id) {
      payload.anonymous_session_id = options.anonymous_session_id;
      payload.device_fingerprint = options.device_fingerprint;
    }

    const response = await apiClient.post('/calls', payload);
    return response.data;
  },

  getState: async (roomId: string): Promise<CallStateResponse> => {
    const response = await apiClient.get(`/calls/${roomId}`);
    return response.data;
  },

  end: async (roomId: string): Promise<EndCallResponse> => {
    const response = await apiClient.post(`/calls/${roomId}/end`);
    return response.data;
  },

  rate: async (roomId: string, data: RateCallRequest): Promise<RateCallResponse> => {
    const response = await apiClient.post(`/calls/${roomId}/rate`, data);
    return response.data;
  },

  /**
   * Capture lead info from anonymous caller after call ends.
   * Only works for anonymous calls.
   */
  captureLead: async (callId: string, data: CaptureLeadData): Promise<CaptureLeadResponse> => {
    const response = await apiClient.post(`/calls/${callId}/capture-lead`, data);
    return response.data;
  },
};

// Leads
export const leadsApi = {
  list: async (params?: {
    status?: LeadStatus;
    search?: string;
    sort_by?: 'created_at' | 'updated_at' | 'estimated_loan_amount' | 'next_followup_at';
    sort_order?: 'asc' | 'desc';
    page?: number;
    page_size?: number;
  }): Promise<LeadListResponse> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.sort_by) queryParams.append('sort_by', params.sort_by);
    if (params?.sort_order) queryParams.append('sort_order', params.sort_order);
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

    const response = await apiClient.get(`/leads?${queryParams.toString()}`);
    return response.data;
  },

  getStats: async (): Promise<LeadStats> => {
    const response = await apiClient.get('/leads/stats');
    return response.data;
  },

  getById: async (leadId: string): Promise<Lead> => {
    const response = await apiClient.get(`/leads/${leadId}`);
    return response.data;
  },

  create: async (data: LeadCreate): Promise<Lead> => {
    const response = await apiClient.post('/leads', data);
    return response.data;
  },

  update: async (leadId: string, data: LeadUpdate): Promise<Lead> => {
    const response = await apiClient.patch(`/leads/${leadId}`, data);
    return response.data;
  },

  delete: async (leadId: string): Promise<void> => {
    await apiClient.delete(`/leads/${leadId}`);
  },

  addActivity: async (leadId: string, data: LeadActivityCreate): Promise<LeadActivity> => {
    const response = await apiClient.post(`/leads/${leadId}/activities`, data);
    return response.data;
  },

  getActivities: async (leadId: string): Promise<LeadActivity[]> => {
    const response = await apiClient.get(`/leads/${leadId}/activities`);
    return response.data;
  },
};

// Billing
export const billingApi = {
  getPlans: async (): Promise<SubscriptionPlan[]> => {
    const response = await apiClient.get('/billing/plans');
    return response.data;
  },

  getSubscription: async (): Promise<Subscription | null> => {
    const response = await apiClient.get('/billing/subscription');
    return response.data;
  },

  createSubscription: async (tier: SubscriptionTier): Promise<CreateSubscriptionResponse> => {
    const response = await apiClient.post('/billing/subscription', { tier });
    return response.data;
  },

  cancelSubscription: async (): Promise<{ message: string; current_period_end: string }> => {
    const response = await apiClient.post('/billing/subscription/cancel');
    return response.data;
  },

  reactivateSubscription: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/billing/subscription/reactivate');
    return response.data;
  },

  getWallet: async (): Promise<BidWallet> => {
    const response = await apiClient.get('/billing/wallet');
    return response.data;
  },

  createDeposit: async (amount: number): Promise<DepositResponse> => {
    const response = await apiClient.post('/billing/wallet/deposit', { amount });
    return response.data;
  },

  updateBidSettings: async (bidAmount: number, dailyBudget?: number): Promise<{ bid_amount: number; daily_budget?: number }> => {
    const response = await apiClient.put('/billing/bid-settings', {
      bid_amount: bidAmount,
      daily_budget: dailyBudget,
    });
    return response.data;
  },

  createPortalSession: async (): Promise<BillingPortalResponse> => {
    const response = await apiClient.post('/billing/portal');
    return response.data;
  },
};

// Videos
export const videosApi = {
  uploadPrerecorded: async (file: File): Promise<VideoUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/videos/me/prerecorded', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  deletePrerecorded: async (): Promise<{ message: string }> => {
    const response = await apiClient.delete('/videos/me/prerecorded');
    return response.data;
  },
};

// Analytics
export const analyticsApi = {
  getOverview: async (): Promise<AnalyticsOverview> => {
    const response = await apiClient.get('/analytics/overview');
    return response.data;
  },

  getDashboard: async (period: '7d' | '30d' | '90d' | '12m' = '30d'): Promise<{
    period: string;
    overview: AnalyticsOverview;
    call_metrics: {
      total_calls: number;
      answered_calls: number;
      missed_calls: number;
      avg_duration_seconds: number;
      avg_pickup_time_seconds: number;
    };
    lead_metrics: {
      total_leads: number;
      new_leads: number;
      qualified_leads: number;
      won_leads: number;
      conversion_rate: number;
    };
    grid_performance: {
      impressions: number;
      clicks: number;
      calls_from_grid: number;
      avg_position: number;
      click_through_rate: number;
    };
  }> => {
    const response = await apiClient.get(`/analytics/dashboard?period=${period}`);
    return response.data;
  },

  getRecentActivity: async (limit = 10): Promise<{
    activities: Array<{
      id: string;
      type: 'call' | 'lead' | 'review';
      title: string;
      description: string;
      time: string;
    }>;
  }> => {
    const response = await apiClient.get(`/analytics/recent-activity?limit=${limit}`);
    return response.data;
  },
};

// Grid Tracking
export const gridTrackingApi = {
  trackImpressions: async (impressions: Array<{ professional_id: string; position: number }>, sessionId?: string): Promise<{
    success: boolean;
    tracked_count: number;
    message: string;
  }> => {
    const response = await apiClient.post('/grid/track-impressions', {
      impressions,
      session_id: sessionId,
    });
    return response.data;
  },

  trackClick: async (data: {
    professional_id: string;
    click_type: 'profile_view' | 'call_initiated' | 'video_preview';
    grid_position?: number;
    session_id?: string;
    filter_context?: Record<string, unknown>;
  }): Promise<{
    success: boolean;
    tracked_count: number;
    message: string;
  }> => {
    const response = await apiClient.post('/grid/track-click', data);
    return response.data;
  },

  getTodayStats: async (): Promise<{
    date: string;
    total_impressions: number;
    total_clicks: number;
    total_calls_initiated: number;
    unique_professionals_shown: number;
    click_through_rate: number;
  }> => {
    const response = await apiClient.get('/grid/stats/today');
    return response.data;
  },
};

// Scheduled Calls
export interface ScheduleCallRequest {
  professional_id: string;
  scheduled_for: string;  // ISO datetime
  timezone: string;
  name: string;
  email: string;
  phone?: string;
  loan_purpose?: string;
  notes?: string;
}

export interface ScheduleCallResponse {
  id: string;
  scheduled_for: string;
  professional_name: string;
  confirmation_sent: boolean;
}

export interface ScheduledCallDetail {
  id: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
  scheduled_for: string;
  timezone: string;
  loan_purpose?: string;
  notes?: string;
  status: string;
  created_at: string;
}

export const scheduledCallsApi = {
  schedule: async (data: ScheduleCallRequest): Promise<ScheduleCallResponse> => {
    const response = await apiClient.post('/scheduled-calls', data);
    return response.data;
  },

  getMyScheduled: async (): Promise<ScheduledCallDetail[]> => {
    const response = await apiClient.get('/scheduled-calls/my-scheduled');
    return response.data;
  },

  getProfessionalUpcoming: async (): Promise<ScheduledCallDetail[]> => {
    const response = await apiClient.get('/scheduled-calls/professional/upcoming');
    return response.data;
  },

  confirm: async (scheduledCallId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/scheduled-calls/${scheduledCallId}/confirm`);
    return response.data;
  },

  cancel: async (scheduledCallId: string, reason?: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/scheduled-calls/${scheduledCallId}/cancel`, { reason });
    return response.data;
  },
};

// Soft Leads (Get Matched)
export interface GetMatchedRequest {
  name: string;
  email: string;
  phone?: string;
  loan_purpose?: string;
  estimated_amount?: number;
  property_state?: string;
  preferred_language?: string;
  timeframe?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
}

export interface GetMatchedResponse {
  success: boolean;
  message: string;
  lead_id: string;
}

export interface SoftLeadDetail {
  id: string;
  name: string;
  email: string;
  phone?: string;
  loan_purpose?: string;
  estimated_amount?: number;
  property_state?: string;
  timeframe?: string;
  status: string;
  matched_at?: string;
  created_at: string;
}

export const softLeadsApi = {
  getMatched: async (data: GetMatchedRequest): Promise<GetMatchedResponse> => {
    const response = await apiClient.post('/soft-leads/get-matched', data);
    return response.data;
  },

  getPending: async (): Promise<SoftLeadDetail[]> => {
    const response = await apiClient.get('/soft-leads/professional/pending');
    return response.data;
  },

  markContacted: async (softLeadId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/soft-leads/${softLeadId}/contact`);
    return response.data;
  },

  convert: async (softLeadId: string): Promise<{ message: string; lead_id: string }> => {
    const response = await apiClient.post(`/soft-leads/${softLeadId}/convert`);
    return response.data;
  },
};

// Partnerships
export interface InvitePartnerRequest {
  realtor_name: string;
  realtor_email: string;
  realtor_phone?: string;
  realtor_company?: string;
}

export interface PartnershipDetail {
  id: string;
  status: string;
  tier: string;
  loan_officer_name?: string;
  loan_officer_company?: string;
  realtor_name?: string;
  realtor_email?: string;
  referral_count: number;
  created_at: string;
  accepted_at?: string;
}

export interface SubmitReferralRequest {
  borrower_name: string;
  borrower_email: string;
  borrower_phone?: string;
  property_address?: string;
  loan_purpose?: string;
  estimated_amount?: number;
  notes?: string;
}

export interface ReferralDetail {
  id: string;
  borrower_name: string;
  borrower_email: string;
  borrower_phone?: string;
  property_address?: string;
  loan_purpose?: string;
  status: string;
  source: string;
  created_at: string;
}

export const partnershipsApi = {
  invitePartner: async (data: InvitePartnerRequest): Promise<{ partnership_id: string; invitation_sent: boolean }> => {
    const response = await apiClient.post('/partnerships/invite', data);
    return response.data;
  },

  getMyPartnerships: async (): Promise<PartnershipDetail[]> => {
    const response = await apiClient.get('/partnerships/my-partnerships');
    return response.data;
  },

  getReferrals: async (partnershipId: string): Promise<ReferralDetail[]> => {
    const response = await apiClient.get(`/partnerships/${partnershipId}/referrals`);
    return response.data;
  },

  acceptPartnership: async (token: string): Promise<{ success: boolean; partnership_id: string; message: string }> => {
    const response = await apiClient.post(`/partnerships/accept/${token}`);
    return response.data;
  },

  submitReferral: async (partnershipId: string, data: SubmitReferralRequest): Promise<ReferralDetail> => {
    const response = await apiClient.post(`/partnerships/${partnershipId}/refer`, data);
    return response.data;
  },

  terminatePartnership: async (partnershipId: string): Promise<{ message: string; status: string }> => {
    const response = await apiClient.post(`/partnerships/${partnershipId}/terminate`);
    return response.data;
  },

  getWidgetCode: async (partnershipId: string): Promise<{ widget_token: string; embed_code: string }> => {
    const response = await apiClient.get(`/partnerships/${partnershipId}/widget-code`);
    return response.data;
  },

  enableWidget: async (partnershipId: string): Promise<{ message: string; widget_token: string }> => {
    const response = await apiClient.post(`/partnerships/${partnershipId}/widget/enable`);
    return response.data;
  },
};

// Devices (Push Notifications)
export interface DeviceInfo {
  token: string;
  platform: 'ios' | 'android' | 'web';
  device_name?: string;
  created_at: string;
}

export const devicesApi = {
  /**
   * Register a device for push notifications.
   * Call this when the app starts or when the FCM token changes.
   */
  register: async (data: {
    token: string;
    platform: 'ios' | 'android' | 'web';
    device_name?: string;
  }): Promise<{ success: boolean; message: string; device_count: number }> => {
    const response = await apiClient.post('/devices/register', data);
    return response.data;
  },

  /**
   * Unregister a device from push notifications.
   * Call this when the user logs out or disables notifications.
   */
  unregister: async (token: string): Promise<{ success: boolean; message: string; device_count: number }> => {
    const response = await apiClient.delete('/devices/unregister', { data: { token } });
    return response.data;
  },

  /**
   * Get all registered devices for the current user.
   */
  getMyDevices: async (): Promise<DeviceInfo[]> => {
    const response = await apiClient.get('/devices/my-devices');
    return response.data;
  },

  /**
   * Enable or disable push notifications for the user.
   */
  togglePush: async (enabled: boolean): Promise<{ success: boolean; push_enabled: boolean }> => {
    const response = await apiClient.post(`/devices/toggle-push?enabled=${enabled}`);
    return response.data;
  },
};
