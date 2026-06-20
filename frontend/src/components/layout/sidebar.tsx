"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  FileSearch,
  FileText,
  Flame,
  Globe,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  Zap,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useSidebarExpanded, useDashboardStore } from "@/store/dashboard-store";
import { useIsMobile } from "@/hooks/use-media-query";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/discovery", label: "Lead Discovery", icon: Search },
  { href: "/websites", label: "Websites", icon: Globe },
  { href: "/audits", label: "Audits", icon: FileSearch },
  { href: "/leads", label: "Lead Priority", icon: Flame },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

function SidebarNavItem({
  href,
  label,
  icon: Icon,
  isActive,
  isExpanded,
}: {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  isActive: boolean;
  isExpanded: boolean;
}) {
  const link = (
    <Link
      href={href}
      prefetch
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
        "transition-[background-color,color,transform] duration-200 ease-out",
        isExpanded ? "" : "justify-center px-2",
        isActive
          ? "bg-primary/10 text-primary shadow-sm"
          : "text-muted-foreground hover:bg-accent/80 hover:text-foreground",
      )}
    >
      {isActive && (
        <span
          className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-primary transition-opacity duration-200"
          aria-hidden
        />
      )}
      <Icon
        className={cn(
          "h-[18px] w-[18px] shrink-0 transition-transform duration-200 ease-out group-hover:scale-105",
          isActive && "text-primary",
        )}
      />
      <span
        className={cn(
          "truncate transition-all duration-300 ease-out",
          isExpanded ? "w-auto opacity-100" : "w-0 overflow-hidden opacity-0",
        )}
      >
        {label}
      </span>
    </Link>
  );

  if (!isExpanded) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          {label}
        </TooltipContent>
      </Tooltip>
    );
  }

  return link;
}

export function Sidebar() {
  const pathname = usePathname();
  const isExpanded = useSidebarExpanded();
  const sidebarMobileOpen = useDashboardStore((s) => s.sidebarMobileOpen);
  const toggleSidebar = useDashboardStore((s) => s.toggleSidebar);
  const isMobile = useIsMobile();

  const isDesktopVisible = !isMobile;
  const isMobileVisible = isMobile && sidebarMobileOpen;

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        id="app-sidebar"
        aria-label="Main navigation"
        data-expanded={isExpanded ? "true" : "false"}
        data-mobile-open={sidebarMobileOpen ? "true" : "false"}
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-card/95 backdrop-blur-glass",
          "transition-[width,transform] duration-300 ease-in-out motion-reduce:transition-none",
          isMobile
            ? cn(
                "w-64 shadow-elevated",
                isMobileVisible ? "translate-x-0" : "-translate-x-full pointer-events-none",
              )
            : cn(
                "translate-x-0",
                isExpanded ? "w-64" : "w-[4.5rem]",
              ),
          (isDesktopVisible || isMobileVisible) && "pointer-events-auto",
        )}
        style={
          !isMobile
            ? { width: isExpanded ? "var(--sidebar-width, 16rem)" : "4.5rem" }
            : undefined
        }
      >
        <div
          className={cn(
            "flex h-16 shrink-0 items-center border-b border-border transition-[padding] duration-300 ease-in-out",
            isExpanded ? "justify-between px-4" : "justify-center px-2",
          )}
        >
          <Link
            href="/dashboard"
            className="flex min-w-0 items-center gap-2.5 outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md"
          >
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <span
              className={cn(
                "truncate text-base font-semibold tracking-tight transition-all duration-300 ease-in-out",
                isExpanded ? "w-auto opacity-100" : "w-0 overflow-hidden opacity-0",
              )}
            >
              Lead Audit <span className="text-primary">Pro</span>
            </span>
          </Link>
          {isExpanded && !isMobile && (
            <button
              type="button"
              onClick={toggleSidebar}
              className="rounded-md p-1.5 text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
              aria-label="Collapse sidebar"
              aria-expanded
            >
              <PanelLeftClose className="h-4 w-4" />
            </button>
          )}
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto overflow-x-hidden p-3">
          {navItems.map((item) => (
            <SidebarNavItem
              key={item.href}
              href={item.href}
              label={item.label}
              icon={item.icon}
              isActive={pathname === item.href || pathname.startsWith(`${item.href}/`)}
              isExpanded={isExpanded}
            />
          ))}
        </nav>

        {!isMobile && !isExpanded && (
          <div className="border-t border-border p-3">
            <button
              type="button"
              onClick={toggleSidebar}
              className="flex w-full items-center justify-center rounded-lg p-2.5 text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
              aria-label="Expand sidebar"
              aria-expanded={false}
            >
              <PanelLeftOpen className="h-4 w-4" />
            </button>
          </div>
        )}
      </aside>
    </TooltipProvider>
  );
}
