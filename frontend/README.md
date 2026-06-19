# Frontend

Next.js 15 application with TypeScript, Tailwind CSS, Shadcn UI, and Framer Motion.

## Directory Guide

```
src/
├── app/                    # Next.js App Router — pages and layouts
│   ├── dashboard/          # Main dashboard overview
│   ├── websites/           # Website management
│   ├── reports/            # Report listing and download
│   ├── analytics/          # Charts and trend analysis
│   ├── settings/           # User and app preferences
│   └── auth/               # Login and registration
│
├── components/
│   ├── ui/                 # Shadcn UI primitives (Button, Card, Input)
│   ├── layout/             # Shell, sidebar, header
│   ├── dashboard/          # Dashboard-specific components
│   ├── tables/             # Data table components (Phase 03)
│   ├── charts/             # Recharts wrappers (Phase 05)
│   ├── forms/              # Form components (Phase 03)
│   └── animations/         # Framer Motion wrappers
│
├── hooks/                  # Custom React hooks
├── lib/                    # Utilities, API client, design tokens
├── services/               # API service functions (used by React Query)
├── store/                  # Zustand stores (auth, dashboard, UI)
├── styles/                 # Global CSS and design token variables
└── types/                  # TypeScript interfaces matching API schemas
```

## State Architecture

| Concern | Tool | Location |
|---------|------|----------|
| Server data | React Query | Hooks calling `services/` |
| Auth session | Zustand (persisted) | `store/auth-store.ts` |
| Dashboard filters | Zustand | `store/dashboard-store.ts` |
| UI preferences | Zustand | `store/ui-store.ts` |

## Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run lint         # ESLint check
npm run type-check   # TypeScript validation
```
