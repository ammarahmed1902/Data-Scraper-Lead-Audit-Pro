"use client";

import { useState } from "react";
import { Download, FileText, Plus } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { exportService, reportService } from "@/services/report-service";
import { downloadAuthenticatedFile } from "@/lib/download";

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [exporting, setExporting] = useState(false);

  const { data: reports, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportService.list(),
  });

  const createExport = useMutation({
    mutationFn: () => exportService.create("leads", "xlsx"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["exports"] }),
  });

  const { data: exports } = useQuery({
    queryKey: ["exports"],
    queryFn: () => exportService.list(),
  });

  async function handleExport() {
    setExporting(true);
    try {
      await createExport.mutateAsync();
    } finally {
      setExporting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Reports"
        description="Generated audit reports and lead exports"
        actions={
          <Button onClick={handleExport} disabled={exporting || createExport.isPending}>
            <Plus className="h-4 w-4" />
            Export All Leads (XLSX)
          </Button>
        }
      />

      <div className="space-y-8">
        <section>
          <h2 className="text-lg font-semibold mb-4">Audit Reports</h2>
          <Card className="glass-card overflow-hidden">
            <CardContent className="p-0">
              {isLoading ? (
                <p className="p-8 text-center text-muted-foreground">Loading reports…</p>
              ) : !reports?.items.length ? (
                <p className="p-8 text-center text-muted-foreground">
                  No reports yet. Run an audit, then generate a PDF from the audit detail.
                </p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/30">
                      <th className="px-4 py-3 text-left font-medium">Title</th>
                      <th className="px-4 py-3 text-left font-medium">Format</th>
                      <th className="px-4 py-3 text-left font-medium">Generated</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.items.map((report) => (
                      <tr key={report.id} className="border-b border-border/50">
                        <td className="px-4 py-3 flex items-center gap-2">
                          <FileText className="h-4 w-4 text-primary" />
                          {report.title}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant="secondary">{report.format.toUpperCase()}</Badge>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {new Date(report.generated_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {report.file_path && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                downloadAuthenticatedFile(
                                  reportService.downloadUrl(report.id),
                                  `report-${report.id}.pdf`,
                                )
                              }
                            >
                              <Download className="h-4 w-4" />
                              Download
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Export History</h2>
          <Card className="glass-card overflow-hidden">
            <CardContent className="p-0">
              {!exports?.items.length ? (
                <p className="p-8 text-center text-muted-foreground">No exports yet.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/30">
                      <th className="px-4 py-3 text-left font-medium">Type</th>
                      <th className="px-4 py-3 text-left font-medium">Format</th>
                      <th className="px-4 py-3 text-left font-medium">Status</th>
                      <th className="px-4 py-3 text-left font-medium">Records</th>
                      <th className="px-4 py-3 text-right font-medium">Download</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exports.items.map((job) => (
                      <tr key={job.id} className="border-b border-border/50">
                        <td className="px-4 py-3">{job.export_type}</td>
                        <td className="px-4 py-3">{job.format.toUpperCase()}</td>
                        <td className="px-4 py-3">
                          <Badge variant={job.status === "completed" ? "success" : "secondary"}>
                            {job.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {job.record_count ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          {job.status === "completed" && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                downloadAuthenticatedFile(
                                  exportService.downloadUrl(job.id),
                                  `export-${job.id}.${job.format}`,
                                )
                              }
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </CardContent>
          </Card>
        </section>
      </div>
    </>
  );
}
