"use client";

import { PageHeader } from "@/components/dashboard/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsOverview, useAuditTrends } from "@/hooks/use-analytics";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
  BarChart,
} from "recharts";

export default function AnalyticsPage() {
  const { data: overview, isLoading } = useAnalyticsOverview();
  const { data: trends } = useAuditTrends("30d");

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Audit trends, score distributions, and insights"
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Audit Trends (30 days)</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {trends && Array.isArray(trends) && trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="date" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Line type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} name="Audits" />
                  <Line type="monotone" dataKey="average_score" stroke="hsl(var(--success))" strokeWidth={2} name="Avg Score" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-20">
                {isLoading ? "Loading…" : "No audit trend data yet"}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            {overview?.score_distribution?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={overview.score_distribution}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="range_label" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-20">No score data yet</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card lg:col-span-2">
          <CardHeader>
            <CardTitle>Top Recurring Issues</CardTitle>
          </CardHeader>
          <CardContent>
            {overview?.top_issues && overview.top_issues.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 font-medium">Issue</th>
                      <th className="text-right py-2 font-medium">Occurrences</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(overview.top_issues as { code: string; count: number }[]).map((issue) => (
                      <tr key={issue.code} className="border-b border-border/50">
                        <td className="py-2">{issue.code.replace(/_/g, " ")}</td>
                        <td className="py-2 text-right text-muted-foreground">{issue.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Complete audits to surface recurring issues.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
