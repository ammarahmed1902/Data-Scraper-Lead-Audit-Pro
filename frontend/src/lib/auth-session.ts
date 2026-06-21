/**
 * Client-side session helpers: JWT expiry checks, refresh, and logout on expiry.
 */

import { clearAuthCookie } from "@/lib/auth-cookie";
import { logApi } from "@/lib/api-logger";
import { useAuthStore } from "@/store/auth-store";
import type { AuthTokens } from "@/types";

const API_BASE_URL =
  typeof window !== "undefined"
    ? "/api"
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1");

let refreshPromise: Promise<string | null> | null = null;
let sessionExpiredHandled = false;

export function resetSessionExpiredFlag(): void {
  sessionExpiredHandled = false;
}

export function getTokenExpiry(accessToken: string): number | null {
  try {
    const payload = JSON.parse(atob(accessToken.split(".")[1] ?? ""));
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

export function isAccessTokenExpired(accessToken: string, bufferSeconds = 60): boolean {
  const exp = getTokenExpiry(accessToken);
  if (exp == null) return true;
  return Date.now() / 1000 >= exp - bufferSeconds;
}

export function handleSessionExpired(): void {
  if (sessionExpiredHandled) return;
  sessionExpiredHandled = true;

  useAuthStore.getState().clearAuth();
  clearAuthCookie();

  if (
    typeof window !== "undefined" &&
    !window.location.pathname.startsWith("/auth/")
  ) {
    window.location.assign("/auth/login?session=expired");
  }
}

export async function refreshAccessToken(): Promise<string | null> {
  const { tokens, setAuth, clearAuth, user } = useAuthStore.getState();
  if (!tokens?.refresh_token) {
    return null;
  }

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

    const newTokens = (await response.json()) as Partial<AuthTokens>;
    const merged: AuthTokens = {
      access_token: newTokens.access_token ?? tokens.access_token,
      refresh_token: newTokens.refresh_token ?? tokens.refresh_token,
      token_type: newTokens.token_type ?? tokens.token_type,
    };

    if (user) {
      setAuth(user, merged);
    } else {
      useAuthStore.setState({ tokens: merged, isAuthenticated: true });
    }

    resetSessionExpiredFlag();
    logApi({ step: "refresh_ok", method: "POST", url, status: response.status });
    return merged.access_token;
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

export async function ensureAccessToken(): Promise<string | null> {
  const { tokens } = useAuthStore.getState();
  if (!tokens?.access_token) {
    return null;
  }

  if (!isAccessTokenExpired(tokens.access_token)) {
    return tokens.access_token;
  }

  if (!tokens.refresh_token) {
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

export async function refreshAccessTokenOnce(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}
