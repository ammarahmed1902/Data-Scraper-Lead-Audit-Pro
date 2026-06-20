"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Download, Loader2 } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { ReportContentView } from "@/components/reports/report-content-view";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useReport, useReportContent } from "@/hooks/use-reports";
import { downloadAuthenticatedFile } from "@/lib/download";
import { reportService } from "@/services/report-service";

function statusVariant(status: string) {
  if (status === "completed") return "success" as const;
  if (status === "failed") return "destructive" as const;
  if (status === "generating") return "warning" as const;
  return "secondary" as const;
}

export default function ReportDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: report, isLoading } = useReport(id);
  const { data: contentData, isLoading: contentLoading } = useReportContent(
    id,
    report?.status === "completed" || report?.has_content === true,
  );

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        Loading report...
      </div>
    );
  }

  if (!report) {
    return (
      <div className="py-16 text-center">
        <p className="text-destructive">Report not found.</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/reports">Back to reports</Link>
        </Button>
      </div>
    );
  }

  const isGenerating = report.status === "pending" || report.status === "generating";

  return (
    <>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/reports">
            <ArrowLeft className="h-4 w-4" />
            All reports
          </Link>
        </Button>
        <div className="flex items-center gap-2">
          <Badge variant={statusVariant(report.status)}>{report.status}</Badge>
          {report.file_path && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                downloadAuthenticatedFile(
                  reportService.downloadUrl(report.id),
                  `report-${report.id}.${report.format}`,
                )
              }
            >
              <Download className="h-4 w-4" />
              Download {report.format.toUpperCase()}
            </Button>
          )}
          <Button variant="outline" size="sm" asChild>
            <Link href={`/audits/${report.audit_report_id}`}>View audit</Link>
          </Button>
        </div>
      </div>

      <PageHeader title={report.title} description={`Report ID: ${report.id}`} />

      {report.error_message && (
        <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {report.error_message}
        </p>
      )}

      {isGenerating && (
        <div className="mb-6 flex items-center gap-2 rounded-md border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          AI report is being generated — this page refreshes automatically.
        </div>
      )}

      {contentLoading && !contentData ? (
        <div className="flex items-center gap-2 py-8 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          Loading report content...
        </div>
      ) : contentData?.content ? (
        <ReportContentView content={contentData.content} />
      ) : report.status === "completed" ? (
        <p className="text-sm text-muted-foreground">Report content unavailable.</p>
      ) : null}
    </>
  );
}
