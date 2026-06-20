"use client";

import { Loader2 } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { BusinessEnrichment } from "@/types";

interface EnrichmentDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  enrichment: BusinessEnrichment | undefined;
  isLoading?: boolean;
  businessName?: string;
}

export function EnrichmentDetailDialog({
  open,
  onOpenChange,
  enrichment,
  isLoading,
  businessName,
}: EnrichmentDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {enrichment?.company_name ?? businessName ?? "Business Enrichment"}
          </DialogTitle>
          <DialogDescription>
            Extracted website data · status: {enrichment?.status ?? "—"}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading enrichment data...
          </div>
        ) : !enrichment ? (
          <p className="text-sm text-muted-foreground">No enrichment data available.</p>
        ) : enrichment.status === "failed" ? (
          <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {enrichment.error_message ?? "Enrichment failed"}
          </p>
        ) : (
          <div className="space-y-5 text-sm">
            {enrichment.business_description && (
              <Section title="Description">{enrichment.business_description}</Section>
            )}

            {enrichment.cms_platform && (
              <Section title="CMS / Platform">
                <span className="capitalize">{enrichment.cms_platform}</span>
                {enrichment.technology_stack && enrichment.technology_stack.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {enrichment.technology_stack.map((tech) => (
                      <span
                        key={tech}
                        className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </Section>
            )}

            {(enrichment.email_addresses?.length ?? 0) > 0 && (
              <Section title="Emails">
                {enrichment.email_addresses!.join(", ")}
              </Section>
            )}

            {(enrichment.phone_numbers?.length ?? 0) > 0 && (
              <Section title="Phones">
                {enrichment.phone_numbers!.join(", ")}
              </Section>
            )}

            {(enrichment.services?.length ?? 0) > 0 && (
              <Section title="Services">
                <ul className="list-inside list-disc space-y-1">
                  {enrichment.services!.map((service) => (
                    <li key={service}>{service}</li>
                  ))}
                </ul>
              </Section>
            )}

            {(enrichment.team_members?.length ?? 0) > 0 && (
              <Section title="Team">
                <ul className="space-y-1">
                  {enrichment.team_members!.map((member) => (
                    <li key={`${member.name}-${member.title}`}>
                      <span className="font-medium">{member.name}</span>
                      {member.title && (
                        <span className="text-muted-foreground"> · {member.title}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {enrichment.about_us_content && (
              <Section title="About Us">
                <p className="whitespace-pre-wrap text-muted-foreground">
                  {enrichment.about_us_content.slice(0, 1500)}
                  {enrichment.about_us_content.length > 1500 ? "…" : ""}
                </p>
              </Section>
            )}

            {(enrichment.pages_crawled?.length ?? 0) > 0 && (
              <Section title="Pages Crawled">
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {enrichment.pages_crawled!.map((url) => (
                    <li key={url} className="truncate">
                      {url}
                    </li>
                  ))}
                </ul>
              </Section>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-1 font-medium">{title}</h3>
      <div className="text-muted-foreground">{children}</div>
    </div>
  );
}
