"use client";

import { useAuthStore } from "@/store/auth-store";

/**
 * Waits for Zustand persist to rehydrate from localStorage before reading auth state.
 * Prevents redirecting authenticated users to /auth/login during hydration.
 */
export function useAuthHydrated() {
  const hasHydrated = useAuthStore((state) => state._hasHydrated);
  const user = useAuthStore((state) => state.user);
  const tokens = useAuthStore((state) => state.tokens);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return {
    hasHydrated,
    user,
    tokens,
    isAuthenticated,
  };
}
