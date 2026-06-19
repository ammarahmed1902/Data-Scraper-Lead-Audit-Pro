"use client";

import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations/fade-in";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAnalyticsOverview } from "@/hooks/use-analytics";
import { Globe, FileSearch, CheckCircle, Clock, TrendingUp } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function DashboardPage() {
  const { data, isLoading } = useAnalyticsOverview();
  const stats = data?.stats;

  return (
    <>
      <FadeIn>
        <PageHeader
          title="Dashboard"
          description="Overview of your lead audit pipeline"
        />
      </FadeIn>

      <StaggerContainer className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <StaggerItem>
          <StatCard
            title="Total Websites"
            value={isLoading ? "…" : stats?.total_websites ?? 0}
            icon={<Globe className="h-4 w-4" />}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            title="Total Audits"
            value={isLoading ? "…" : stats?.total_audits ?? 0}
            icon={<FileSearch className="h-4 w-4" />}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            title="Completed"
            value={isLoading ? "…" : stats?.completed_audits ?? 0}
            icon={<CheckCircle className="h-4 w-4" />}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            title="Pending"
            value={isLoading ? "…" : stats?.pending_audits ?? 0}
            icon={<Clock className="h-4 w-4" />}
          />
        </StaggerItem>
      </StaggerContainer>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              Score Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[280px]">
            {data?.score_distribution?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.score_distribution}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="range_label" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-16">
                Run audits to see score distribution
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader>
            <CardTitle>Priority Leads</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Average Score</span>
                <span className="font-semibold">
                  {stats?.average_score != null ? `${stats.average_score}/100` : "—"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Audits This Week</span>
                <span className="font-semibold">{stats?.audits_this_week ?? 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Audits This Month</span>
                <span className="font-semibold">{stats?.audits_this_month ?? 0}</span>
              </div>
            </div>
            {data?.top_issues && data.top_issues.length > 0 && (
              <div className="mt-6">
                <p className="text-sm font-medium mb-2">Top Issues</p>
                <ul className="space-y-1">
                  {(data.top_issues as { code: string; count: number }[]).slice(0, 5).map((issue) => (
                    <li key={issue.code} className="flex justify-between text-xs text-muted-foreground">
                      <span>{issue.code.replace(/_/g, " ")}</span>
                      <span>{issue.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
