/**
 * Structured client-side API request logging (development only).
 */

const PREFIX = "[LeadAudit API]";

function isDev(): boolean {
  return process.env.NODE_ENV === "development";
}

export interface ApiLogContext {
  step: string;
  method?: string;
  url?: string;
  status?: number;
  durationMs?: number;
  error?: string;
  detail?: unknown;
}

export function logApi(ctx: ApiLogContext): void {
  if (!isDev()) return;
  const parts = [
    `${PREFIX} ${ctx.step}`,
    ctx.method && ctx.url ? `${ctx.method} ${ctx.url}` : ctx.url,
    ctx.status != null ? `status=${ctx.status}` : null,
    ctx.durationMs != null ? `${ctx.durationMs}ms` : null,
    ctx.error ? `error=${ctx.error}` : null,
  ].filter(Boolean);
  if (ctx.error) {
    console.error(parts.join(" | "), ctx.detail ?? "");
  } else {
    console.warn(parts.join(" | "), ctx.detail ?? "");
  }
}
