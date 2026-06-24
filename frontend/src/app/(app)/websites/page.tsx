"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileSearch, Plus, Upload } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { BulkImportForm } from "@/components/forms/bulk-import-form";
import { WebsiteForm } from "@/components/forms/website-form";
import { WebsiteTable } from "@/components/tables/website-table";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { useBulkCreateAudits, useCreateAudit } from "@/hooks/use-audits";
import { usePermissions } from "@/hooks/use-permissions";
import { toast } from "@/hooks/use-toast";
import { useDeleteWebsite, useWebsites } from "@/hooks/use-websites";
import type { WebsiteStatus } from "@/types";

export default function WebsitesPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<WebsiteStatus | "">("");

  const [formOpen, setFormOpen] = useState(false);
  const [formMode, setFormMode] = useState<"create" | "edit">("create");
  const [editId, setEditId] = useState<string | undefined>();
  const [bulkOpen, setBulkOpen] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);

  const deleteWebsite = useDeleteWebsite();
  const createAudit = useCreateAudit();
  const bulkCreateAudits = useBulkCreateAudits();
  const [auditingIds, setAuditingIds] = useState<Set<string>>(new Set());
  const { canCreateWebsite, canUpdateWebsite, canDeleteWebsite, canRunAudit } =
    usePermissions();

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    const editParam = new URLSearchParams(window.location.search).get("edit");
    if (!editParam) return;
    setFormMode("edit");
    setEditId(editParam);
    setFormOpen(true);
  }, []);

  const { data, isLoading, isFetching } = useWebsites({
    page,
    page_size: 20,
    status: statusFilter,
    search: debouncedSearch,
  });

  const handleAdd = useCallback(() => {
    setFormMode("create");
    setEditId(undefined);
    setFormOpen(true);
  }, []);

  const handleEdit = useCallback((id: string) => {
    setFormMode("edit");
    setEditId(id);
    setFormOpen(true);
  }, []);

  const handleDeleteRequest = useCallback((id: string) => {
    setDeleteTargetId(id);
  }, []);

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTargetId) return;
    try {
      await deleteWebsite.mutateAsync(deleteTargetId);
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(deleteTargetId);
        return next;
      });
      toast({ title: "Website deleted" });
    } catch (err) {
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : "Could not delete website",
        variant: "destructive",
      });
    } finally {
      setDeleteTargetId(null);
    }
  }, [deleteTargetId, deleteWebsite]);

  const handleAudit = useCallback(
    async (id: string) => {
      setAuditingIds((prev) => new Set(prev).add(id));
      try {
        const audit = await createAudit.mutateAsync(id);
        toast({ title: "Audit started" });
        router.push(`/audits/${audit.id}`);
      } catch (err) {
        toast({
          title: "Audit failed",
          description: err instanceof Error ? err.message : "Failed to start audit",
          variant: "destructive",
        });
      } finally {
        setAuditingIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }
    },
    [createAudit, router],
  );

  const handleBulkAudit = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;
    try {
      const result = await bulkCreateAudits.mutateAsync(ids);
      toast({
        title: "Bulk audit queued",
        description: `${result.queued} audit${result.queued === 1 ? "" : "s"} started.`,
      });
      setSelectedIds(new Set());
      router.push("/audits");
    } catch (err) {
      toast({
        title: "Bulk audit failed",
        description: err instanceof Error ? err.message : "Could not queue audits",
        variant: "destructive",
      });
    }
  }, [bulkCreateAudits, router, selectedIds]);

  const handleToggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleToggleSelectAll = useCallback(
    (checked: boolean) => {
      if (!checked) {
        setSelectedIds(new Set());
        return;
      }
      setSelectedIds(new Set((data?.items ?? []).map((item) => item.id)));
    },
    [data?.items],
  );

  const handleStatusChange = useCallback((value: WebsiteStatus | "") => {
    setStatusFilter(value);
    setPage(1);
  }, []);

  return (
    <>
      <PageHeader
        title="Websites"
        description="Manage lead websites and trigger audits"
        actions={
          <>
            {canRunAudit && selectedIds.size > 0 && (
              <Button
                variant="outline"
                onClick={handleBulkAudit}
                disabled={bulkCreateAudits.isPending}
              >
                <FileSearch className="h-4 w-4" />
                Audit selected ({selectedIds.size})
              </Button>
            )}
            {canCreateWebsite && (
              <>
                <Button variant="outline" onClick={() => setBulkOpen(true)}>
                  <Upload className="h-4 w-4" />
                  Bulk Import
                </Button>
                <Button onClick={handleAdd}>
                  <Plus className="h-4 w-4" />
                  Add Website
                </Button>
              </>
            )}
          </>
        }
      />

      <WebsiteTable
        items={data?.items ?? []}
        total={data?.total ?? 0}
        page={data?.page ?? page}
        pageSize={data?.page_size ?? 20}
        totalPages={data?.total_pages ?? 1}
        search={search}
        statusFilter={statusFilter}
        isLoading={isLoading || isFetching}
        onSearchChange={setSearch}
        onStatusChange={handleStatusChange}
        onPageChange={setPage}
        onEdit={handleEdit}
        onDelete={handleDeleteRequest}
        onAudit={handleAudit}
        auditingIds={auditingIds}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
        onToggleSelectAll={handleToggleSelectAll}
        canRunAudit={canRunAudit}
        canUpdate={canUpdateWebsite}
        canDelete={canDeleteWebsite}
        enableSelection={canRunAudit}
      />

      <WebsiteForm
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
        websiteId={editId}
      />

      <BulkImportForm open={bulkOpen} onOpenChange={setBulkOpen} />

      <ConfirmDialog
        open={!!deleteTargetId}
        onOpenChange={(open) => {
          if (!open) setDeleteTargetId(null);
        }}
        title="Delete website?"
        description="This cannot be undone. All associated audit history will remain, but the website record will be removed."
        confirmLabel="Delete"
        destructive
        loading={deleteWebsite.isPending}
        onConfirm={handleDeleteConfirm}
      />
    </>
  );
}
