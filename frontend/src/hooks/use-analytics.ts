import { useQuery } from "@tanstack/react-query";

import { useAuthReady } from "@/hooks/use-auth-ready";
import { analyticsService } from "@/services/analytics-service";

export const analyticsKeys = {
  overview: ["analytics", "overview"] as const,
  trends: (period: string) => ["analytics", "trends", period] as const,
};

export function useAnalyticsOverview() {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: analyticsKeys.overview,
    queryFn: () => analyticsService.overview(),
    enabled: authReady,
    retry: false,
  });
}

export function useAuditTrends(period = "30d") {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: analyticsKeys.trends(period),
    queryFn: () => analyticsService.trends(period),
    enabled: authReady,
    retry: false,
  });
}
