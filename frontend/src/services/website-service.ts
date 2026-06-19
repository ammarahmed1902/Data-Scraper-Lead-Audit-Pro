import { apiClient } from "@/lib/api-client";
import type { PaginatedResponse, Website } from "@/types";

export interface WebsiteBulkResult {
  created: number;
  skipped: number;
  errors: { index: string; url: string; error: string }[];
}

export interface WebsiteListItem {
  id: string;
  url: string;
  domain: string;
  company_name?: string | null;
  status: Website["status"];
  last_audited_at?: string | null;
  created_at: string;
}

export const websiteService = {
  list: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.status) query.set("status", params.status);
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<WebsiteListItem>>(
      `/websites${qs ? `?${qs}` : ""}`,
    );
  },

  get: (id: string) => apiClient.get<Website>(`/websites/${id}`),

  create: (data: Partial<Website>) =>
    apiClient.post<Website>("/websites", data),

  update: (id: string, data: Partial<Website>) =>
    apiClient.put<Website>(`/websites/${id}`, data),

  delete: (id: string) => apiClient.delete<void>(`/websites/${id}`),

  bulkImport: (websites: Partial<Website>[]) =>
    apiClient.post<WebsiteBulkResult>("/websites/bulk", { websites }),
};
