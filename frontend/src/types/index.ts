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

export interface AuditReport {
  id: string;
  website_id: string;
  created_by?: string | null;
  status: AuditStatus;
  overall_score?: number | null;
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
  issues?: { items?: { severity: string; code: string; message: string }[] };
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export interface PerformanceReport {
  id: string;
  score?: number | null;
  load_time_ms?: number | null;
  first_contentful_paint?: number | null;
  largest_contentful_paint?: number | null;
  cumulative_layout_shift?: number | null;
  metrics?: Record<string, unknown>;
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export interface TechnicalReport {
  id: string;
  score?: number | null;
  ssl_valid?: boolean | null;
  http_status_code?: number | null;
  issues?: { items?: { severity: string; code: string; message: string }[] };
  recommendations?: { items?: { priority: string; title: string; description: string }[] };
}

export interface GeneratedReport {
  id: string;
  audit_report_id: string;
  title: string;
  format: string;
  file_path?: string | null;
  file_size_bytes?: number | null;
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
