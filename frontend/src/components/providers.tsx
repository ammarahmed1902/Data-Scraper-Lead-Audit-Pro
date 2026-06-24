"use client";

import { useEffect } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { ThemeProvider } from "@/components/theme/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import { getQueryClient } from "@/lib/query-client";
import { useAuthStore } from "@/store/auth-store";

interface ProvidersProps {
  children: React.ReactNode;
}

function AuthStoreHydration() {
  useEffect(() => {
    const markHydrated = () => {
      useAuthStore.setState({ _hasHydrated: true });
    };

    const unsub = useAuthStore.persist.onFinishHydration(markHydrated);

    if (useAuthStore.persist.hasHydrated()) {
      markHydrated();
    } else {
      void useAuthStore.persist.rehydrate();
    }

    return unsub;
  }, []);

  return null;
}

export function Providers({ children }: ProvidersProps) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthStoreHydration />
        {children}
        <Toaster />
        {process.env.NODE_ENV === "development" && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
