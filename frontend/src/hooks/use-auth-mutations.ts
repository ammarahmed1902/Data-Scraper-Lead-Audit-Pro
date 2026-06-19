"use client";

import { useMutation } from "@tanstack/react-query";

import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";
import { setAuthCookie, clearAuthCookie } from "@/lib/auth-cookie";

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authService.login(email, password),
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      setAuthCookie();
    },
  });
}

export function useRegister() {
  const setAuth = useAuthStore((s) => s.setAuth);

  return useMutation({
    mutationFn: ({
      email,
      password,
      full_name,
    }: {
      email: string;
      password: string;
      full_name: string;
    }) => authService.register(email, password, full_name),
    onSuccess: (data) => {
      setAuth(data.user, data.tokens);
      setAuthCookie();
    },
  });
}

export function useLogout() {
  const { tokens, clearAuth } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      if (tokens?.access_token) {
        await authService.logout(tokens.access_token, tokens.refresh_token);
      }
    },
    onSettled: () => {
      clearAuth();
      clearAuthCookie();
    },
  });
}
