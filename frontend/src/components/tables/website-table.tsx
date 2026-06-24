"use client";

import Link from "next/link";
import { ExternalLink, FileSearch, Pencil, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { WebsiteListItem } from "@/services/website-service";
import type { WebsiteStatus } from "@/types";

const STATUS_VARIANT: Record<
  WebsiteStatus,
  "default" | "secondary" | "success" | "warning" | "destructive" | "outline"
> = {
  pending: "secondary",
  queued: "default",
  auditing: "warning",
  completed: "success",
  failed: "destructive",
  archived: "outline",
};

interface WebsiteTableProps {
  items: WebsiteListItem[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  search: string;
  statusFilter: WebsiteStatus | "";
  isLoading?: boolean;
  onSearchChange: (value: string) => void;
  onStatusChange: (value: WebsiteStatus | "") => void;
  onPageChange: (page: number) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onAudit: (id: string) => void;
  auditingIds?: Set<string>;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
  onToggleSelectAll?: (checked: boolean) => void;
  canRunAudit?: boolean;
  canUpdate?: boolean;
  canDelete?: boolean;
  enableSelection?: boolean;
}

export function WebsiteTable({
  items,
  total,
  page,
  pageSize,
  totalPages,
  search,
  statusFilter,
  isLoading,
  onSearchChange,
  onStatusChange,
  onPageChange,
  onEdit,
  onDelete,
  onAudit,
  auditingIds,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  canRunAudit = true,
  canUpdate = true,
  canDelete = true,
  enableSelection = false,
}: WebsiteTableProps) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  const allSelected =
    items.length > 0 && items.every((website) => selectedIds?.has(website.id));
  const columnCount =
    5 + (enableSelection ? 1 : 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Input
          placeholder="Search URL, domain, company, contact..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="sm:max-w-sm"
        />
        <Select
          value={statusFilter || "all"}
          onValueChange={(v) => onStatusChange(v === "all" ? "" : (v as WebsiteStatus))}
        >
          <SelectTrigger className="w-full sm:w-[180px]">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="auditing">Auditing</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="glass-card overflow-hidden">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  {enableSelection && (
                    <th className="px-4 py-3 text-left font-medium w-10">
                      <input
                        type="checkbox"
                        checked={allSelected}
                        onChange={(e) => onToggleSelectAll?.(e.target.checked)}
                        aria-label="Select all websites on this page"
                        className="h-4 w-4 rounded border-border"
                      />
                    </th>
                  )}
                  <th className="px-4 py-3 text-left font-medium">Website</th>
                  <th className="px-4 py-3 text-left font-medium hidden md:table-cell">
                    Company
                  </th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                  <th className="px-4 py-3 text-left font-medium hidden lg:table-cell">
                    Last Audited
                  </th>
                  <th className="px-4 py-3 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={columnCount} className="px-4 py-12 text-center text-muted-foreground">
                      Loading websites...
                    </td>
                  </tr>
                ) : items.length === 0 ? (
                  <tr>
                    <td colSpan={columnCount} className="px-4 py-12 text-center text-muted-foreground">
                      No websites found
                    </td>
                  </tr>
                ) : (
                  items.map((website) => (
                    <tr
                      key={website.id}
                      className="border-b border-border/50 hover:bg-muted/20 transition-colors"
                    >
                      {enableSelection && (
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selectedIds?.has(website.id) ?? false}
                            onChange={() => onToggleSelect?.(website.id)}
                            aria-label={`Select ${website.domain}`}
                            className="h-4 w-4 rounded border-border"
                          />
                        </td>
                      )}
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-0.5">
                          <Link
                            href={`/websites/${website.id}`}
                            className="font-medium text-primary hover:underline inline-flex items-center gap-1 w-fit"
                          >
                            {website.domain}
                          </Link>
                          <a
                            href={website.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-muted-foreground truncate max-w-[200px] inline-flex items-center gap-1 hover:text-foreground"
                          >
                            {website.url}
                            <ExternalLink className="h-3 w-3 shrink-0" />
                          </a>
                        </div>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell text-muted-foreground">
                        {website.company_name || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={STATUS_VARIANT[website.status]}>
                          {website.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 hidden lg:table-cell text-muted-foreground">
                        {website.last_audited_at
                          ? new Date(website.last_audited_at).toLocaleDateString()
                          : "Never"}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          {canRunAudit && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onAudit(website.id)}
                              disabled={auditingIds?.has(website.id)}
                              aria-label="Run audit"
                              title="Run audit"
                            >
                              <FileSearch className="h-4 w-4" />
                            </Button>
                          )}
                          {canUpdate && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onEdit(website.id)}
                              aria-label="Edit website"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          )}
                          {canDelete && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => onDelete(website.id)}
                              aria-label="Delete website"
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {total > 0 && (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between text-sm text-muted-foreground">
          <span>
            Showing {start}–{end} of {total}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1 || isLoading}
            >
              Previous
            </Button>
            <span className="px-2">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
