"use client";

import { Menu, Bell, Search, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/use-auth";
import { useLogout } from "@/hooks/use-auth-mutations";
import { useDashboardStore } from "@/store/dashboard-store";

export function Header() {
  const { toggleSidebar } = useDashboardStore();
  const { user } = useAuth();
  const logout = useLogout();
  const router = useRouter();

  const initials = user?.full_name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "LA";

  function handleLogout() {
    logout.mutate(undefined, {
      onSettled: () => router.push("/auth/login"),
    });
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 px-6 backdrop-blur-glass">
      <Button variant="ghost" size="icon" onClick={toggleSidebar}>
        <Menu className="h-5 w-5" />
      </Button>

      <div className="relative max-w-md flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search websites, reports..."
          className="border-transparent bg-secondary/50 pl-9"
        />
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" onClick={handleLogout} title="Sign out">
          <LogOut className="h-5 w-5" />
        </Button>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-medium text-primary">
          {initials}
        </div>
      </div>
    </header>
  );
}
