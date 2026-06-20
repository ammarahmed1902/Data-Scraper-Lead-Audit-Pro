import { apiClient } from "@/lib/api-client";
import type {
  LeadScore,
  PaginatedResponse,
  RankedLead,
  ScoringDashboard,
  ScoringJob,
} from "@/types";

export const scoringService = {
  getDashboard: () => apiClient.get<ScoringDashboard>("/scoring/dashboard"),

  listRankedLeads: (params?: {
    page?: number;
    page_size?: number;
    classification?: string;
    search_id?: string;
    min_composite?: number;
    opportunity?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.classification) query.set("classification", params.classification);
    if (params?.search_id) query.set("search_id", params.search_id);
    if (params?.min_composite != null) query.set("min_composite", String(params.min_composite));
    if (params?.opportunity) query.set("opportunity", params.opportunity);
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<RankedLead>>(
      `/scoring/leads${qs ? `?${qs}` : ""}`,
    );
  },

  scoreLead: (leadId: string) =>
    apiClient.post<{ job_id: string; status: string }>(`/scoring/leads/${leadId}`, {}),

  scoreSearch: (searchId: string) =>
    apiClient.post<{ job_id: string; status: string }>(
      `/scoring/searches/${searchId}`,
      {},
    ),

  getJob: (jobId: string) => apiClient.get<ScoringJob>(`/scoring/jobs/${jobId}`),

  getLeadScore: (leadId: string) =>
    apiClient.get<LeadScore>(`/scoring/leads/${leadId}`),

  getOpportunityReport: (leadId: string) =>
    apiClient.get<{
      lead_id: string;
      business_name: string;
      classification: string;
      composite_score?: number;
      opportunities: Array<{
        category: string;
        code: string;
        severity: string;
        title: string;
        description: string;
      }>;
      opportunity_summary?: Record<string, unknown>;
    }>(`/scoring/leads/${leadId}/opportunities`),
};
