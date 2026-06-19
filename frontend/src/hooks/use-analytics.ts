import { useQuery } from "@tanstack/react-query";

import { analyticsService } from "@/services/analytics-service";

export const analyticsKeys = {
  overview: ["analytics", "overview"] as const,
  trends: (period: string) => ["analytics", "trends", period] as const,
};

export function useAnalyticsOverview() {
  return useQuery({
    queryKey: analyticsKeys.overview,
    queryFn: () => analyticsService.overview(),
  });
}

export function useAuditTrends(period = "30d") {
  return useQuery({
    queryKey: analyticsKeys.trends(period),
    queryFn: () => analyticsService.trends(period),
  });
}
