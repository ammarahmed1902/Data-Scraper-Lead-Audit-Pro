import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  discoveryService,
  type DiscoverySearchCreate,
} from "@/services/discovery-service";

export const discoveryKeys = {
  all: ["discovery"] as const,
  searches: (params: Record<string, unknown>) => ["discovery", "searches", params] as const,
  search: (id: string) => ["discovery", "search", id] as const,
  leads: (searchId: string, params: Record<string, unknown>) =>
    ["discovery", "leads", searchId, params] as const,
};

export function useDiscoverySearches(page = 1, pageSize = 10) {
  return useQuery({
    queryKey: discoveryKeys.searches({ page, page_size: pageSize }),
    queryFn: () => discoveryService.listSearches({ page, page_size: pageSize }),
  });
}

export function useDiscoverySearch(id: string | null, poll = false) {
  return useQuery({
    queryKey: discoveryKeys.search(id ?? ""),
    queryFn: () => discoveryService.getSearch(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      if (!poll) return false;
      const status = query.state.data?.status;
      return status === "pending" || status === "running" ? 3000 : false;
    },
  });
}

export function useDiscoveredLeads(
  searchId: string | null,
  page = 1,
  includeDuplicates = false,
) {
  return useQuery({
    queryKey: discoveryKeys.leads(searchId ?? "", { page, include_duplicates: includeDuplicates }),
    queryFn: () =>
      discoveryService.listLeads(searchId!, {
        page,
        page_size: 20,
        include_duplicates: includeDuplicates,
      }),
    enabled: !!searchId,
  });
}

export function useCreateDiscoverySearch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DiscoverySearchCreate) => discoveryService.createSearch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: discoveryKeys.all });
    },
  });
}

export function useImportDiscoveredLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) => discoveryService.importLead(leadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: discoveryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["websites"] });
    },
  });
}
