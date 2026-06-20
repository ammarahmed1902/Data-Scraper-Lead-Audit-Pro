"use client";

import { useCallback, useRef } from "react";

import { logApi } from "@/lib/api-logger";
import { discoveryService } from "@/services/discovery-service";
import type { DiscoverySearch } from "@/types";

const POLL_INTERVAL_MS = 2500;
const MAX_POLL_MS = 5 * 60 * 1000;

export function useDiscoveryTab() {
  const tabRef = useRef<Window | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const cleanup = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const closeSourceTab = useCallback(() => {
    if (tabRef.current && !tabRef.current.closed) {
      try {
        tabRef.current.close();
      } catch {
        // Browser may block close in edge cases; safe to ignore.
      }
    }
    tabRef.current = null;
  }, []);

  const openSourceTab = useCallback(
    (url: string) => {
      closeSourceTab();
      tabRef.current = window.open(url, "_blank");
      return tabRef.current;
    },
    [closeSourceTab],
  );

  const watchSearchAndCloseTab = useCallback(
    (searchId: string, onComplete?: (search?: DiscoverySearch) => void) => {
      cleanup();
      const started = Date.now();

      pollRef.current = setInterval(async () => {
        if (Date.now() - started > MAX_POLL_MS) {
          cleanup();
          closeSourceTab();
          logApi({
            step: "discovery_poll_timeout",
            url: `/discovery/searches/${searchId}`,
            detail: { searchId },
          });
          return;
        }

        try {
          const search = await discoveryService.getSearch(searchId);
          logApi({
            step: "discovery_poll_status",
            url: `/discovery/searches/${searchId}`,
            detail: {
              status: search.status,
              total_found: search.total_found,
              total_new: search.total_new,
              total_duplicates: search.total_duplicates,
            },
          });
          if (search.status === "completed" || search.status === "failed") {
            cleanup();
            closeSourceTab();
            onComplete?.(search);
          }
        } catch (error) {
          logApi({
            step: "discovery_poll_error",
            url: `/discovery/searches/${searchId}`,
            error: error instanceof Error ? error.message : String(error),
          });
        }
      }, POLL_INTERVAL_MS);
    },
    [cleanup, closeSourceTab],
  );

  return {
    openSourceTab,
    watchSearchAndCloseTab,
    closeSourceTab,
    cleanup,
  };
}
