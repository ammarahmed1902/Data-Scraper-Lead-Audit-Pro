/**
 * Inline script to apply persisted sidebar width before React hydrates (prevents layout flash).
 */
export const sidebarInitScript = `
(function () {
  try {
    var stored = localStorage.getItem('lap-dashboard');
    if (!stored) {
      document.documentElement.style.setProperty('--sidebar-width', '16rem');
      return;
    }
    var parsed = JSON.parse(stored);
    var collapsed = parsed.state && parsed.state.sidebarCollapsed === true;
    document.documentElement.style.setProperty('--sidebar-width', collapsed ? '4.5rem' : '16rem');
  } catch (e) {
    document.documentElement.style.setProperty('--sidebar-width', '16rem');
  }
})();
`.trim();

export const SIDEBAR_WIDTH_EXPANDED = "16rem";
export const SIDEBAR_WIDTH_COLLAPSED = "4.5rem";
