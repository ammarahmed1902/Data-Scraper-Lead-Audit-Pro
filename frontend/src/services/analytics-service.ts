import { apiClient } from "@/lib/api-client";
import type { AnalyticsOverview } from "@/types";

export const analyticsService = {
  overview: () => apiClient.get<AnalyticsOverview>("/analytics/overview"),
  trends: (period = "30d") => apiClient.get(`/analytics/trends?period=${period}`),
  scores: () => apiClient.get("/analytics/scores"),
  issues: (limit = 10) => apiClient.get(`/analytics/issues?limit=${limit}`),
};
