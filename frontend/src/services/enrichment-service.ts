import { apiClient } from "@/lib/api-client";
import { logApi } from "@/lib/api-logger";
import type {
  BusinessEnrichment,
  EnrichmentJob,
  EnrichmentQueuedResponse,
  PaginatedResponse,
} from "@/types";

export const enrichmentService = {
  enrichLead: (leadId: string) => {
    logApi({
      step: "enrichment_lead_start",
      method: "POST",
      url: `/enrichment/leads/${leadId}`,
    });
    return apiClient.post<EnrichmentQueuedResponse>(`/enrichment/leads/${leadId}`, {});
  },

  enrichSearch: (searchId: string) => {
    logApi({
      step: "enrichment_search_start",
      method: "POST",
      url: `/enrichment/searches/${searchId}`,
    });
    return apiClient.post<EnrichmentQueuedResponse>(
      `/enrichment/searches/${searchId}`,
      {},
    );
  },

  getJob: (jobId: string) => apiClient.get<EnrichmentJob>(`/enrichment/jobs/${jobId}`),

  getLeadEnrichment: (leadId: string) =>
    apiClient.get<BusinessEnrichment>(`/enrichment/leads/${leadId}`),

  listEnrichments: (params?: { page?: number; page_size?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.status) query.set("status", params.status);
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<BusinessEnrichment>>(
      `/enrichment/enrichments${qs ? `?${qs}` : ""}`,
    );
  },
};
