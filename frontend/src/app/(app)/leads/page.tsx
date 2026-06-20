"use client";

import { useState } from "react";
import { Flame, Filter } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { OpportunityReportDialog } from "@/components/scoring/opportunity-report-dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRankedLeads, useScoringDashboard } from "@/hooks/use-scoring";
import type { LeadClassification } from "@/types";

const OPPORTUNITY_FILTERS = [
  { value: "all", label: "All opportunities" },
  { value: "missing_seo", label: "Missing SEO" },
  { value: "poor_performance", label: "Poor Performance" },
  { value: "technical_problems", label: "Technical Problems" },
  { value: "missing_tracking_pixels", label: "Missing Tracking" },
  { value: "missing_analytics", label: "Missing Analytics" },
  { value: "missing_conversion_elements", label: "Missing Conversions" },
];

export default function LeadsPriorityPage() {
  const [classification, setClassification] = useState<LeadClassification | "">("");
  const [opportunity, setOpportunity] = useState("all");
  const [page, setPage] = useState(1);
  const [reportLeadId, setReportLeadId] = useState<string | null>(null);

  const { data: dashboard } = useScoringDashboard();
  const { data: ranked, isLoading } = useRankedLeads({
    page,
    classification: classification || undefined,
    opportunity: opportunity === "all" ? undefined : opportunity,
  });

  return (
    <>
      <PageHeader
        title="Lead Priority"
        description="Ranked leads by opportunity score — hot, warm, and cold classifications"
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Hot Leads" value={dashboard?.hot_leads ?? 0} variant="hot" />
        <StatCard label="Warm Leads" value={dashboard?.warm_leads ?? 0} variant="warm" />
        <StatCard label="Cold Leads" value={dashboard?.cold_leads ?? 0} variant="cold" />
        <StatCard
          label="Avg Score"
          value={
            dashboard?.average_composite_score != null
              ? `${Math.round(dashboard.average_composite_score)}`
              : "—"
          }
          variant="default"
        />
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <Select
          value={classification || "all"}
          onValueChange={(v) => {
            setClassification(v === "all" ? "" : (v as LeadClassification));
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[160px]">
            <Filter className="h-3 w-3 mr-1" />
            <SelectValue placeholder="Classification" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All classes</SelectItem>
            <SelectItem value="hot">Hot</SelectItem>
            <SelectItem value="warm">Warm</SelectItem>
            <SelectItem value="cold">Cold</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={opportunity}
          onValueChange={(v) => {
            setOpportunity(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Opportunity type" />
          </SelectTrigger>
          <SelectContent>
            {OPPORTUNITY_FILTERS.map((f) => (
              <SelectItem key={f.value} value={f.value}>
                {f.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="glass-card rounded-lg border border-border overflow-hidden">
        {isLoading ? (
          <p className="p-6 text-sm text-muted-foreground">Loading ranked leads...</p>
        ) : (ranked?.items.length ?? 0) === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No scored leads yet. Run audits and score leads from Discovery.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-left">
                  <th className="px-4 py-3 font-medium">Rank</th>
                  <th className="px-4 py-3 font-medium">Business</th>
                  <th className="px-4 py-3 font-medium">Class</th>
                  <th className="px-4 py-3 font-medium">Composite</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">SEO Opp</th>
                  <th className="px-4 py-3 font-medium hidden md:table-cell">Tech Opp</th>
                  <th className="px-4 py-3 font-medium hidden lg:table-cell">Sales</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {ranked?.items.map((item) => (
                  <tr key={item.score.id} className="border-b border-border/50">
                    <td className="px-4 py-3 font-mono">#{item.rank ?? "—"}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.lead.business_name}</div>
                      <div className="text-xs text-muted-foreground">{item.lead.domain}</div>
                    </td>
                    <td className="px-4 py-3">
                      <ClassificationBadge classification={item.score.classification} />
                    </td>
                    <td className="px-4 py-3 font-semibold">
                      {item.score.composite_score != null
                        ? Math.round(item.score.composite_score)
                        : "—"}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-muted-foreground">
                      {item.score.seo_opportunity_score != null
                        ? Math.round(item.score.seo_opportunity_score)
                        : "—"}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-muted-foreground">
                      {item.score.technical_opportunity_score != null
                        ? Math.round(item.score.technical_opportunity_score)
                        : "—"}
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell text-muted-foreground">
                      {item.score.sales_potential_score != null
                        ? Math.round(item.score.sales_potential_score)
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setReportLeadId(item.lead.id)}
                      >
                        Report
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {(ranked?.total_pages ?? 1) > 1 && (
        <div className="mt-4 flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="self-center text-sm text-muted-foreground">
            Page {page} of {ranked?.total_pages ?? 1}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= (ranked?.total_pages ?? 1)}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}

      <OpportunityReportDialog
        leadId={reportLeadId}
        onClose={() => setReportLeadId(null)}
      />
    </>
  );
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number | string;
  variant: "hot" | "warm" | "cold" | "default";
}) {
  const colors = {
    hot: "text-red-500",
    warm: "text-orange-500",
    cold: "text-blue-400",
    default: "text-primary",
  };
  return (
    <div className="glass-card rounded-lg border border-border p-4">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${colors[variant]}`}>{value}</p>
    </div>
  );
}

function ClassificationBadge({ classification }: { classification: LeadClassification }) {
  const styles: Record<LeadClassification, string> = {
    hot: "bg-red-500/10 text-red-500",
    warm: "bg-orange-500/10 text-orange-500",
    cold: "bg-blue-500/10 text-blue-400",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs capitalize ${styles[classification]}`}
    >
      {classification === "hot" && <Flame className="h-3 w-3" />}
      {classification}
    </span>
  );
}
