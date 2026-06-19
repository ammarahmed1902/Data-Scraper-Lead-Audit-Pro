/**
 * Design token constants — mirrors CSS custom properties in globals.css.
 * Use for programmatic styling (charts, canvas, Framer Motion).
 */

export const colors = {
  background: "hsl(240 10% 3.9%)",
  foreground: "hsl(0 0% 98%)",
  primary: "hsl(262 83% 58%)",
  primaryForeground: "hsl(0 0% 100%)",
  muted: "hsl(240 5% 14%)",
  mutedForeground: "hsl(240 5% 64.9%)",
  success: "hsl(142 71% 45%)",
  warning: "hsl(38 92% 50%)",
  destructive: "hsl(0 72% 51%)",
  border: "hsl(240 5% 17%)",
  card: "hsl(240 10% 6%)",
} as const;

export const spacing = {
  xs: "0.25rem",
  sm: "0.5rem",
  md: "1rem",
  lg: "1.5rem",
  xl: "2rem",
  "2xl": "3rem",
  "3xl": "4rem",
} as const;

export const typography = {
  fontFamily: {
    sans: "var(--font-geist-sans)",
    mono: "var(--font-geist-mono)",
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    base: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem",
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
} as const;

export const shadows = {
  glass: "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
  card: "0 1px 3px 0 rgba(0, 0, 0, 0.3)",
  elevated: "0 10px 40px -10px rgba(0, 0, 0, 0.5)",
  glow: "0 0 20px rgba(139, 92, 246, 0.15)",
} as const;

export const borderRadius = {
  sm: "0.375rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  full: "9999px",
} as const;

export const animation = {
  duration: {
    fast: 150,
    normal: 300,
    slow: 500,
  },
  easing: {
    default: [0.4, 0, 0.2, 1] as const,
    spring: [0.34, 1.56, 0.64, 1] as const,
  },
} as const;
