"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, FileText, Loader2 } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { AuditScoreCard } from "@/components/audits/audit-score-card";
import { AuditReportTabs } from "@/components/audits/audit-report-tabs";
import { Button } from "@/components/ui/button";
import { useAudit } from "@/hooks/use-audits";
import { useGenerateReport, useReports } from "@/hooks/use-reports";
import { ApiError } from "@/lib/api-client";

export default function AuditDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: audit, isLoading, error } = useAudit(id);
  const generateReport = useGenerateReport();
  const { data: auditReports } = useReports(
    { audit_id: id },
    audit?.status === "completed",
  );
  const [reportError, setReportError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading audit...
      </div>
    );
  }

  if (error || !audit) {
    return (
      <div className="py-16 text-center">
        <p className="text-destructive">Audit not found or failed to load.</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/audits">Back to audits</Link>
        </Button>
      </div>
    );
  }

  const isRunning = audit.status === "pending" || audit.status === "running";
  const latestReport = auditReports?.items?.[0];

  async function handleGenerateReport() {
    setReportError(null);
    try {
      const report = await generateReport.mutateAsync(id);
      router.push(`/reports/${report.id}`);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "Failed to generate report.";
      setReportError(message);
    }
  }

  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/audits">
            <ArrowLeft className="h-4 w-4" />
            All audits
          </Link>
        </Button>
        {audit.status === "completed" && (
          <div className="flex items-center gap-2">
            {latestReport && (
              <Button variant="outline" size="sm" asChild>
                <Link href={`/reports/${latestReport.id}`}>
                  <FileText className="h-4 w-4" />
                  View report
                </Link>
              </Button>
            )}
            <Button
              size="sm"
              onClick={handleGenerateReport}
              disabled={generateReport.isPending}
            >
              {generateReport.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <FileText className="h-4 w-4" />
              )}
              Generate AI Report
            </Button>
          </div>
        )}
      </div>

      <PageHeader
        title="Website Audit"
        description={`Status: ${audit.status}${isRunning ? " — refreshing every 3s" : ""}`}
      />

      {reportError && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {reportError}
        </p>
      )}

      {audit.error_message && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {audit.error_message}
        </p>
      )}

      {audit.summary && (
        <div className="glass-card mb-6 rounded-lg border border-border p-4">
          <h2 className="mb-2 font-medium">Executive Summary</h2>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">{audit.summary}</p>
        </div>
      )}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
        <AuditScoreCard label="Overall" score={audit.overall_score} highlight />
        <AuditScoreCard label="SEO" score={audit.seo_report?.score} />
        <AuditScoreCard label="Performance" score={audit.performance_report?.score} />
        <AuditScoreCard label="Technical" score={audit.technical_report?.score} />
        <AuditScoreCard label="Security" score={audit.security_score} />
        <AuditScoreCard label="Mobile" score={audit.mobile_score} />
        <AuditScoreCard label="Accessibility" score={audit.accessibility_score} />
        <AuditScoreCard label="Conversion" score={audit.conversion_score} />
        <AuditScoreCard
          label="Opportunity"
          score={audit.lead_opportunity_score}
        />
      </div>

      {audit.status === "completed" ? (
        <AuditReportTabs audit={audit} />
      ) : isRunning ? (
        <div className="flex items-center gap-2 py-8 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          Audit in progress...
        </div>
      ) : null}
    </>
  );
}
