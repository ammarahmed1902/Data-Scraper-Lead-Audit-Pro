import { create } from "zustand";
import { persist } from "zustand/middleware";

import {
  SIDEBAR_WIDTH_COLLAPSED,
  SIDEBAR_WIDTH_EXPANDED,
} from "@/lib/sidebar-script";

interface DashboardFilters {
  dateRange: "7d" | "30d" | "90d" | "1y";
  status: string | null;
  search: string;
}

interface DashboardState {
  /** When false, desktop sidebar shows icon-only mode. Never changed by navigation. */
  sidebarCollapsed: boolean;
  /** Mobile overlay drawer open state. Never changed by navigation. */
  sidebarMobileOpen: boolean;
  filters: DashboardFilters;
  _hasHydrated: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setSidebarMobileOpen: (open: boolean) => void;
  toggleSidebarMobile: () => void;
  setFilters: (filters: Partial<DashboardFilters>) => void;
  resetFilters: () => void;
  setHasHydrated: (value: boolean) => void;
}

const defaultFilters: DashboardFilters = {
  dateRange: "30d",
  status: null,
  search: "",
};

function applySidebarWidth(collapsed: boolean) {
  if (typeof document === "undefined") return;
  document.documentElement.style.setProperty(
    "--sidebar-width",
    collapsed ? SIDEBAR_WIDTH_COLLAPSED : SIDEBAR_WIDTH_EXPANDED,
  );
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      sidebarMobileOpen: false,
      filters: defaultFilters,
      _hasHydrated: false,

      toggleSidebar: () =>
        set((state) => {
          const collapsed = !state.sidebarCollapsed;
          applySidebarWidth(collapsed);
          return { sidebarCollapsed: collapsed };
        }),

      setSidebarCollapsed: (collapsed) => {
        applySidebarWidth(collapsed);
        set({ sidebarCollapsed: collapsed });
      },

      setSidebarMobileOpen: (open) => set({ sidebarMobileOpen: open }),

      toggleSidebarMobile: () =>
        set((state) => ({ sidebarMobileOpen: !state.sidebarMobileOpen })),

      setFilters: (filters) =>
        set((state) => ({ filters: { ...state.filters, ...filters } })),

      resetFilters: () => set({ filters: defaultFilters }),

      setHasHydrated: (value) => set({ _hasHydrated: value }),
    }),
    {
      name: "lap-dashboard",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        sidebarMobileOpen: state.sidebarMobileOpen,
        filters: state.filters,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          applySidebarWidth(state.sidebarCollapsed);
        }
      },
    },
  ),
);

/** Desktop sidebar is expanded (full width with labels). */
export function useSidebarExpanded(): boolean {
  const collapsed = useDashboardStore((s) => s.sidebarCollapsed);
  const hydrated = useDashboardStore((s) => s._hasHydrated);
  if (!hydrated) return true;
  return !collapsed;
}
