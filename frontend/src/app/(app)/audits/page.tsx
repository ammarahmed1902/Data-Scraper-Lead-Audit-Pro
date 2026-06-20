"use client";

import Link from "next/link";

import { PageHeader } from "@/components/dashboard/page-header";
import { AuditScoreCard } from "@/components/audits/audit-score-card";
import { Button } from "@/components/ui/button";
import { useAudits } from "@/hooks/use-audits";

export default function AuditsPage() {
  const { data, isLoading } = useAudits({ page: 1, page_size: 50 });

  return (
    <>
      <PageHeader
        title="Website Audits"
        description="SEO, performance, and technical audit results"
      />

      <div className="glass-card rounded-lg border border-border overflow-hidden">
        {isLoading ? (
          <p className="p-6 text-sm text-muted-foreground">Loading audits...</p>
        ) : (data?.items.length ?? 0) === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No audits yet. Run an audit from the Websites or Discovery page.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-left">
                  <th className="px-4 py-3 font-medium">Audit</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Overall</th>
                  <th className="px-4 py-3 font-medium">SEO</th>
                  <th className="px-4 py-3 font-medium">Perf</th>
                  <th className="px-4 py-3 font-medium">Tech</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {data?.items.map((audit) => (
                  <tr key={audit.id} className="border-b border-border/50">
                    <td className="px-4 py-3 font-mono text-xs">{audit.id.slice(0, 8)}…</td>
                    <td className="px-4 py-3 capitalize">{audit.status}</td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={audit.overall_score} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">—</td>
                    <td className="px-4 py-3 text-muted-foreground">—</td>
                    <td className="px-4 py-3 text-muted-foreground">—</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(audit.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/audits/${audit.id}`}>View</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function ScoreBadge({ score }: { score?: number | null }) {
  if (score == null) return <span className="text-muted-foreground">—</span>;
  const color =
    score >= 80 ? "text-green-600" : score >= 50 ? "text-yellow-600" : "text-destructive";
  return <span className={`font-medium ${color}`}>{Math.round(score)}</span>;
}
