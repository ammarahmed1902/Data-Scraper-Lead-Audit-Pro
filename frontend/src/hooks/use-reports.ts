import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { reportService } from "@/services/report-service";

export const reportKeys = {
  all: ["reports"] as const,
  list: (params?: Record<string, unknown>) => ["reports", "list", params] as const,
  detail: (id: string) => ["reports", "detail", id] as const,
  content: (id: string) => ["reports", "content", id] as const,
};

export function useReports(
  params?: { page?: number; audit_id?: string },
  enabled = true,
) {
  return useQuery({
    queryKey: reportKeys.list(params),
    queryFn: () => reportService.list(params),
    enabled,
  });
}

export function useReport(id: string, enabled = true) {
  return useQuery({
    queryKey: reportKeys.detail(id),
    queryFn: () => reportService.get(id),
    enabled: enabled && !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "generating" ? 3000 : false;
    },
  });
}

export function useReportContent(id: string, enabled = true) {
  return useQuery({
    queryKey: reportKeys.content(id),
    queryFn: () => reportService.getContent(id),
    enabled: enabled && !!id,
    retry: (count, error) => {
      if (error instanceof Error && error.message.includes("404")) return false;
      return count < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "generating" ? 3000 : false;
    },
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (auditId: string) => reportService.createForAudit(auditId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: reportKeys.all });
    },
  });
}
