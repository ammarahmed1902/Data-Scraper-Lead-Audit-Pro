import { apiClient } from "@/lib/api-client";
import { logApi } from "@/lib/api-logger";
import type { AuthResponse } from "@/types";

export const authService = {
  login: async (email: string, password: string) => {
    logApi({ step: "auth_login_start", method: "POST", url: "/api/auth/login" });
    const result = await apiClient.post<AuthResponse>("/auth/login", {
      email,
      password,
    });
    logApi({ step: "auth_login_success", method: "POST", url: "/api/auth/login" });
    return result;
  },

  register: async (email: string, password: string, full_name: string) => {
    logApi({ step: "auth_register_start", method: "POST", url: "/api/auth/register" });
    return apiClient.post<AuthResponse>("/auth/register", {
      email,
      password,
      full_name,
    });
  },

  refresh: (refresh_token: string) =>
    apiClient.post<{ access_token: string; refresh_token: string }>(
      "/auth/refresh",
      { refresh_token },
    ),

  logout: (token: string, refresh_token?: string) =>
    apiClient.post<void>(
      "/auth/logout",
      refresh_token ? { refresh_token } : undefined,
      token,
    ),

  me: (token: string) => apiClient.get("/auth/me", token),
};
