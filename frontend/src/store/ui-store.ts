import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface UIState {
  theme: ThemePreference;
  _hasHydrated: boolean;
  setTheme: (theme: ThemePreference) => void;
  setHasHydrated: (value: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: "system",
      _hasHydrated: false,

      setTheme: (theme) => set({ theme }),

      setHasHydrated: (value) => set({ _hasHydrated: value }),
    }),
    {
      name: "lap-ui",
      partialize: (state) => ({ theme: state.theme }),
    },
  ),
);

export function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference === "light" || preference === "dark") return preference;
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyThemeToDocument(theme: ResolvedTheme) {
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.style.colorScheme = theme;
}

export const THEME_STORAGE_KEY = "lap-ui";
