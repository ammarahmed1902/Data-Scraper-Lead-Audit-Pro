"use client";

import Link from "next/link";
import { Flame } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { StatCard } from "@/components/dashboard/stat-card";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/animations/fade-in";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAnalyticsOverview } from "@/hooks/use-analytics";
import { useScoringDashboard } from "@/hooks/use-scoring";
import { Globe, FileSearch, CheckCircle, TrendingUp } from "lucide-react";
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
  const { data: scoring } = useScoringDashboard();
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
            title="Hot Leads"
            value={scoring?.hot_leads ?? "—"}
            icon={<Flame className="h-4 w-4" />}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            title="Completed Audits"
            value={isLoading ? "…" : stats?.completed_audits ?? 0}
            icon={<CheckCircle className="h-4 w-4" />}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            title="Scored Leads"
            value={scoring?.total_scored ?? "—"}
            icon={<FileSearch className="h-4 w-4" />}
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
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Priority Leads</CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link href="/leads">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="mb-4 grid grid-cols-3 gap-2 text-center text-sm">
              <div>
                <p className="text-red-500 font-bold text-lg">{scoring?.hot_leads ?? 0}</p>
                <p className="text-muted-foreground text-xs">Hot</p>
              </div>
              <div>
                <p className="text-orange-500 font-bold text-lg">{scoring?.warm_leads ?? 0}</p>
                <p className="text-muted-foreground text-xs">Warm</p>
              </div>
              <div>
                <p className="text-blue-400 font-bold text-lg">{scoring?.cold_leads ?? 0}</p>
                <p className="text-muted-foreground text-xs">Cold</p>
              </div>
            </div>
            {scoring?.top_hot_leads && scoring.top_hot_leads.length > 0 ? (
              <ul className="space-y-2">
                {scoring.top_hot_leads.map((item) => (
                  <li
                    key={item.lead.id}
                    className="flex justify-between text-sm border-b border-border/50 pb-2"
                  >
                    <span className="truncate pr-2">{item.lead.business_name}</span>
                    <span className="font-semibold text-red-500 shrink-0">
                      {item.score.composite_score != null
                        ? Math.round(item.score.composite_score)
                        : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">
                Score leads after discovery and audit to see hot leads here.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
