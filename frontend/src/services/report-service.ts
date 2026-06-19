import { apiClient } from "@/lib/api-client";
import type { ExportJob, GeneratedReport, PaginatedResponse } from "@/types";

export const reportService = {
  list: (params?: { page?: number; audit_id?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.audit_id) query.set("audit_id", params.audit_id);
    const qs = query.toString();
    return apiClient.get<PaginatedResponse<GeneratedReport>>(`/reports${qs ? `?${qs}` : ""}`);
  },

  create: (auditReportId: string, title: string, format = "pdf") =>
    apiClient.post<GeneratedReport>("/reports", {
      audit_report_id: auditReportId,
      title,
      format,
    }),

  downloadUrl: (reportId: string) => `/api/reports/${reportId}/download`,

  delete: (id: string) => apiClient.delete<void>(`/reports/${id}`),
};

export const exportService = {
  list: (page = 1) =>
    apiClient.get<PaginatedResponse<ExportJob>>(`/exports?page=${page}`),

  create: (exportType: string, format: string, filters?: Record<string, unknown>) =>
    apiClient.post<ExportJob>("/exports", {
      export_type: exportType,
      format,
      filters,
    }),

  downloadUrl: (exportId: string) => `/api/exports/${exportId}/download`,
};
