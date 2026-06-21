import { apiClient } from "@/lib/api-client";
import { logApi } from "@/lib/api-logger";
import type { AuditListItem, AuditReport, PaginatedResponse } from "@/types";

export const auditService = {
  list: (params?: { page?: number; page_size?: number; website_id?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    if (params?.website_id) query.set("website_id", params.website_id);
    if (params?.status) query.set("status", params.status);
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<AuditListItem>>(`/audits${qs ? `?${qs}` : ""}`);
  },

  get: (id: string) => apiClient.get<AuditReport>(`/audits/${id}`),

  create: (websiteId: string) => {
    logApi({
      step: "audit_create_start",
      method: "POST",
      url: "/audits",
      detail: { website_id: websiteId },
    });
    return apiClient.post<AuditReport>("/audits", { website_id: websiteId });
  },

  createForLead: (leadId: string, autoImport = true) =>
    apiClient.post<AuditReport>(`/audits/leads/${leadId}`, { auto_import: autoImport }),

  bulkCreate: (websiteIds: string[]) =>
    apiClient.post<{ queued: number; audit_ids: string[] }>("/audits/bulk", {
      website_ids: websiteIds,
    }),

  getStatus: (id: string) =>
    apiClient.get<{
      id: string;
      status: string;
      overall_score?: number;
      error_message?: string;
    }>(`/audits/${id}/status`),

  cancel: (id: string) => apiClient.delete<void>(`/audits/${id}`),
};
