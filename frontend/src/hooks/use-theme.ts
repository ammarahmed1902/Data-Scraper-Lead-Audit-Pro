"use client";

import { createContext, useContext } from "react";

import type { ResolvedTheme, ThemePreference } from "@/store/ui-store";

export interface ThemeContextValue {
  theme: ThemePreference;
  resolvedTheme: ResolvedTheme;
  hydrated: boolean;
  isTransitioning: boolean;
  setTheme: (theme: ThemePreference) => Promise<void>;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeActionsProvider");
  }
  return context;
}
