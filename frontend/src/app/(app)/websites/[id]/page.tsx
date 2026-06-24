"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, ExternalLink, FileSearch, Loader2, Pencil } from "lucide-react";

import { AuditScoreCard } from "@/components/audits/audit-score-card";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAudits, useCreateAudit } from "@/hooks/use-audits";
import { usePermissions } from "@/hooks/use-permissions";
import { useWebsite } from "@/hooks/use-websites";
import { toast } from "@/hooks/use-toast";

export default function WebsiteDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: website, isLoading, error } = useWebsite(id);
  const { data: auditsData, isLoading: auditsLoading } = useAudits({
    website_id: id,
    page_size: 10,
  });
  const createAudit = useCreateAudit();
  const { canRunAudit, canUpdateWebsite } = usePermissions();

  const latestAudit = auditsData?.items?.[0];

  async function handleAudit() {
    try {
      const audit = await createAudit.mutateAsync(id);
      toast({ title: "Audit started", description: "Redirecting to audit progress..." });
      router.push(`/audits/${audit.id}`);
    } catch (err) {
      toast({
        title: "Audit failed",
        description: err instanceof Error ? err.message : "Could not start audit",
        variant: "destructive",
      });
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading website...
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="py-16 text-center">
        <p className="text-destructive">Website not found or failed to load.</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/websites">Back to websites</Link>
        </Button>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/websites">
            <ArrowLeft className="h-4 w-4" />
            All websites
          </Link>
        </Button>
        <div className="flex gap-2">
          {canUpdateWebsite && (
            <Button variant="outline" size="sm" asChild>
              <Link href={`/websites?edit=${website.id}`}>
                <Pencil className="h-4 w-4" />
                Edit
              </Link>
            </Button>
          )}
          {canRunAudit && (
            <Button size="sm" onClick={handleAudit} disabled={createAudit.isPending}>
              {createAudit.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileSearch className="h-4 w-4" />
              )}
              Run audit
            </Button>
          )}
        </div>
      </div>

      <PageHeader
        title={website.company_name?.trim() || website.domain}
        description={website.url}
      />

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className="glass-card rounded-lg border border-border p-4 space-y-3">
          <h2 className="font-medium">Website details</h2>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <DetailItem label="Domain" value={website.domain} />
            <DetailItem label="Status">
              <Badge>{website.status}</Badge>
            </DetailItem>
            <DetailItem label="Company" value={website.company_name || "—"} />
            <DetailItem label="Contact" value={website.contact_name || "—"} />
            <DetailItem label="Email" value={website.contact_email || "—"} />
            <DetailItem label="Phone" value={website.contact_phone || "—"} />
            <DetailItem
              label="Last audited"
              value={
                website.last_audited_at
                  ? new Date(website.last_audited_at).toLocaleString()
                  : "Never"
              }
            />
            <DetailItem label="Added" value={new Date(website.created_at).toLocaleDateString()} />
          </dl>
          <a
            href={website.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Open live site
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>

        <div className="glass-card rounded-lg border border-border p-4">
          <h2 className="mb-3 font-medium">Latest audit scores</h2>
          {latestAudit ? (
            <>
              <div className="mb-4 grid gap-3 sm:grid-cols-2">
                <AuditScoreCard label="Overall" score={latestAudit.overall_score} highlight />
                <AuditScoreCard label="SEO" score={latestAudit.seo_score} />
                <AuditScoreCard label="Performance" score={latestAudit.performance_score} />
                <AuditScoreCard label="Technical" score={latestAudit.technical_score} />
              </div>
              <Button size="sm" asChild>
                <Link href={`/audits/${latestAudit.id}`}>View full audit</Link>
              </Button>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              No audits yet.{canRunAudit ? " Run an audit to see scores here." : ""}
            </p>
          )}
        </div>
      </div>

      <div className="glass-card rounded-lg border border-border overflow-hidden">
        <div className="border-b border-border px-4 py-3">
          <h2 className="font-medium">Audit history</h2>
        </div>
        {auditsLoading ? (
          <p className="p-4 text-sm text-muted-foreground">Loading audits...</p>
        ) : (auditsData?.items.length ?? 0) === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">No audit history for this website.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-left">
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Overall</th>
                  <th className="px-4 py-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {auditsData?.items.map((audit) => (
                  <tr key={audit.id} className="border-b border-border/50">
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(audit.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">{audit.status}</td>
                    <td className="px-4 py-3">{audit.overall_score ?? "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm" asChild>
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

function DetailItem({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 font-medium">{children ?? value}</dd>
    </div>
  );
}
