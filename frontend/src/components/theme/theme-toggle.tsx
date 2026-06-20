"use client";

import { Monitor, Moon, Sun } from "lucide-react";

import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { type ThemePreference } from "@/store/ui-store";

interface ThemeToggleProps {
  variant?: "icon" | "full";
  className?: string;
}

const options: { value: ThemePreference; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

export function ThemeToggle({ variant = "icon", className }: ThemeToggleProps) {
  const { theme, hydrated, isTransitioning, setTheme } = useTheme();

  const ActiveIcon =
    theme === "light" ? Sun : theme === "dark" ? Moon : Monitor;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size={variant === "icon" ? "icon" : "default"}
          className={cn(
            variant === "full" && "w-full justify-start gap-2",
            isTransitioning && "opacity-80",
            className,
          )}
          aria-label="Toggle theme"
          aria-busy={isTransitioning}
          disabled={isTransitioning}
        >
          <ActiveIcon
            className={cn(
              "h-4 w-4 transition-transform duration-300",
              isTransitioning && "scale-90 opacity-70",
            )}
          />
          {variant === "full" && (
            <span>
              {hydrated
                ? options.find((o) => o.value === theme)?.label ?? "Theme"
                : "Theme"}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuLabel>Theme</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup
          value={theme}
          onValueChange={(value) => void setTheme(value as ThemePreference)}
        >
          {options.map(({ value, label, icon: Icon }) => (
            <DropdownMenuRadioItem
              key={value}
              value={value}
              className="gap-2"
              disabled={isTransitioning}
            >
              <Icon className="h-4 w-4" />
              {label}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
