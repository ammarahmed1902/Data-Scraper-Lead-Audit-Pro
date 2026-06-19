"use client";

import { useAuthStore } from "@/store/auth-store";

export function useAuth() {
  const { user, tokens, isAuthenticated, setAuth, clearAuth, setUser } =
    useAuthStore();

  return {
    user,
    tokens,
    isAuthenticated,
    accessToken: tokens?.access_token ?? null,
    setAuth,
    clearAuth,
    setUser,
  };
}
