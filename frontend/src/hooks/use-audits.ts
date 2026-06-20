import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { auditService } from "@/services/audit-service";

export const auditKeys = {
  all: ["audits"] as const,
  list: (params: Record<string, unknown>) => ["audits", "list", params] as const,
  detail: (id: string) => ["audits", "detail", id] as const,
  status: (id: string) => ["audits", "status", id] as const,
};

export function useAudits(params: { page?: number; page_size?: number; website_id?: string } = {}) {
  return useQuery({
    queryKey: auditKeys.list(params),
    queryFn: () => auditService.list(params),
  });
}

export function useAudit(id: string, enabled = true) {
  return useQuery({
    queryKey: auditKeys.detail(id),
    queryFn: () => auditService.get(id),
    enabled: enabled && !!id,
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "pending"
        ? 3000
        : false,
  });
}

export function useCreateAudit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (websiteId: string) => auditService.create(websiteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.all });
      queryClient.invalidateQueries({ queryKey: ["websites"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });
}

export function useCreateAuditForLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, autoImport }: { leadId: string; autoImport?: boolean }) =>
      auditService.createForLead(leadId, autoImport ?? true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.all });
      queryClient.invalidateQueries({ queryKey: ["websites"] });
      queryClient.invalidateQueries({ queryKey: ["discovery"] });
    },
  });
}

export function useBulkCreateAudits() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (websiteIds: string[]) => auditService.bulkCreate(websiteIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.all });
      queryClient.invalidateQueries({ queryKey: ["websites"] });
    },
  });
}
