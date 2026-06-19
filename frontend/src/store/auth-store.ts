import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthTokens, User } from "@/types";

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  /** Set after Zustand persist finishes reading localStorage (client-only). */
  _hasHydrated: boolean;
  setAuth: (user: User, tokens: AuthTokens) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
  setHasHydrated: (value: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      _hasHydrated: false,

      setAuth: (user, tokens) =>
        set({ user, tokens, isAuthenticated: true }),

      clearAuth: () =>
        set({ user: null, tokens: null, isAuthenticated: false }),

      setUser: (user) => set({ user }),

      setHasHydrated: (value) => set({ _hasHydrated: value }),
    }),
    {
      name: "lap-auth",
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => () => {
        useAuthStore.setState({ _hasHydrated: true });
      },
    },
  ),
);
