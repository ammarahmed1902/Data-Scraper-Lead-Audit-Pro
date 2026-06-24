"use client";

import { X } from "lucide-react";

import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export function Toaster() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2"
      aria-live="polite"
    >
      {toasts.map((item) => (
        <div
          key={item.id}
          className={cn(
            "glass-card flex items-start gap-3 rounded-lg border p-4 shadow-elevated",
            item.variant === "destructive"
              ? "border-destructive/40 bg-destructive/10"
              : "border-border bg-card",
          )}
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">{item.title}</p>
            {item.description && (
              <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => dismiss(item.id)}
            className="rounded-md p-1 text-muted-foreground hover:text-foreground"
            aria-label="Dismiss notification"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
