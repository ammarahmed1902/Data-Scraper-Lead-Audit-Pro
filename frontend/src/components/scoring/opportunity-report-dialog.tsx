"use client";

import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useOpportunityReport } from "@/hooks/use-scoring";

interface OpportunityReportDialogProps {
  leadId: string | null;
  onClose: () => void;
}

export function OpportunityReportDialog({ leadId, onClose }: OpportunityReportDialogProps) {
  const { data, isLoading } = useOpportunityReport(leadId);

  return (
    <Dialog open={!!leadId} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] max-w-lg overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{data?.business_name ?? "Opportunity Report"}</DialogTitle>
          <DialogDescription>
            {data
              ? `${data.classification.toUpperCase()} lead · composite ${data.composite_score != null ? Math.round(data.composite_score) : "—"}`
              : "Detected sales opportunities"}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center gap-2 py-8 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading report...
          </div>
        ) : !data?.opportunities?.length ? (
          <p className="text-sm text-muted-foreground">No opportunities detected.</p>
        ) : (
          <ul className="space-y-3">
            {data.opportunities.map((opp) => (
              <li
                key={`${opp.code}-${opp.title}`}
                className="rounded-md border border-border/50 p-3 text-sm"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{opp.title}</span>
                  <span className="text-xs capitalize text-muted-foreground">{opp.severity}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground capitalize">
                  {opp.category.replace(/_/g, " ")}
                </p>
                <p className="mt-1 text-muted-foreground">{opp.description}</p>
              </li>
            ))}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  );
}
