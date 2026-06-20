"use client";

import { useEffect } from "react";

import { useDashboardStore } from "@/store/dashboard-store";

export function DashboardStoreHydration() {
  useEffect(() => {
    const markHydrated = () => {
      useDashboardStore.setState({ _hasHydrated: true });
    };

    const unsub = useDashboardStore.persist.onFinishHydration(markHydrated);

    if (useDashboardStore.persist.hasHydrated()) {
      markHydrated();
    } else {
      void useDashboardStore.persist.rehydrate();
    }

    return unsub;
  }, []);

  return null;
}
