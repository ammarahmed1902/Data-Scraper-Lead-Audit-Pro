"use client";

import { ExternalLink, Eye, FileSearch, Import, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { DiscoveredLead, DiscoverySearch, EnrichmentStatus, LeadClassification, LeadScrapeStatus } from "@/types";
import { cn } from "@/lib/utils";

interface DiscoveredLeadsTableProps {
  search: DiscoverySearch | undefined;
  leads: DiscoveredLead[];
  isLoading?: boolean;
  onImport: (leadId: string) => void;
  importingId?: string | null;
  onEnrich: (leadId: string) => void;
  onEnrichAll?: () => void;
  onScoreAll?: () => void;
  scoringAll?: boolean;
  onAudit?: (leadId: string) => void;
  auditingId?: string | null;
  enrichingId?: string | null;
  enrichingAll?: boolean;
  enrichmentStatusMap?: Record<string, EnrichmentStatus | undefined>;
  leadScoreMap?: Record<string, { classification: LeadClassification; composite: number }>;
  onViewEnrichment: (leadId: string, businessName: string) => void;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function DiscoveredLeadsTable({
  search,
  leads,
  isLoading,
  onImport,
  importingId,
  onEnrich,
  onEnrichAll,
  onScoreAll,
  scoringAll,
  onAudit,
  auditingId,
  enrichingId,
  enrichingAll,
  enrichmentStatusMap = {},
  leadScoreMap = {},
  onViewEnrichment,
  page,
  totalPages,
  onPageChange,
}: DiscoveredLeadsTableProps) {
  if (!search) {
    return (
      <div className="glass-card rounded-lg border border-border p-6">
        <p className="text-sm text-muted-foreground">
          Select a search from history or start a new discovery to view leads.
        </p>
      </div>
    );
  }

  const enrichableCount = leads.filter((l) => l.website_url && !l.is_duplicate).length;

  return (
    <div className="glass-card rounded-lg border border-border p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold capitalize">{search.industry_keyword} Leads</h2>
          <p className="text-sm text-muted-foreground">
            {search.total_found} found · {search.total_new} imported · {search.total_duplicates}{" "}
            duplicates · status: {search.status}
          </p>
          {search.status === "failed" && search.error_message && (
            <p className="mt-1 text-sm text-destructive">{search.error_message}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          {(search.status === "pending" || search.status === "running") && (
            <span className="text-sm text-primary animate-pulse">Discovering...</span>
          )}
          {onScoreAll && search.status === "completed" && (
            <Button size="sm" variant="outline" disabled={scoringAll} onClick={onScoreAll}>
              {scoringAll ? "Scoring..." : "Score All"}
            </Button>
          )}
          {onEnrichAll && enrichableCount > 0 && search.status === "completed" && (
            <Button
              size="sm"
              variant="secondary"
              disabled={enrichingAll}
              onClick={onEnrichAll}
            >
              <Sparkles className="h-3 w-3" />
              {enrichingAll ? "Enriching..." : "Enrich All"}
            </Button>
          )}
        </div>
      </div>

      {search.error_message && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {search.error_message}
        </p>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading leads...</p>
      ) : leads.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {search.status === "completed"
            ? "No new leads found for this search."
            : "Leads will appear here as they are discovered."}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="pb-2 pr-4 font-medium">Business</th>
                <th className="pb-2 pr-4 font-medium">Location</th>
                <th className="pb-2 pr-4 font-medium">Contact</th>
                <th className="pb-2 pr-4 font-medium">Website</th>
                <th className="pb-2 pr-4 font-medium">Enrichment</th>
                <th className="pb-2 pr-4 font-medium">Score</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => {
                const enrichStatus = enrichmentStatusMap[lead.id];
                return (
                  <tr key={lead.id} className="border-b border-border/50">
                    <td className="py-3 pr-4">
                      <div className="font-medium">{lead.business_name}</div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {lead.business_category ?? "—"}
                        {lead.is_duplicate && " · duplicate"}
                      </div>
                      {lead.scrape_status && (
                        <ScrapeStatusBadge status={lead.scrape_status} />
                      )}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {[lead.city, lead.state, lead.country].filter(Boolean).join(", ") || "—"}
                      {lead.address && <div className="text-xs">{lead.address}</div>}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {lead.phone_number && <div>{lead.phone_number}</div>}
                      {lead.email_address && <div>{lead.email_address}</div>}
                      {!lead.phone_number && !lead.email_address && "—"}
                    </td>
                    <td className="py-3 pr-4">
                      {lead.website_url ? (
                        <a
                          href={lead.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-primary hover:underline"
                        >
                          {lead.domain ?? "Visit"}
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      {lead.website_url ? (
                        <EnrichmentBadge status={enrichStatus} />
                      ) : (
                        <span className="text-xs text-muted-foreground">No website</span>
                      )}
                    </td>
                    <td className="py-3 pr-4">
                      <LeadScoreBadge score={leadScoreMap[lead.id]} />
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-1">
                        {lead.website_url && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={
                                enrichingId === lead.id ||
                                enrichStatus === "running" ||
                                enrichStatus === "pending"
                              }
                              onClick={() => onEnrich(lead.id)}
                            >
                              <Sparkles className="h-3 w-3" />
                              {enrichingId === lead.id ||
                              enrichStatus === "running" ||
                              enrichStatus === "pending"
                                ? "..."
                                : enrichStatus === "completed"
                                  ? "Re-enrich"
                                  : "Enrich"}
                            </Button>
                            {(enrichStatus === "completed" || enrichStatus === "failed") && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() =>
                                  onViewEnrichment(lead.id, lead.business_name)
                                }
                              >
                                <Eye className="h-3 w-3" />
                                View
                              </Button>
                            )}
                            {onAudit && (
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={auditingId === lead.id}
                                onClick={() => onAudit(lead.id)}
                              >
                                <FileSearch className="h-3 w-3" />
                                {auditingId === lead.id ? "..." : "Audit"}
                              </Button>
                            )}
                          </>
                        )}
                        {lead.imported_website_id ? (
                          <span className="self-center text-xs text-muted-foreground">
                            Imported
                          </span>
                        ) : lead.website_url ? (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={importingId === lead.id}
                            onClick={() => onImport(lead.id)}
                          >
                            <Import className="h-3 w-3" />
                            {importingId === lead.id ? "..." : "Import"}
                          </Button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

function LeadScoreBadge({
  score,
}: {
  score?: { classification: LeadClassification; composite: number };
}) {
  if (!score) {
    return <span className="text-xs text-muted-foreground">Not scored</span>;
  }
  const colors: Record<LeadClassification, string> = {
    hot: "text-red-500",
    warm: "text-orange-500",
    cold: "text-blue-400",
  };
  return (
    <span className={`text-xs capitalize ${colors[score.classification]}`}>
      {score.classification} · {Math.round(score.composite)}
    </span>
  );
}

function EnrichmentBadge({ status }: { status?: EnrichmentStatus }) {
  if (!status) {
    return <span className="text-xs text-muted-foreground">Not enriched</span>;
  }
  const styles: Record<EnrichmentStatus, string> = {
    pending: "text-yellow-600",
    running: "text-primary animate-pulse",
    completed: "text-green-600",
    failed: "text-destructive",
  };
  return <span className={`text-xs capitalize ${styles[status]}`}>{status}</span>;
}

function ScrapeStatusBadge({ status }: { status: LeadScrapeStatus }) {
  const styles: Record<LeadScrapeStatus, string> = {
    success: "text-green-600",
    partial: "text-yellow-600",
    failed: "text-destructive",
    skipped: "text-muted-foreground",
  };
  return (
    <span className={cn("mt-0.5 inline-block text-xs capitalize", styles[status])}>
      Scraped: {status}
    </span>
  );
}
