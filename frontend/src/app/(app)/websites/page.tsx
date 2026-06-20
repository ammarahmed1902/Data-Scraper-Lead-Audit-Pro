"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Upload } from "lucide-react";

import { PageHeader } from "@/components/dashboard/page-header";
import { BulkImportForm } from "@/components/forms/bulk-import-form";
import { WebsiteForm } from "@/components/forms/website-form";
import { WebsiteTable } from "@/components/tables/website-table";
import { Button } from "@/components/ui/button";
import { useCreateAudit } from "@/hooks/use-audits";
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

  const deleteWebsite = useDeleteWebsite();
  const createAudit = useCreateAudit();
  const [auditingIds, setAuditingIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

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

  const handleDelete = useCallback(
    async (id: string) => {
      if (!confirm("Delete this website? This cannot be undone.")) return;
      try {
        await deleteWebsite.mutateAsync(id);
      } catch (err) {
        alert(err instanceof Error ? err.message : "Failed to delete website");
      }
    },
    [deleteWebsite],
  );

  const handleAudit = useCallback(
    async (id: string) => {
      setAuditingIds((prev) => new Set(prev).add(id));
      try {
        const audit = await createAudit.mutateAsync(id);
        router.push(`/audits/${audit.id}`);
      } catch (err) {
        alert(err instanceof Error ? err.message : "Failed to start audit");
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
            <Button variant="outline" onClick={() => setBulkOpen(true)}>
              <Upload className="h-4 w-4" />
              Bulk Import
            </Button>
            <Button onClick={handleAdd}>
              <Plus className="h-4 w-4" />
              Add Website
            </Button>
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
        onDelete={handleDelete}
        onAudit={handleAudit}
        auditingIds={auditingIds}
      />

      <WebsiteForm
        open={formOpen}
        onOpenChange={setFormOpen}
        mode={formMode}
        websiteId={editId}
      />

      <BulkImportForm open={bulkOpen} onOpenChange={setBulkOpen} />
    </>
  );
}
