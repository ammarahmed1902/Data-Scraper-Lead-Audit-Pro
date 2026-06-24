"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuthHydrated } from "@/hooks/use-auth-hydrated";
import { setAuthCookie } from "@/lib/auth-cookie";
import { AuthSessionRefresh } from "@/components/auth/auth-session-refresh";

function AuthLoadingSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
    </div>
  );
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { hasHydrated, isAuthenticated } = useAuthHydrated();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!hasHydrated) return;

    if (isAuthenticated) {
      setAuthCookie();
      return;
    }

    const redirect = encodeURIComponent(pathname || "/dashboard");
    router.replace(`/auth/login?redirect=${redirect}`);
  }, [hasHydrated, isAuthenticated, router, pathname]);

  if (!hasHydrated || !isAuthenticated) {
    return <AuthLoadingSpinner />;
  }

  return (
    <>
      <AuthSessionRefresh />
      {children}
    </>
  );
}
