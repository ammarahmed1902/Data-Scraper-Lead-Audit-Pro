import { apiClient } from "@/lib/api-client";
import { logApi } from "@/lib/api-logger";
import type { DiscoveredLead, DiscoverySearch, PaginatedResponse } from "@/types";

export interface DiscoverySearchCreate {
  industry_keyword: string;
  country: string;
  state?: string;
  city?: string;
  data_source_category: string;
  data_source_website: string;
}

export const discoveryService = {
  createSearch: (data: DiscoverySearchCreate) => {
    logApi({ step: "discovery_search_start", method: "POST", url: "/discovery/searches", detail: data });
    return apiClient.post<DiscoverySearch>("/discovery/searches", data);
  },

  listSearches: (params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<DiscoverySearch>>(
      `/discovery/searches${qs ? `?${qs}` : ""}`,
    );
  },

  getSearch: (id: string) => apiClient.get<DiscoverySearch>(`/discovery/searches/${id}`),

  listLeads: (
    searchId: string,
    params?: { page?: number; page_size?: number; include_duplicates?: boolean },
  ) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.include_duplicates) query.set("include_duplicates", "true");
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<DiscoveredLead>>(
      `/discovery/searches/${searchId}/leads${qs ? `?${qs}` : ""}`,
    );
  },

  importLead: (leadId: string) =>
    apiClient.post<{ lead_id: string; website_id: string; message: string }>(
      `/discovery/leads/${leadId}/import`,
      {},
    ),
};
