"use client";

import Link from "next/link";
import { useMemo } from "react";
import { ExternalLink } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { useAudits } from "@/hooks/use-audits";
import { useWebsites } from "@/hooks/use-websites";
import type { AuditListItem } from "@/types";

export default function AuditsPage() {
  const { data, isLoading } = useAudits({ page: 1, page_size: 50 });
  const { data: websitesData } = useWebsites({ page: 1, page_size: 100 });

  const websiteById = useMemo(() => {
    const map = new Map<string, { company_name?: string | null; url: string; domain: string }>();
    for (const website of websitesData?.items ?? []) {
      map.set(website.id, {
        company_name: website.company_name,
        url: website.url,
        domain: website.domain,
      });
    }
    return map;
  }, [websitesData?.items]);

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
                  <th className="px-4 py-3 font-medium">Company Name</th>
                  <th className="px-4 py-3 font-medium">Website Name</th>
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
                {data?.items.map((audit) => {
                  const website = websiteById.get(audit.website_id);
                  const companyName = audit.company_name ?? website?.company_name;
                  const websiteUrl = audit.website_url ?? website?.url;
                  const domain = audit.domain ?? website?.domain;

                  return (
                  <tr key={audit.id} className="border-b border-border/50">
                    <td className="px-4 py-3 text-muted-foreground">
                      {companyName?.trim() || "—"}
                    </td>
                    <td className="px-4 py-3">
                      <WebsiteCell
                        audit={{
                          ...audit,
                          company_name: companyName,
                          website_url: websiteUrl,
                          domain,
                        }}
                      />
                    </td>
                    <td className="px-4 py-3 capitalize">{audit.status}</td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={audit.overall_score} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={audit.seo_score} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={audit.performance_score} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={audit.technical_score} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(audit.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Button variant="outline" size="sm" asChild>
                        <Link href={`/audits/${audit.id}`}>View</Link>
                      </Button>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}

function WebsiteCell({ audit }: { audit: AuditListItem }) {
  const label = audit.domain?.trim() || audit.website_url?.trim();
  if (!label) {
    return <span className="text-muted-foreground">—</span>;
  }

  if (audit.website_url) {
    return (
      <div className="flex flex-col gap-0.5">
        <a
          href={audit.website_url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-primary hover:underline inline-flex items-center gap-1"
        >
          {audit.domain || audit.website_url}
          <ExternalLink className="h-3 w-3" />
        </a>
        {audit.domain && audit.website_url !== audit.domain && (
          <span className="text-xs text-muted-foreground truncate max-w-[220px]">
            {audit.website_url}
          </span>
        )}
      </div>
    );
  }

  return <span>{label}</span>;
}

function ScoreBadge({ score }: { score?: number | null }) {
  if (score == null) return <span className="text-muted-foreground">—</span>;
  const color =
    score >= 80 ? "text-green-600" : score >= 50 ? "text-yellow-600" : "text-destructive";
  return <span className={`font-medium ${color}`}>{Math.round(score)}</span>;
}
