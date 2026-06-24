"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { DiscoveredLeadsTable } from "@/components/discovery/discovered-leads-table";
import { EnrichmentDetailDialog } from "@/components/discovery/enrichment-detail-dialog";
import { DiscoverySearchForm } from "@/components/discovery/discovery-search-form";
import { DiscoverySearchHistory } from "@/components/discovery/discovery-search-history";
import { PageHeader } from "@/components/dashboard/page-header";
import { toast } from "@/hooks/use-toast";
import {
  useDiscoveredLeads,
  useDiscoverySearch,
  useDiscoverySearches,
  useImportDiscoveredLead,
} from "@/hooks/use-discovery";
import {
  useCreateAuditForLead,
} from "@/hooks/use-audits";
import {
  useEnrichLead,
  useEnrichSearch,
  useEnrichmentJob,
  useEnrichmentsList,
  useLeadEnrichment,
} from "@/hooks/use-enrichment";
import {
  useRankedLeads,
  useScoreSearch,
} from "@/hooks/use-scoring";
import type { EnrichmentStatus, LeadClassification } from "@/types";

export default function DiscoveryPage() {
  const [selectedSearchId, setSelectedSearchId] = useState<string | null>(null);
  const [leadsPage, setLeadsPage] = useState(1);
  const [importingId, setImportingId] = useState<string | null>(null);
  const [enrichingId, setEnrichingId] = useState<string | null>(null);
  const [auditingId, setAuditingId] = useState<string | null>(null);
  const [bulkJobId, setBulkJobId] = useState<string | null>(null);
  const [viewLeadId, setViewLeadId] = useState<string | null>(null);
  const [viewBusinessName, setViewBusinessName] = useState("");

  const { data: searchesData, isLoading: searchesLoading } = useDiscoverySearches(1, 15);
  const { data: activeSearch } = useDiscoverySearch(selectedSearchId, true);
  const { data: leadsData, isLoading: leadsLoading } = useDiscoveredLeads(
    selectedSearchId,
    leadsPage,
  );
  const { data: enrichmentsData, refetch: refetchEnrichments } = useEnrichmentsList(1);
  const { data: bulkJob } = useEnrichmentJob(bulkJobId, true);
  const { data: viewEnrichment, isLoading: viewEnrichmentLoading } = useLeadEnrichment(
    viewLeadId,
    !!viewLeadId,
  );

  const importLead = useImportDiscoveredLead();
  const enrichLead = useEnrichLead();
  const enrichSearch = useEnrichSearch();
  const auditLead = useCreateAuditForLead();
  const scoreSearch = useScoreSearch();
  const { data: rankedData, refetch: refetchRanked } = useRankedLeads({
    search_id: selectedSearchId ?? undefined,
    page: 1,
    enabled: !!selectedSearchId && activeSearch?.status === "completed",
  });

  const enrichmentStatusMap = useMemo(() => {
    const map: Record<string, EnrichmentStatus> = {};
    for (const item of enrichmentsData?.items ?? []) {
      map[item.lead_id] = item.status;
    }
    return map;
  }, [enrichmentsData]);

  const leadScoreMap = useMemo(() => {
    const map: Record<string, { classification: LeadClassification; composite: number }> = {};
    for (const item of rankedData?.items ?? []) {
      map[item.lead.id] = {
        classification: item.score.classification,
        composite: item.score.composite_score ?? 0,
      };
    }
    return map;
  }, [rankedData]);

  const handleSearchStarted = useCallback((searchId: string) => {
    setSelectedSearchId(searchId);
    setLeadsPage(1);
  }, []);

  const handleSelectSearch = useCallback((id: string) => {
    setSelectedSearchId(id);
    setLeadsPage(1);
  }, []);

  const handleImport = useCallback(
    async (leadId: string) => {
      setImportingId(leadId);
      try {
        await importLead.mutateAsync(leadId);
      } catch (err) {
        toast({
          title: "Import failed",
          description: err instanceof Error ? err.message : "Could not import lead",
          variant: "destructive",
        });
      } finally {
        setImportingId(null);
      }
    },
    [importLead],
  );

  const handleEnrich = useCallback(
    async (leadId: string) => {
      setEnrichingId(leadId);
      try {
        await enrichLead.mutateAsync(leadId);
        await refetchEnrichments();
      } catch (err) {
        toast({
          title: "Enrichment failed",
          description: err instanceof Error ? err.message : "Could not enrich lead",
          variant: "destructive",
        });
      } finally {
        setEnrichingId(null);
      }
    },
    [enrichLead, refetchEnrichments],
  );

  const handleEnrichAll = useCallback(async () => {
    if (!selectedSearchId) return;
    try {
      const result = await enrichSearch.mutateAsync(selectedSearchId);
      setBulkJobId(result.job_id);
      await refetchEnrichments();
    } catch (err) {
      toast({
        title: "Bulk enrichment failed",
        description: err instanceof Error ? err.message : "Could not start bulk enrichment",
        variant: "destructive",
      });
    }
  }, [selectedSearchId, enrichSearch, refetchEnrichments]);

  const handleViewEnrichment = useCallback((leadId: string, businessName: string) => {
    setViewLeadId(leadId);
    setViewBusinessName(businessName);
  }, []);

  const handleAudit = useCallback(
    async (leadId: string) => {
      setAuditingId(leadId);
      try {
        const audit = await auditLead.mutateAsync({ leadId, autoImport: true });
        window.location.href = `/audits/${audit.id}`;
      } catch (err) {
        toast({
          title: "Audit failed",
          description: err instanceof Error ? err.message : "Could not start audit",
          variant: "destructive",
        });
      } finally {
        setAuditingId(null);
      }
    },
    [auditLead],
  );

  const handleScoreAll = useCallback(async () => {
    if (!selectedSearchId) return;
    try {
      await scoreSearch.mutateAsync(selectedSearchId);
      await refetchRanked();
    } catch (err) {
      toast({
        title: "Scoring failed",
        description: err instanceof Error ? err.message : "Could not score leads",
        variant: "destructive",
      });
    }
  }, [selectedSearchId, scoreSearch, refetchRanked]);

  const enrichingAll =
    enrichSearch.isPending ||
    bulkJob?.status === "pending" ||
    bulkJob?.status === "running";

  useEffect(() => {
    if (bulkJob?.status === "completed" || bulkJob?.status === "failed") {
      void refetchEnrichments();
    }
  }, [bulkJob?.status, refetchEnrichments]);

  return (
    <>
      <PageHeader
        title="Lead Discovery"
        description="Find businesses by industry and location, then enrich with website data"
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <DiscoverySearchForm onSearchStarted={handleSearchStarted} />
          <DiscoveredLeadsTable
            search={activeSearch}
            leads={leadsData?.items ?? []}
            isLoading={leadsLoading}
            onImport={handleImport}
            importingId={importingId}
            onEnrich={handleEnrich}
            onEnrichAll={handleEnrichAll}
            onScoreAll={handleScoreAll}
            scoringAll={scoreSearch.isPending}
            onAudit={handleAudit}
            auditingId={auditingId}
            enrichingId={enrichingId}
            enrichingAll={enrichingAll}
            enrichmentStatusMap={enrichmentStatusMap}
            leadScoreMap={leadScoreMap}
            onViewEnrichment={handleViewEnrichment}
            page={leadsData?.page ?? leadsPage}
            totalPages={leadsData?.total_pages ?? 1}
            onPageChange={setLeadsPage}
          />
        </div>
        <div>
          <DiscoverySearchHistory
            searches={searchesData?.items ?? []}
            selectedId={selectedSearchId}
            onSelect={handleSelectSearch}
            isLoading={searchesLoading}
          />
        </div>
      </div>

      <EnrichmentDetailDialog
        open={!!viewLeadId}
        onOpenChange={(open) => {
          if (!open) setViewLeadId(null);
        }}
        enrichment={viewEnrichment}
        isLoading={viewEnrichmentLoading}
        businessName={viewBusinessName}
      />
    </>
  );
}
