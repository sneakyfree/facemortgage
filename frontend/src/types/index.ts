export type UserType = 'borrower' | 'loan_officer' | 'realtor' | 'title_rep' | 'attorney';

export type ProfessionalStatus = 'offline' | 'online_available' | 'online_busy' | 'in_call' | 'away';

export type SubscriptionTier = 'free' | 'basic' | 'professional' | 'premium';

export interface ProfessionalProfileRef {
  id: string;
  status?: ProfessionalStatus;
  subscription_tier?: SubscriptionTier;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  user_type: UserType;
  email_verified: boolean;
  phone_verified: boolean;
  is_active: boolean;
  created_at: string;
  professional_profile?: ProfessionalProfileRef;
}

export interface Specialty {
  id: number;
  name: string;
  category?: string;
}

export interface Language {
  id: number;
  code: string;
  name: string;
  proficiency?: string;
}

export interface County {
  id: number;
  state_code: string;
  county_name: string;
}

export interface ProfessionalStats {
  total_calls_completed: number;
  avg_pickup_time_seconds?: number;
  total_reviews: number;
  avg_rating: number;
  time_online_today_seconds: number;
}

export interface Professional {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email?: string;
  avatar_url?: string;
  user_type: UserType;

  company_name?: string;
  job_title?: string;
  bio?: string;
  years_experience?: number;
  nmls_id?: string;
  timezone: string;

  status: ProfessionalStatus;
  subscription_tier: SubscriptionTier;

  prerecorded_video_url?: string;
  webcam_enabled: boolean;
  nmls_verified: boolean;
  is_featured: boolean;
  profile_complete: boolean;

  stats?: ProfessionalStats;
  specialties: Specialty[];
  languages: Language[];
  service_areas: County[];

  created_at: string;
  updated_at: string;
}

export interface ProfessionalGridItem {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
  user_type: UserType;

  company_name?: string;
  job_title?: string;
  bio?: string;
  nmls_id?: string;

  status: ProfessionalStatus;
  subscription_tier: SubscriptionTier;

  prerecorded_video_url?: string;
  video_type: 'live' | 'recorded';
  video_stream_url?: string;
  thumbnail_url?: string;
  video_url?: string;

  avg_rating: number;
  total_reviews: number;
  avg_pickup_time_seconds?: number;
  years_experience?: number;

  specialty_names: string[];
  language_codes: string[];

  grid_position: number;
  score: number;
}

export interface GridFilters {
  language?: string;
  specialty?: number;
  county?: number;
  state_code?: string;
  user_type?: UserType;
  min_rating?: number;
}

// Geo-location types
export interface GeoLocationData {
  state_code: string | null;
  state_name: string | null;
  city: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  source: 'browser' | 'ip' | 'cached' | 'coordinates' | 'unknown';
}

export interface USState {
  code: string;
  name: string;
}

export interface ProfessionalGridResponse {
  professionals: ProfessionalGridItem[];
  total: number;
  filters_applied: GridFilters;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
  user_type: UserType;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ==================== Calls ====================

export type CallState = 'waiting' | 'ringing' | 'connected' | 'ended' | 'failed';

export interface InitiateCallResponse {
  room_id: string;
  signaling_url: string;
  ice_servers: RTCIceServer[];
  professional_name: string;
  professional_avatar?: string;
}

export interface CallStateResponse {
  room_id: string;
  state: CallState;
  borrower_id: string;
  professional_id: string;
  created_at: string;
  answered_at?: string;
  ended_at?: string;
}

export interface RateCallRequest {
  overall_rating: number;
  communication_rating?: number;
  knowledge_rating?: number;
  responsiveness_rating?: number;
  content?: string;
}

export interface RateCallResponse {
  message: string;
  review_id: string;
}

export interface EndCallResponse {
  message: string;
  duration_seconds?: number;
  pickup_time_seconds?: number;
}

// ==================== Leads ====================

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'proposal_sent' | 'negotiation' | 'won' | 'lost';

export type LeadActivityType = 'note' | 'call' | 'email' | 'meeting' | 'status_change' | 'system';

export interface LeadListItem {
  id: string;
  lead_status: LeadStatus;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  loan_purpose?: string;
  estimated_loan_amount?: number;
  next_followup_at?: string;
  estimated_value?: number;
  last_activity_at?: string;
  activity_count: number;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  leads: LeadListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Lead {
  id: string;
  professional_id: string;
  lead_status: LeadStatus;
  borrower?: BorrowerInfo;
  source_call?: SourceCallInfo;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  loan_purpose?: string;
  property_address?: string;
  estimated_property_value?: number;
  estimated_loan_amount?: number;
  last_contact_at?: string;
  next_followup_at?: string;
  notes?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  estimated_value?: number;
  actual_value?: number;
  activities: LeadActivity[];
  created_at: string;
  updated_at: string;
}

export interface BorrowerInfo {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  avatar_url?: string;
}

export interface SourceCallInfo {
  id: string;
  initiated_at: string;
  duration_seconds?: number;
  rating?: number;
}

export interface LeadActivity {
  id: string;
  lead_id: string;
  activity_type: LeadActivityType;
  description: string;
  metadata?: Record<string, unknown>;
  performed_by?: string;
  created_at: string;
}

export interface LeadStats {
  total_leads: number;
  leads_by_status: Record<string, number>;
  new_leads_today: number;
  new_leads_this_week: number;
  new_leads_this_month: number;
  conversion_rate: number;
  total_value_won: number;
  total_value_pipeline: number;
  leads_needing_followup: number;
}

export interface LeadCreate {
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  loan_purpose?: string;
  property_address?: string;
  estimated_property_value?: number;
  estimated_loan_amount?: number;
  notes?: string;
  borrower_id?: string;
  source_call_id?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
}

export interface LeadUpdate {
  lead_status?: LeadStatus;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  loan_purpose?: string;
  property_address?: string;
  estimated_property_value?: number;
  estimated_loan_amount?: number;
  next_followup_at?: string;
  notes?: string;
  estimated_value?: number;
  actual_value?: number;
}

export interface LeadActivityCreate {
  activity_type: LeadActivityType;
  description: string;
  metadata?: Record<string, unknown>;
}

// ==================== Billing ====================

export type SubscriptionStatus = 'pending' | 'active' | 'past_due' | 'cancelled';

export interface SubscriptionPlan {
  tier: string;
  name: string;
  price: number;
  features: string[];
}

export interface Subscription {
  id: string;
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  stripe_subscription_id?: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
}

export interface CreateSubscriptionResponse {
  subscription_id: string;
  status: string;
  client_secret?: string;
  current_period_end: string;
}

export interface BidWallet {
  available_credits: number;
  reserved_credits: number;
  total_deposited: number;
  total_spent: number;
}

export interface DepositResponse {
  checkout_url: string;
}

export interface BillingPortalResponse {
  portal_url: string;
}

// ==================== Videos ====================

export interface VideoUploadResponse {
  message: string;
  video_url: string;
}

// ==================== Analytics ====================

export interface AnalyticsOverview {
  total_calls: number;
  total_leads: number;
  total_reviews: number;
  avg_rating: number;
  avg_pickup_time_seconds: number;
  total_time_online_seconds: number;
  revenue_this_month?: number;
}
