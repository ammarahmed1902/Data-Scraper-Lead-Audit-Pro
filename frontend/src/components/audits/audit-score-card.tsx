"use client";

import { cn } from "@/lib/utils";

interface AuditScoreCardProps {
  label: string;
  score?: number | null;
  highlight?: boolean;
}

export function AuditScoreCard({ label, score, highlight }: AuditScoreCardProps) {
  const value = score != null ? Math.round(score) : null;
  const color =
    value == null
      ? "text-muted-foreground"
      : value >= 80
        ? "text-green-600"
        : value >= 50
          ? "text-yellow-600"
          : "text-destructive";

  return (
    <div
      className={cn(
        "glass-card rounded-lg border border-border p-4 text-center",
        highlight && "ring-1 ring-primary/30",
      )}
    >
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-3xl font-bold", color)}>{value ?? "—"}</p>
    </div>
  );
}
