"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import type { AuditCategoryBreakdown, AuditReport } from "@/types";

const TABS = [
  "SEO",
  "Performance",
  "Functional",
  "Mobile",
  "Technical SEO",
  "SEO Strategy",
  "Security",
  "Accessibility",
  "Marketing",
  "Conversion",
  "QA",
  "Technology",
] as const;
type Tab = (typeof TABS)[number];

interface AuditReportTabsProps {
  audit: AuditReport;
}

export function AuditReportTabs({ audit }: AuditReportTabsProps) {
  const [tab, setTab] = useState<Tab>("SEO");

  return (
    <div className="glass-card rounded-lg border border-border">
      <div className="flex flex-wrap border-b border-border">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={cn(
              "px-4 py-3 text-sm font-medium transition-colors",
              tab === t
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="p-4">
        {tab === "SEO" && <SeoPanel report={audit.seo_report} />}
        {tab === "Performance" && (
          audit.performance_report ? (
            <PerformancePanel report={audit.performance_report} />
          ) : (
            <CategoryPanel category={audit.category_breakdown?.performance} />
          )
        )}
        {tab === "Functional" && (
          <CategoryPanel category={audit.category_breakdown?.functional} />
        )}
        {tab === "Mobile" && (
          <CategoryPanel category={audit.category_breakdown?.mobile} />
        )}
        {tab === "Technical SEO" && (
          <CategoryPanel category={audit.category_breakdown?.technical_seo} />
        )}
        {tab === "SEO Strategy" && (
          <CategoryPanel category={audit.category_breakdown?.seo_strategy} />
        )}
        {tab === "Security" && (
          <CategoryPanel category={audit.category_breakdown?.security} />
        )}
        {tab === "Accessibility" && (
          <CategoryPanel category={audit.category_breakdown?.accessibility} />
        )}
        {tab === "Marketing" && (
          <CategoryPanel category={audit.category_breakdown?.marketing} />
        )}
        {tab === "Conversion" && (
          <CategoryPanel category={audit.category_breakdown?.conversion} />
        )}
        {tab === "QA" && <CategoryPanel category={audit.category_breakdown?.qa} />}
        {tab === "Technology" && (
          <TechnologyPanel
            report={audit.technical_report}
            category={audit.category_breakdown?.technology}
          />
        )}
      </div>
    </div>
  );
}

function SeoPanel({ report }: { report: AuditReport["seo_report"] }) {
  if (!report) return <EmptyPanel />;
  const h2Tags = (report.issues?.meta as { h2_tags?: string[] } | undefined)?.h2_tags ?? [];
  const h1Tags = (report.issues?.meta as { h1_tags?: string[] } | undefined)?.h1_tags ?? [];

  return (
    <div className="space-y-4 text-sm">
      <MetricGrid
        items={[
          ["Title", report.title_tag ?? "—"],
          ["Meta Description", truncate(report.meta_description, 120)],
          ["H1 Count", String(report.h1_count ?? 0)],
          ["H2 Count", String(report.h2_count ?? h2Tags.length)],
          ["Canonical", report.canonical_url ?? "—"],
          ["Internal Links", String(report.internal_links ?? 0)],
          ["Broken Links", String(report.broken_links ?? 0)],
          ["Sitemap", report.has_sitemap ? "Yes" : "No"],
          ["Robots.txt", report.has_robots_txt ? "Yes" : "No"],
        ]}
      />
      {h1Tags.length > 0 && <TagList title="H1 Tags" items={h1Tags} />}
      {h2Tags.length > 0 && <TagList title="H2 Tags" items={h2Tags} />}
      <IssuesList issues={report.issues?.items} />
      <RecommendationsList items={report.recommendations?.items} />
    </div>
  );
}

function PerformancePanel({ report }: { report: AuditReport["performance_report"] }) {
  if (!report) return <EmptyPanel />;
  const metrics = report.metrics ?? {};

  return (
    <div className="space-y-4 text-sm">
      <MetricGrid
        items={[
          ["LCP", formatMs(report.largest_contentful_paint)],
          ["FCP", formatMs(report.first_contentful_paint)],
          ["CLS", report.cumulative_layout_shift?.toString() ?? "—"],
          ["TTFB", formatMs(metrics.ttfb as number | undefined)],
          ["Load Time", formatMs(report.load_time_ms)],
          ["Page Size", report.page_size_kb ? `${report.page_size_kb} KB` : "—"],
          ["Source", String(metrics.source ?? "—")],
        ]}
      />
      <IssuesList issues={report.issues?.items} />
      <RecommendationsList items={report.recommendations?.items} />
    </div>
  );
}

function TechnicalPanel({ report }: { report: AuditReport["technical_report"] }) {
  if (!report) return <EmptyPanel />;

  return (
    <div className="space-y-4 text-sm">
      <MetricGrid
        items={[
          ["SSL Valid", report.ssl_valid ? "Yes" : "No"],
          ["HTTPS", report.issues?.meta?.uses_https ? "Yes" : "Unknown"],
          ["HTTP Status", String(report.http_status_code ?? "—")],
          ["Mobile Friendly", report.mobile_friendly ? "Yes" : "No"],
          ["Indexable", report.indexable === false ? "No (noindex)" : "Yes"],
          ["Accessibility", report.accessibility_score?.toString() ?? "—"],
          ["Server", report.server_header ?? "—"],
        ]}
      />
      <IssuesList issues={report.issues?.items} />
      <RecommendationsList items={report.recommendations?.items} />
    </div>
  );
}

function CategoryPanel({ category }: { category?: AuditCategoryBreakdown }) {
  if (!category) return <EmptyPanel />;
  const checks = (category.checks as Record<string, unknown>) ?? {};
  const checkItems = Object.entries(checks)
    .filter(([, v]) => typeof v !== "object" || v === null)
    .slice(0, 12)
    .map(([k, v]) => [k.replace(/_/g, " "), String(v)] as [string, string]);

  return (
    <div className="space-y-4 text-sm">
      {category.score != null && (
        <p className="font-medium">Score: {String(category.score)}/100</p>
      )}
      {checkItems.length > 0 && <MetricGrid items={checkItems} />}
      <IssuesList
        issues={
          (category.issues as { items?: { severity: string; code: string; message: string }[] })
            ?.items
        }
      />
      <RecommendationsList
        items={
          (
            category.recommendations as {
              items?: { priority: string; title: string; description: string }[];
            }
          )?.items
        }
      />
    </div>
  );
}

function TechnologyPanel({
  report,
  category,
}: {
  report: AuditReport["technical_report"];
  category?: AuditCategoryBreakdown;
}) {
  const checks = (category?.checks as Record<string, unknown>) ?? {};
  const stack = (checks.technology_stack as string[]) ?? report?.technologies?.detected ?? [];

  return (
    <div className="space-y-4 text-sm">
      <MetricGrid
        items={[
          ["CMS Platform", String(checks.cms_platform ?? report?.technologies?.cms_platform ?? "—")],
          ["Framework", String(checks.framework ?? "—")],
          ["Stack Size", String(stack.length)],
        ]}
      />
      {stack.length > 0 && <TagList title="Technology Stack" items={stack} />}
    </div>
  );
}

function MetricGrid({ items }: { items: [string, string][] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-md bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="font-medium break-all">{value}</p>
        </div>
      ))}
    </div>
  );
}

