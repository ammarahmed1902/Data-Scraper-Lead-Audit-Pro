"use client";

import { formatDate } from "@/utils/format";
import type { DiscoverySearch } from "@/types";
import { getCategoryLabel, getWebsiteLabel } from "@/lib/discovery-sources";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-500/10 text-yellow-600",
  running: "bg-blue-500/10 text-blue-600",
  completed: "bg-green-500/10 text-green-600",
  failed: "bg-destructive/10 text-destructive",
  cancelled: "bg-muted text-muted-foreground",
};

interface DiscoverySearchHistoryProps {
  searches: DiscoverySearch[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  isLoading?: boolean;
}

export function DiscoverySearchHistory({
  searches,
  selectedId,
  onSelect,
  isLoading,
}: DiscoverySearchHistoryProps) {
  if (isLoading) {
    return (
      <div className="glass-card rounded-lg border border-border p-6">
        <p className="text-sm text-muted-foreground">Loading search history...</p>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-lg border border-border p-6">
      <h2 className="mb-4 text-lg font-semibold">Search History</h2>
      {searches.length === 0 ? (
        <p className="text-sm text-muted-foreground">No searches yet. Start your first discovery above.</p>
      ) : (
        <ul className="space-y-2">
          {searches.map((search) => (
            <li key={search.id}>
              <button
                type="button"
                onClick={() => onSelect(search.id)}
                className={cn(
                  "w-full rounded-md border px-3 py-2 text-left transition-colors",
                  selectedId === search.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:bg-accent",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium capitalize">{search.industry_keyword}</span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                      STATUS_STYLES[search.status] ?? STATUS_STYLES.pending,
                    )}
                  >
                    {search.status}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {[search.city, search.state, search.country].filter(Boolean).join(", ")}
                </p>
                {(search.data_source_category || search.data_source_website) && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {search.data_source_category
                      ? getCategoryLabel(search.data_source_category)
                      : "Unknown source"}
                    {search.data_source_website
                      ? ` · ${getWebsiteLabel(search.data_source_category ?? "", search.data_source_website)}`
                      : ""}
                  </p>
                )}
                <p className="mt-1 text-xs text-muted-foreground">
                  {search.total_new} new · {search.total_duplicates} duplicates ·{" "}
                  {formatDate(search.created_at)}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
