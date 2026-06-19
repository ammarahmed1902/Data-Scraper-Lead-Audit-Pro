import { create } from "zustand";

interface DashboardFilters {
  dateRange: "7d" | "30d" | "90d" | "1y";
  status: string | null;
  search: string;
}

interface DashboardState {
  sidebarCollapsed: boolean;
  filters: DashboardFilters;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setFilters: (filters: Partial<DashboardFilters>) => void;
  resetFilters: () => void;
}

const defaultFilters: DashboardFilters = {
  dateRange: "30d",
  status: null,
  search: "",
};

export const useDashboardStore = create<DashboardState>()((set) => ({
  sidebarCollapsed: false,
  filters: defaultFilters,

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (collapsed) =>
    set({ sidebarCollapsed: collapsed }),

  setFilters: (filters) =>
    set((state) => ({ filters: { ...state.filters, ...filters } })),

  resetFilters: () => set({ filters: defaultFilters }),
}));
