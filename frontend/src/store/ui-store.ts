import { create } from "zustand";

interface UIState {
  theme: "dark" | "light";
  isMobileMenuOpen: boolean;
  activeModal: string | null;
  setTheme: (theme: "dark" | "light") => void;
  toggleMobileMenu: () => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>()((set) => ({
  theme: "dark",
  isMobileMenuOpen: false,
  activeModal: null,

  setTheme: (theme) => set({ theme }),
  toggleMobileMenu: () =>
    set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
  openModal: (modalId) => set({ activeModal: modalId }),
  closeModal: () => set({ activeModal: null }),
}));
