"use client";

import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { DashboardStoreHydration } from "./dashboard-store-hydration";
import { useSidebarExpanded, useDashboardStore } from "@/store/dashboard-store";
import { useIsMobile } from "@/hooks/use-media-query";
import { cn } from "@/lib/utils";

interface DashboardShellProps {
  children: React.ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  const isExpanded = useSidebarExpanded();
  const sidebarMobileOpen = useDashboardStore((s) => s.sidebarMobileOpen);
  const setSidebarMobileOpen = useDashboardStore((s) => s.setSidebarMobileOpen);
  const isMobile = useIsMobile();

  return (
    <div className="min-h-screen bg-background">
      <DashboardStoreHydration />
      <Sidebar />

      {isMobile && sidebarMobileOpen && (
        <button
          type="button"
          aria-label="Close sidebar overlay"
          className="fixed inset-0 z-30 bg-background/60 backdrop-blur-sm transition-opacity duration-300 ease-out lg:hidden motion-reduce:transition-none"
          onClick={() => setSidebarMobileOpen(false)}
        />
      )}

      <div
        className={cn(
          "flex min-h-screen flex-col transition-[padding-left] duration-300 ease-in-out motion-reduce:transition-none",
          !isMobile && (isExpanded ? "lg:pl-64" : "lg:pl-[4.5rem]"),
        )}
        style={
          !isMobile
            ? { paddingLeft: isExpanded ? "var(--sidebar-width, 16rem)" : "4.5rem" }
            : undefined
        }
      >
        <Header />
        <main className="flex-1 p-4 sm:p-6 animate-fade-in">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
