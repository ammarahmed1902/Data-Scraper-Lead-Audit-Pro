/**
 * Centralized HTTP client with automatic token refresh on 401.
 */

import { logApi } from "@/lib/api-logger";
import { formatApiError } from "@/lib/format-api-error";
import { useAuthStore } from "@/store/auth-store";
import { clearAuthCookie } from "@/lib/auth-cookie";

const API_BASE_URL =
  typeof window !== "undefined"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1");

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  token?: string | null;
  skipRefresh?: boolean;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const { tokens, setAuth, clearAuth, user } = useAuthStore.getState();
  if (!tokens?.refresh_token) return null;

  const url = `${API_BASE_URL}/auth/refresh`;
  logApi({ step: "refresh_start", method: "POST", url });

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    });

    if (!response.ok) {
      logApi({ step: "refresh_failed", method: "POST", url, status: response.status });
      clearAuth();
      clearAuthCookie();
      return null;
    }

    const newTokens = await response.json();
    if (user) {
      setAuth(user, { ...tokens, ...newTokens });
    }
    logApi({ step: "refresh_ok", method: "POST", url, status: response.status });
    return newTokens.access_token;
  } catch (error) {
    logApi({
      step: "refresh_network_error",
      method: "POST",
      url,
      error: error instanceof Error ? error.message : String(error),
    });
    clearAuth();
    clearAuthCookie();
    return null;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, token, skipRefresh, headers: customHeaders, ...rest } = options;
  const method = (rest.method ?? "GET").toUpperCase();
  const url = `${API_BASE_URL}${endpoint}`;
  const started = performance.now();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  const accessToken =
    token ?? useAuthStore.getState().tokens?.access_token ?? null;

  if (accessToken) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${accessToken}`;
  }

  logApi({
    step: "fetch_start",
    method,
    url,
    detail: body ? { hasBody: true } : undefined,
  });

  let response: Response;
  try {
    response = await fetch(url, {
      ...rest,
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      credentials: "same-origin",
    });
  } catch (error) {
    const durationMs = Math.round(performance.now() - started);
    const rawMessage = error instanceof Error ? error.message : String(error);
    const isFailedFetch = rawMessage === "Failed to fetch";

    logApi({
      step: "fetch_network_error",
      method,
      url,
      durationMs,
      error: rawMessage,
      detail: {
        hint: isFailedFetch
          ? "No HTTP response received. Common causes: Next.js dev server not running, wrong port (use 3002), or browser extension blocking fetch."
          : undefined,
      },
    });

    if (isFailedFetch) {
      throw new ApiError(
        0,
        "Cannot reach the API. Confirm Next.js is running (npm run dev → http://localhost:3002) and the backend is on port 8000. Try disabling browser extensions if this persists.",
      );
    }
    throw new ApiError(0, rawMessage);
  }

  const durationMs = Math.round(performance.now() - started);
  logApi({
    step: "fetch_response",
    method,
    url,
    status: response.status,
    durationMs,
  });

  if (response.status === 401 && !skipRefresh && accessToken) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }
    const newToken = await refreshPromise;
    if (newToken) {
      return request<T>(endpoint, { ...options, token: newToken, skipRefresh: true });
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const message = formatApiError(response.status, error);

    logApi({
      step: "fetch_error_response",
      method,
      url,
      status: response.status,
      durationMs,
      error: message,
      detail: error,
    });

    throw new ApiError(response.status, message, error);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data = await response.json();
  logApi({ step: "fetch_ok", method, url, status: response.status, durationMs });
  return data;
}

export const apiClient = {
  get: <T>(endpoint: string, token?: string | null) =>
    request<T>(endpoint, { method: "GET", token }),

  post: <T>(endpoint: string, body?: unknown, token?: string | null) =>
    request<T>(endpoint, { method: "POST", body, token }),

  put: <T>(endpoint: string, body?: unknown, token?: string | null) =>
    request<T>(endpoint, { method: "PUT", body, token }),

  delete: <T>(endpoint: string, token?: string | null) =>
    request<T>(endpoint, { method: "DELETE", token }),
};
