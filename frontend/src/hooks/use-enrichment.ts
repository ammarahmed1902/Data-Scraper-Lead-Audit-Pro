import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { enrichmentService } from "@/services/enrichment-service";

export const enrichmentKeys = {
  all: ["enrichment"] as const,
  job: (id: string) => ["enrichment", "job", id] as const,
  lead: (leadId: string) => ["enrichment", "lead", leadId] as const,
  list: (params: Record<string, unknown>) => ["enrichment", "list", params] as const,
};

export function useEnrichmentJob(jobId: string | null, poll = false) {
  return useQuery({
    queryKey: enrichmentKeys.job(jobId ?? ""),
    queryFn: () => enrichmentService.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      if (!poll) return false;
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    },
  });
}

export function useLeadEnrichment(leadId: string | null, enabled = true) {
  return useQuery({
    queryKey: enrichmentKeys.lead(leadId ?? ""),
    queryFn: () => enrichmentService.getLeadEnrichment(leadId!),
    enabled: !!leadId && enabled,
    retry: false,
  });
}

export function useEnrichLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) => enrichmentService.enrichLead(leadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: enrichmentKeys.all });
    },
  });
}

export function useEnrichSearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (searchId: string) => enrichmentService.enrichSearch(searchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: enrichmentKeys.all });
    },
  });
}

export function useEnrichmentsList(page = 1, status?: string) {
  return useQuery({
    queryKey: enrichmentKeys.list({ page, status }),
    queryFn: () => enrichmentService.listEnrichments({ page, page_size: 50, status }),
  });
}
