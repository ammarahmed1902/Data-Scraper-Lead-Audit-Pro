"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuthHydrated } from "@/hooks/use-auth-hydrated";
import { setAuthCookie } from "@/lib/auth-cookie";

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

  useEffect(() => {
    if (!hasHydrated) return;

    if (isAuthenticated) {
      setAuthCookie();
      return;
    }

    router.replace("/auth/login");
  }, [hasHydrated, isAuthenticated, router]);

  if (!hasHydrated || !isAuthenticated) {
    return <AuthLoadingSpinner />;
  }

  return <>{children}</>;
}
