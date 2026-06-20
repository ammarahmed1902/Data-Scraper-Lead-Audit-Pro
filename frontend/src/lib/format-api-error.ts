/**
 * Extract a user-facing message from API error payloads.
 */

type ErrorPayload = {
  message?: string;
  detail?: string | { msg?: string }[] | Record<string, unknown>;
  success?: boolean;
  error_type?: string;
  source?: string;
  debug?: { type?: string; error?: string };
};

function detailToString(detail: ErrorPayload["detail"]): string | null {
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "object" && first && "msg" in first && typeof first.msg === "string") {
      return first.msg;
    }
  }
  return null;
}

export function formatApiError(status: number, payload?: unknown, fallback?: string): string {
  const body = (payload ?? {}) as ErrorPayload;

  const detailText = detailToString(body.detail);
  if (detailText) {
    return detailText;
  }

  if (typeof body.message === "string" && body.message.trim()) {
    const message = body.message.trim();
    if (message !== "An unexpected server error occurred.") {
      return message;
    }
  }

  if (body.debug?.error) {
    return body.debug.error;
  }

  if (status === 400) return "Invalid request. Check industry keyword and country.";
  if (status === 401) return "Your session expired. Please sign in again.";
  if (status === 403) return "You do not have permission to perform this action.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status === 502) return "Cannot reach the API server. Ensure the backend is running on port 8000.";
  if (status === 503) {
    return "Lead discovery is temporarily unavailable. Check database migrations and background workers.";
  }
  if (status >= 500) {
    return fallback ?? "Server error. Please try again or check backend logs.";
  }

  return fallback ?? `Request failed with status ${status}`;
}

export function formatDiscoveryError(status: number, payload?: unknown, fallback?: string): string {
  const message = formatApiError(status, payload, fallback);
  const body = (payload ?? {}) as ErrorPayload;
  const parts = [message];

  if (body.error_type) {
    parts.push(`Error type: ${body.error_type}`);
  }
  if (body.source) {
    parts.push(`Source: ${body.source}`);
  }

  return parts.join(" · ");
}
