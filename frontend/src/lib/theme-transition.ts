import {
  applyThemeToDocument,
  resolveTheme,
  type ResolvedTheme,
  type ThemePreference,
} from "@/store/ui-store";

const TRANSITION_MS = 280;
const FADE_MS = 140;

function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getResolvedFromDom(): ResolvedTheme {
  return document.documentElement.classList.contains("light") ? "light" : "dark";
}

function runOverlayTransition(apply: () => void): Promise<void> {
  return new Promise((resolve) => {
    const overlay = document.createElement("div");
    overlay.className = "theme-fade-overlay";
    overlay.setAttribute("aria-hidden", "true");
    document.body.appendChild(overlay);

    requestAnimationFrame(() => {
      overlay.classList.add("theme-fade-overlay--visible");

      window.setTimeout(() => {
        apply();

        overlay.classList.remove("theme-fade-overlay--visible");
        overlay.classList.add("theme-fade-overlay--hidden");

        const cleanup = () => {
          overlay.remove();
          resolve();
        };

        overlay.addEventListener("transitionend", cleanup, { once: true });
        window.setTimeout(cleanup, TRANSITION_MS + 50);
      }, FADE_MS);
    });
  });
}

function runViewTransition(apply: () => void): Promise<void> {
  const doc = document as Document & {
    startViewTransition?: (callback: () => void) => { finished: Promise<void> };
  };

  if (!doc.startViewTransition) {
    return runOverlayTransition(apply);
  }

  return doc.startViewTransition(apply).finished.catch(() => {
    apply();
  });
}

export async function applyThemeWithTransition(
  preference: ThemePreference,
  options?: { animate?: boolean },
): Promise<ResolvedTheme> {
  const next = resolveTheme(preference);
  const current = getResolvedFromDom();
  const shouldAnimate = options?.animate !== false && next !== current;

  document.documentElement.dataset.themePreference = preference;

  if (!shouldAnimate || prefersReducedMotion()) {
    applyThemeToDocument(next);
    return next;
  }

  document.documentElement.classList.add("theme-switching");

  try {
    await runViewTransition(() => applyThemeToDocument(next));
  } finally {
    window.setTimeout(() => {
      document.documentElement.classList.remove("theme-switching");
    }, TRANSITION_MS);
  }

  return next;
}

export { TRANSITION_MS };
