/**
 * DOM attributes injected by browser extensions before React hydrates.
 * These are not present in server-rendered HTML and cause hydration mismatches.
 *
 * Common sources:
 * - bis_skin_checked: VPN / antivirus (Urban VPN, Bitdefender, SpeakIt, etc.)
 * - cz-shortcut-listen: ColorZilla
 * - data-gr-*: Grammarly
 * - fdprocessedid: password managers / form fillers
 */
export const BROWSER_EXTENSION_ATTRIBUTES = [
  "bis_skin_checked",
  "bis_register",
  "bis_use",
  "cz-shortcut-listen",
  "data-new-gr-c-s-check-loaded",
  "data-gr-ext-installed",
  "data-gr-ext-disabled",
  "data-lt-installed",
  "data-dynamic-id",
  "fdprocessedid",
] as const;
