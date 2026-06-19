"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useBulkImportWebsites } from "@/hooks/use-websites";
import type { Website } from "@/types";

interface BulkImportFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

function parseBulkInput(text: string): Partial<Website>[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(",").map((p) => p.trim());
      if (parts.length === 1) {
        return { url: parts[0] };
      }
      return {
        url: parts[0],
        company_name: parts[1] || undefined,
        contact_name: parts[2] || undefined,
        contact_email: parts[3] || undefined,
      };
    });
}

export function BulkImportForm({ open, onOpenChange, onSuccess }: BulkImportFormProps) {
  const bulkImport = useBulkImportWebsites();
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    created: number;
    skipped: number;
    errors: { index: string; url: string; error: string }[];
  } | null>(null);

  function handleClose(nextOpen: boolean) {
    if (!nextOpen) {
      setInput("");
      setError(null);
      setResult(null);
    }
    onOpenChange(nextOpen);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);

    const websites = parseBulkInput(input);
    if (websites.length === 0) {
      setError("Enter at least one URL");
      return;
    }
    if (websites.length > 500) {
      setError("Maximum 500 URLs per import");
      return;
    }

    try {
      const res = await bulkImport.mutateAsync(websites);
      setResult(res);
      if (res.created > 0) {
        onSuccess?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Bulk import failed");
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Bulk Import Websites</DialogTitle>
          <DialogDescription>
            Paste one URL per line, or CSV: url, company, contact, email. Up to 500
            URLs per import. Duplicate domains are skipped.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          {result && (
            <div className="rounded-md bg-muted/50 px-3 py-2 text-sm space-y-1">
              <p>
                <span className="font-medium text-success">{result.created}</span> created,{" "}
                <span className="font-medium text-warning">{result.skipped}</span> skipped
              </p>
              {result.errors.length > 0 && (
                <ul className="mt-2 max-h-32 overflow-y-auto text-destructive text-xs space-y-1">
                  {result.errors.map((err, i) => (
                    <li key={i}>
                      Line {Number(err.index) + 1}: {err.url} — {err.error}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="bulk-input">URLs</Label>
            <Textarea
              id="bulk-input"
              rows={10}
              placeholder={`https://example.com\nhttps://acme.com,Acme Corp,John Doe,john@acme.com`}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={bulkImport.isPending}
            />
            <p className="text-xs text-muted-foreground">
              {parseBulkInput(input).length} URL(s) detected
            </p>
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={bulkImport.isPending}
            >
              {result ? "Close" : "Cancel"}
            </Button>
            {!result && (
              <Button type="submit" disabled={bulkImport.isPending}>
                {bulkImport.isPending ? "Importing..." : "Import"}
              </Button>
            )}
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
