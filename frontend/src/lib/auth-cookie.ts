const AUTH_COOKIE = "lap-authenticated";
const MAX_AGE = 60 * 60 * 24 * 7; // 7 days

export function setAuthCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=true; path=/; max-age=${MAX_AGE}; SameSite=Lax`;
}

export function clearAuthCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0`;
}

export function hasAuthCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie.includes(`${AUTH_COOKIE}=true`);
}

export { AUTH_COOKIE };
