/**
 * Download a file from an authenticated API endpoint.
 */
export async function downloadAuthenticatedFile(
  endpoint: string,
  filename: string,
): Promise<void> {
  const { useAuthStore } = await import("@/store/auth-store");
  const token = useAuthStore.getState().tokens?.access_token;

  const response = await fetch(endpoint, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error(`Download failed (${response.status})`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
