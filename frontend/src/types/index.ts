export type UserRole =
  | "super_admin"
  | "admin"
  | "manager"
  | "analyst"
  | "viewer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  avatar_url?: string | null;
  phone?: string | null;
  timezone: string;
  last_login_at?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export type WebsiteStatus =
  | "pending"
  | "queued"
  | "auditing"
  | "completed"
  | "failed"
  | "archived";

export interface Website {
  id: string;
  owner_id: string;
  url: string;
  domain: string;
  company_name?: string | null;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  industry?: string | null;
  status: WebsiteStatus;
  notes?: string | null;
  tags?: string[] | null;
  last_audited_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type AuditStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface AuditCategoryBreakdown {
  score?: number;
  issues?: {
    items?: { severity: string; code: string; message: string }[];
  };
  recommendations?: {
    items?: { priority: string; title: string; description: string }[];
  };
  checks?: Record<string, unknown>;
}

export interface AuditReport {
  id: string;
  website_id: string;
  created_by?: string | null;
  status: AuditStatus;
  overall_score?: number | null;
  security_score?: number | null;
  mobile_score?: number | null;
  technical_seo_score?: number | null;
  accessibility_score?: number | null;
  conversion_score?: number | null;
  lead_opportunity_score?: number | null;
  lead_classification?: LeadClassification | null;
  sales_summary?: string | null;
  category_breakdown?: {
    security?: AuditCategoryBreakdown;
    mobile?: AuditCategoryBreakdown;
    technical_seo?: AuditCategoryBreakdown;
    accessibility?: AuditCategoryBreakdown;
    marketing?: AuditCategoryBreakdown;
    conversion?: AuditCategoryBreakdown;
    technology?: AuditCategoryBreakdown;
    performance?: AuditCategoryBreakdown;
    functional?: AuditCategoryBreakdown;
    seo_strategy?: AuditCategoryBreakdown;
    qa?: AuditCategoryBreakdown;
  } | null;
  summary?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  seo_report?: SEOReport | null;
  performance_report?: PerformanceReport | null;
  technical_report?: TechnicalReport | null;
}

export interface SEOReport {
  id: string;
  score?: number | null;
  title_tag?: string | null;
  meta_description?: string | null;
  h1_count?: number | null;
  h2_count?: number | null;
  canonical_url?: string | null;
  internal_links?: number | null;
  external_links?: number | null;
  broken_links?: number | null;
  has_sitemap?: boolean | null;
  has_robots_txt?: boolean | null;
  mobile_friendly?: boolean | null;
  issues?: {
    items?: { severity: string; code: string; message: string }[];
    meta?: Record<string, unknown>;
  };
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export interface PerformanceReport {
  id: string;
  score?: number | null;
  load_time_ms?: number | null;
  first_contentful_paint?: number | null;
  largest_contentful_paint?: number | null;
  cumulative_layout_shift?: number | null;
  time_to_interactive?: number | null;
  page_size_kb?: number | null;
  metrics?: Record<string, unknown>;
  issues?: {
    items?: { severity: string; code: string; message: string }[];
    meta?: Record<string, unknown>;
  };
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export interface TechnicalReport {
  id: string;
  score?: number | null;
  ssl_valid?: boolean | null;
  http_status_code?: number | null;
  server_header?: string | null;
  mobile_friendly?: boolean | null;
  indexable?: boolean | null;
  accessibility_score?: number | null;
  technologies?: {
    detected?: string[];
    cms_platform?: string | null;
    technology_stack?: string[];
  } | null;
  issues?: {
    items?: { severity: string; code: string; message: string }[];
    meta?: Record<string, unknown>;
  };
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export type ReportStatus = "pending" | "generating" | "completed" | "failed";

export interface GeneratedReport {
  id: string;
  audit_report_id: string;
  user_id?: string | null;
  title: string;
  format: string;
  status: ReportStatus;
  file_path?: string | null;
  file_size_bytes?: number | null;
  error_message?: string | null;
  generated_at: string;
  expires_at?: string | null;
  has_content?: boolean;
}

export interface ClientRecommendation {
  title: string;
  description: string;
  priority: string;
}

export interface OutreachRecommendation {
  channel: string;
  message: string;
  timing: string;
}

export interface ReportContent {
  executive_summary: string;
  seo_summary: string;
  performance_summary: string;
  technical_summary: string;
  opportunity_summary: string;
  client_recommendations: ClientRecommendation[];
  cold_calling_talking_points: string[];
  sales_pitch_summary: string;
  outreach_recommendations: OutreachRecommendation[];
  metadata?: { generated_by?: string; model?: string | null };
}

export interface ReportContentResponse {
  report_id: string;
  audit_report_id: string;
  title: string;
  status: ReportStatus;
  content: ReportContent;
  generated_at: string;
}

export interface ExportJob {
  id: string;
  export_type: string;
  format: string;
  status: string;
  record_count?: number | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DashboardStats {
  total_websites: number;
  total_audits: number;
  pending_audits: number;
  completed_audits: number;
  average_score?: number | null;
  audits_this_week: number;
  audits_this_month: number;
}

export interface AnalyticsOverview {
  stats: DashboardStats;
  score_distribution: { range_label: string; count: number }[];
  audit_trends: { date: string; count: number; average_score?: number }[];
  top_issues: Record<string, unknown>[];
}

export type DiscoverySearchStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type LeadScrapeStatus = "success" | "partial" | "failed" | "skipped";

export interface DiscoverySearch {
  id: string;
  industry_keyword: string;
  country: string;
  state?: string | null;
  city?: string | null;
  data_source_category?: string | null;
  data_source_website?: string | null;
  source_search_url?: string | null;
  status: DiscoverySearchStatus;
  total_found: number;
  total_new: number;
  total_duplicates: number;
  pages_processed?: number;
  error_message?: string | null;
  celery_task_id?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface DiscoveredLead {
  id: string;
  search_id: string;
  business_name: string;
  website_url?: string | null;
  domain?: string | null;
  business_category?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  phone_number?: string | null;
  email_address?: string | null;
  social_profiles?: Record<string, string> | null;
  source?: string | null;
  profile_url?: string | null;
  scrape_status?: LeadScrapeStatus | null;
  scrape_errors?: string[] | null;
  is_duplicate: boolean;
  imported_website_id?: string | null;
  created_at: string;
}

export type EnrichmentStatus = "pending" | "running" | "completed" | "failed";

export interface EnrichmentJob {
  id: string;
  job_type: "single_lead" | "search_bulk";
  lead_id?: string | null;
  search_id?: string | null;
  status: EnrichmentStatus;
  total_leads: number;
  processed_leads: number;
  failed_leads: number;
  error_message?: string | null;
  celery_task_id?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface BusinessEnrichment {
  id: string;
  lead_id: string;
  job_id?: string | null;
  status: EnrichmentStatus;
  company_name?: string | null;
  about_us_content?: string | null;
  services?: string[] | null;
  contact_page_data?: Record<string, unknown> | null;
  email_addresses?: string[] | null;
  phone_numbers?: string[] | null;
  team_members?: Array<{ name: string; title: string }> | null;
  business_description?: string | null;
  technology_stack?: string[] | null;
  cms_platform?: string | null;
  cms_detected?: Record<string, boolean> | null;
  pages_crawled?: string[] | null;
  error_message?: string | null;
  enriched_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EnrichmentQueuedResponse {
  job_id: string;
  status: EnrichmentStatus;
  message: string;
}

export type LeadClassification = "hot" | "warm" | "cold";

export interface LeadScore {
  id: string;
  lead_id: string;
  audit_id?: string | null;
  website_quality_score?: number | null;
  seo_opportunity_score?: number | null;
  technical_opportunity_score?: number | null;
  sales_potential_score?: number | null;
  composite_score?: number | null;
  classification: LeadClassification;
  opportunities?: Array<{
    category: string;
    code: string;
    severity: string;
    title: string;
    description: string;
  }> | null;
  opportunity_summary?: Record<string, unknown> | null;
  ranking?: number | null;
  scored_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RankedLead {
  rank?: number | null;
  score: LeadScore;
  lead: DiscoveredLead;
}

export interface ScoringDashboard {
  total_scored: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  average_composite_score?: number | null;
  top_hot_leads: RankedLead[];
}

export interface ScoringJob {
  id: string;
  job_type: string;
  status: string;
  total_leads: number;
  processed_leads: number;
  failed_leads: number;
  error_message?: string | null;
  created_at: string;
}
