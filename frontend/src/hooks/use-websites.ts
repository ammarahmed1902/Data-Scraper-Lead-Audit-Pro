import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { websiteService } from "@/services/website-service";
import type { Website, WebsiteStatus } from "@/types";

export const websiteKeys = {
  all: ["websites"] as const,
  list: (params: Record<string, unknown>) => ["websites", "list", params] as const,
  detail: (id: string) => ["websites", "detail", id] as const,
};

export interface WebsiteListParams {
  page?: number;
  page_size?: number;
  status?: WebsiteStatus | "";
  search?: string;
}

export function useWebsites(params: WebsiteListParams = {}) {
  const queryParams = {
    page: params.page ?? 1,
    page_size: params.page_size ?? 20,
    status: params.status || undefined,
    search: params.search || undefined,
  };

  return useQuery({
    queryKey: websiteKeys.list(queryParams),
    queryFn: () => websiteService.list(queryParams),
  });
}

export function useWebsite(id: string, enabled = true) {
  return useQuery({
    queryKey: websiteKeys.detail(id),
    queryFn: () => websiteService.get(id),
    enabled: enabled && !!id,
  });
}

export function useCreateWebsite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Website>) => websiteService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: websiteKeys.all }),
  });
}

export function useUpdateWebsite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Website> }) =>
      websiteService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: websiteKeys.all }),
  });
}

export function useDeleteWebsite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => websiteService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: websiteKeys.all }),
  });
}

export function useBulkImportWebsites() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (websites: Partial<Website>[]) => websiteService.bulkImport(websites),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: websiteKeys.all }),
  });
}
