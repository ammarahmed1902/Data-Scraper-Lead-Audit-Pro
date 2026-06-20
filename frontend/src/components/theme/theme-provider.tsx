"use client";

import { useEffect, useRef } from "react";

import { applyThemeWithTransition } from "@/lib/theme-transition";
import { resolveTheme, useUIStore } from "@/store/ui-store";
import { ThemeActionsProvider } from "@/components/theme/theme-actions-provider";

function UIStoreHydration() {
  useEffect(() => {
    const markHydrated = () => {
      useUIStore.setState({ _hasHydrated: true });
    };

    const unsub = useUIStore.persist.onFinishHydration(markHydrated);

    if (useUIStore.persist.hasHydrated()) {
      markHydrated();
    } else {
      void useUIStore.persist.rehydrate();
    }

    return unsub;
  }, []);

  return null;
}

function ThemeSync() {
  const theme = useUIStore((s) => s.theme);
  const hydrated = useUIStore((s) => s._hasHydrated);
  const isFirstRun = useRef(true);

  useEffect(() => {
    if (!hydrated) return;

    document.documentElement.dataset.themePreference = theme;

    if (isFirstRun.current) {
      isFirstRun.current = false;
      void applyThemeWithTransition(theme, { animate: false });
      return;
    }
  }, [theme, hydrated]);

  useEffect(() => {
    if (!hydrated || theme !== "system") return;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      void applyThemeWithTransition("system", { animate: true });
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [theme, hydrated]);

  return null;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <ThemeActionsProvider>
      <UIStoreHydration />
      <ThemeSync />
      {children}
    </ThemeActionsProvider>
  );
}

export { resolveTheme };
