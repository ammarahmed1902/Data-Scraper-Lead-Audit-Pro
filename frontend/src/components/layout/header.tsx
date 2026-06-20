"use client";

import { Bell, LogOut, Menu, Search } from "lucide-react";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { useLogout } from "@/hooks/use-auth-mutations";
import { useIsMobile } from "@/hooks/use-media-query";
import { useSidebarExpanded, useDashboardStore } from "@/store/dashboard-store";

export function Header() {
  const isExpanded = useSidebarExpanded();
  const toggleSidebar = useDashboardStore((s) => s.toggleSidebar);
  const toggleSidebarMobile = useDashboardStore((s) => s.toggleSidebarMobile);
  const sidebarMobileOpen = useDashboardStore((s) => s.sidebarMobileOpen);
  const { user } = useAuth();
  const logout = useLogout();
  const router = useRouter();
  const isMobile = useIsMobile();

  const initials =
    user?.full_name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase() ?? "LA";

  function handleMenuToggle() {
    if (isMobile) {
      toggleSidebarMobile();
    } else {
      toggleSidebar();
    }
  }

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => router.push("/auth/login"),
    });
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-border/80 bg-background/80 px-4 backdrop-blur-glass sm:gap-4 sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={handleMenuToggle}
        aria-label={isMobile ? "Toggle navigation menu" : "Toggle sidebar"}
        aria-expanded={isMobile ? sidebarMobileOpen : isExpanded}
        className="shrink-0"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="relative hidden min-w-0 flex-1 sm:block sm:max-w-md lg:max-w-lg">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search websites, leads, reports..."
          className="h-9 border-transparent bg-secondary/50 pl-9 transition-all duration-200 focus-visible:border-input focus-visible:bg-background focus-visible:shadow-sm"
        />
      </div>

      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <ThemeToggle />
        <Button variant="ghost" size="icon" className="hidden sm:inline-flex">
          <Bell className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleLogout}
          title="Sign out"
          className="hidden sm:inline-flex"
        >
          <LogOut className="h-5 w-5" />
        </Button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary ring-1 ring-primary/20">
          {initials}
        </div>
      </div>
    </header>
  );
}
