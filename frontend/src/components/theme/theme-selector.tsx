"use client";

import { Monitor, Moon, Sun } from "lucide-react";

import { ThemeToggle } from "@/components/theme/theme-toggle";
import { useTheme } from "@/hooks/use-theme";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { type ThemePreference } from "@/store/ui-store";

const themes: {
  value: ThemePreference;
  label: string;
  description: string;
  icon: typeof Sun;
}[] = [
  {
    value: "light",
    label: "Light",
    description: "Clean white backgrounds for a modern SaaS look.",
    icon: Sun,
  },
  {
    value: "dark",
    label: "Dark",
    description: "High-contrast dark mode optimized for long sessions.",
    icon: Moon,
  },
  {
    value: "system",
    label: "System",
    description: "Automatically match your device appearance.",
    icon: Monitor,
  },
];

export function ThemeSelector() {
  const { theme, isTransitioning, setTheme } = useTheme();

  return (
    <Card className="glass-card overflow-hidden">
      <CardHeader>
        <CardTitle>Appearance</CardTitle>
        <CardDescription>
          Choose how Lead Audit Pro looks. Changes fade in smoothly — no page reload required.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className={cn(
            "grid gap-3 sm:grid-cols-3 transition-opacity duration-300",
            isTransitioning && "pointer-events-none opacity-90",
          )}
          aria-busy={isTransitioning}
        >
          {themes.map(({ value, label, description, icon: Icon }) => {
            const selected = theme === value;
            return (
              <button
                key={value}
                type="button"
                onClick={() => void setTheme(value)}
                disabled={isTransitioning || selected}
                aria-pressed={selected}
                className={cn(
                  "relative flex flex-col items-start gap-3 rounded-xl border p-4 text-left",
                  "transition-all duration-300 ease-out",
                  selected
                    ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/20"
                    : "border-border bg-card hover:border-primary/30 hover:bg-accent/40 hover:shadow-sm",
                  isTransitioning && !selected && "opacity-60",
                )}
              >
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-lg transition-colors duration-300",
                    selected ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground",
                  )}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium">{label}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{description}</p>
                </div>
                {selected && (
                  <span className="absolute right-3 top-3 h-2 w-2 rounded-full bg-primary animate-pulse-subtle" />
                )}
              </button>
            );
          })}
        </div>
        <div className="flex items-center justify-between rounded-lg border border-border/60 bg-muted/30 px-4 py-3">
          <span className="text-sm text-muted-foreground">
            {isTransitioning ? "Applying theme…" : "Quick toggle"}
          </span>
          <ThemeToggle variant="full" className="h-9 px-3" />
        </div>
      </CardContent>
    </Card>
  );
}
