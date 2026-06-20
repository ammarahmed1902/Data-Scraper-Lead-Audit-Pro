"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { applyThemeWithTransition } from "@/lib/theme-transition";
import { ThemeContext } from "@/hooks/use-theme";
import {
  resolveTheme,
  type ResolvedTheme,
  type ThemePreference,
  useUIStore,
} from "@/store/ui-store";

export function ThemeActionsProvider({ children }: { children: ReactNode }) {
  const theme = useUIStore((s) => s.theme);
  const hydrated = useUIStore((s) => s._hasHydrated);
  const storeSetTheme = useUIStore((s) => s.setTheme);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>("dark");

  useEffect(() => {
    if (hydrated) {
      setResolvedTheme(resolveTheme(theme));
    }
  }, [hydrated, theme]);

  const setTheme = useCallback(
    async (next: ThemePreference) => {
      if (next === theme && hydrated) return;

      setIsTransitioning(true);
      storeSetTheme(next);

      try {
        const resolved = await applyThemeWithTransition(next, { animate: hydrated });
        setResolvedTheme(resolved);
      } finally {
        setIsTransitioning(false);
      }
    },
    [theme, hydrated, storeSetTheme],
  );

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme: hydrated ? resolvedTheme : resolveTheme(theme),
      hydrated,
      isTransitioning,
      setTheme,
    }),
    [theme, resolvedTheme, hydrated, isTransitioning, setTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
