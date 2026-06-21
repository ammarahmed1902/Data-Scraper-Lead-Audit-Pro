"use client";

import { useEffect, useState } from "react";

import { useAuthHydrated } from "@/hooks/use-auth-hydrated";
import {
  ensureAccessToken,
  handleSessionExpired,
  isAccessTokenExpired,
} from "@/lib/auth-session";

/**
 * True once persisted auth is loaded and a usable access token is available.
 * Refreshes expired tokens before enabling authenticated API queries.
 */
export function useAuthReady(): boolean {
  const { hasHydrated, isAuthenticated, tokens } = useAuthHydrated();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!hasHydrated || !isAuthenticated || !tokens?.access_token) {
      setReady(false);
      return;
    }

    if (!isAccessTokenExpired(tokens.access_token)) {
      setReady(true);
      return;
    }

    let cancelled = false;
    setReady(false);

    void (async () => {
      const accessToken = await ensureAccessToken();
      if (cancelled) return;
      if (accessToken) {
        setReady(true);
        return;
      }
      handleSessionExpired();
    })();

    return () => {
      cancelled = true;
    };
  }, [hasHydrated, isAuthenticated, tokens?.access_token, tokens?.refresh_token]);

  return ready;
}