function TagList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="mb-1 font-medium">{title}</p>
      <ul className="list-inside list-disc text-muted-foreground">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function IssuesList({
  issues,
}: {
  issues?: { severity: string; code: string; message: string }[];
}) {
  if (!issues?.length) return null;
  return (
    <div>
      <p className="mb-2 font-medium">Issues ({issues.length})</p>
      <ul className="space-y-1">
        {issues.map((issue) => (
          <li
            key={`${issue.code}-${issue.message}`}
            className="rounded-md bg-destructive/5 px-2 py-1 text-muted-foreground"
          >
            <span className="capitalize text-destructive">{issue.severity}</span>
            {" · "}
            {issue.message}
          </li>
        ))}
      </ul>
    </div>
  );
}

function RecommendationsList({
  items,
}: {
  items?: { priority: string; title: string; description: string }[];
}) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="mb-2 font-medium">Recommendations</p>
      <ul className="space-y-2">
        {items.slice(0, 8).map((rec) => (
          <li key={rec.title} className="text-muted-foreground">
            <span className="font-medium text-foreground">{rec.title}</span>
            {" — "}
            {rec.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EmptyPanel() {
  return <p className="text-sm text-muted-foreground">No report data available.</p>;
}

function truncate(text: string | null | undefined, max: number) {
  if (!text) return "—";
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function formatMs(value?: number | null) {
  if (value == null) return "—";
  return `${Math.round(value)} ms`;
}
