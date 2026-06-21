"use client";

import { useEffect } from "react";

import { useAuthHydrated } from "@/hooks/use-auth-hydrated";
import {
  ensureAccessToken,
  handleSessionExpired,
  isAccessTokenExpired,
} from "@/lib/auth-session";

/**
 * Proactively refreshes an expired access token after auth hydration
 * so dashboard queries do not fail with 401 on first load.
 */
export function AuthSessionRefresh() {
  const { hasHydrated, isAuthenticated, tokens } = useAuthHydrated();

  useEffect(() => {
    if (!hasHydrated || !isAuthenticated || !tokens?.access_token) return;

    if (!isAccessTokenExpired(tokens.access_token)) return;

    void (async () => {
      const accessToken = await ensureAccessToken();
      if (!accessToken) {
        handleSessionExpired();
      }
    })();
  }, [hasHydrated, isAuthenticated, tokens?.access_token, tokens?.refresh_token]);

  return null;
}
