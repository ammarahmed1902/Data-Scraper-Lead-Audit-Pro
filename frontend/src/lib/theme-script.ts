export const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem('lap-ui');
    var preference = 'system';
    if (stored) {
      var parsed = JSON.parse(stored);
      preference = parsed.state && parsed.state.theme ? parsed.state.theme : 'system';
    }
    var resolved = preference;
    if (preference === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    var root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolved);
    root.style.colorScheme = resolved;
    root.dataset.themePreference = preference;
  } catch (e) {}
})();
`.trim();
