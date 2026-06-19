"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateWebsite, useUpdateWebsite } from "@/hooks/use-websites";
import { websiteService } from "@/services/website-service";
import type { Website, WebsiteStatus } from "@/types";

const STATUSES: { value: WebsiteStatus; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "queued", label: "Queued" },
  { value: "auditing", label: "Auditing" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "archived", label: "Archived" },
];

interface WebsiteFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  mode: "create" | "edit";
  websiteId?: string;
  onSuccess?: () => void;
}

export function WebsiteForm({
  open,
  onOpenChange,
  mode,
  websiteId,
  onSuccess,
}: WebsiteFormProps) {
  const createWebsite = useCreateWebsite();
  const updateWebsite = useUpdateWebsite();

  const [url, setUrl] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [industry, setIndustry] = useState("");
  const [notes, setNotes] = useState("");
  const [tags, setTags] = useState("");
  const [status, setStatus] = useState<WebsiteStatus>("pending");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;

    if (mode === "create") {
      setUrl("");
      setCompanyName("");
      setContactName("");
      setContactEmail("");
      setContactPhone("");
      setIndustry("");
      setNotes("");
      setTags("");
      setStatus("pending");
      setError(null);
      return;
    }

    if (!websiteId) return;

    setLoading(true);
    websiteService
      .get(websiteId)
      .then((website: Website) => {
        setUrl(website.url);
        setCompanyName(website.company_name ?? "");
        setContactName(website.contact_name ?? "");
        setContactEmail(website.contact_email ?? "");
        setContactPhone(website.contact_phone ?? "");
        setIndustry(website.industry ?? "");
        setNotes(website.notes ?? "");
        setTags(website.tags?.join(", ") ?? "");
        setStatus(website.status);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [open, mode, websiteId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const tagsList = tags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    const payload = {
      url,
      company_name: companyName || undefined,
      contact_name: contactName || undefined,
      contact_email: contactEmail || undefined,
      contact_phone: contactPhone || undefined,
      industry: industry || undefined,
      notes: notes || undefined,
      tags: tagsList.length > 0 ? tagsList : undefined,
    };

    try {
      if (mode === "create") {
        await createWebsite.mutateAsync(payload);
      } else if (websiteId) {
        await updateWebsite.mutateAsync({
          id: websiteId,
          data: { ...payload, status },
        });
      }
      onOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save website");
    }
  }

  const isPending = createWebsite.isPending || updateWebsite.isPending || loading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "Add Website" : "Edit Website"}</DialogTitle>
          <DialogDescription>
            {mode === "create"
              ? "Enter a website URL and optional lead details."
              : "Update website details and status."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <div className="space-y-2">
            <Label htmlFor="url">Website URL *</Label>
            <Input
              id="url"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              disabled={isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="company">Company Name</Label>
            <Input
              id="company"
              placeholder="Acme Corp"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              disabled={isPending}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="contact">Contact Name</Label>
              <Input
                id="contact"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                disabled={isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                disabled={isPending}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="email">Contact Email</Label>
              <Input
                id="email"
                type="email"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                disabled={isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Contact Phone</Label>
              <Input
                id="phone"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                disabled={isPending}
              />
            </div>
          </div>

          {mode === "edit" && (
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as WebsiteStatus)}>
                <SelectTrigger disabled={isPending}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUSES.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              placeholder="saas, b2b, priority"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              disabled={isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={isPending}
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? "Saving..." : mode === "create" ? "Add Website" : "Save Changes"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
