import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { scoringService } from "@/services/scoring-service";

export const scoringKeys = {
  all: ["scoring"] as const,
  dashboard: () => ["scoring", "dashboard"] as const,
  ranked: (params: Record<string, unknown>) => ["scoring", "ranked", params] as const,
  lead: (leadId: string) => ["scoring", "lead", leadId] as const,
  job: (jobId: string) => ["scoring", "job", jobId] as const,
};

export function useScoringDashboard() {
  return useQuery({
    queryKey: scoringKeys.dashboard(),
    queryFn: () => scoringService.getDashboard(),
  });
}

export function useRankedLeads(params: {
  page?: number;
  classification?: string;
  search_id?: string;
  min_composite?: number;
  opportunity?: string;
  enabled?: boolean;
} = {}) {
  const { enabled = true, page, ...queryParams } = params;
  return useQuery({
    queryKey: scoringKeys.ranked(params),
    queryFn: () =>
      scoringService.listRankedLeads({ page: page ?? 1, ...queryParams }),
    enabled,
    retry: false,
  });
}

export function useLeadScore(leadId: string | null) {
  return useQuery({
    queryKey: scoringKeys.lead(leadId ?? ""),
    queryFn: () => scoringService.getLeadScore(leadId!),
    enabled: !!leadId,
    retry: false,
  });
}

export function useScoreLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) => scoringService.scoreLead(leadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.all });
    },
  });
}

export function useScoreSearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (searchId: string) => scoringService.scoreSearch(searchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.all });
    },
  });
}

export function useOpportunityReport(leadId: string | null) {
  return useQuery({
    queryKey: ["scoring", "opportunities", leadId],
    queryFn: () => scoringService.getOpportunityReport(leadId!),
    enabled: !!leadId,
    retry: false,
  });
}
