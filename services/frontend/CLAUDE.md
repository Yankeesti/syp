# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
npm install      # Install dependencies
npm run dev      # Start dev server (port 3000, auto-fallback if busy)
npm run build    # Production build (outputs to /build)
```

No test or lint commands are currently configured.

## Architecture Overview

This is a **React 18 + TypeScript + Vite** frontend for "KI Tutor", an AI-powered quiz learning platform.

### Tech Stack
- **Build**: Vite with React SWC plugin
- **Styling**: Tailwind CSS + Radix UI primitives
- **Routing**: React Router DOM
- **Icons**: Lucide React
- **State**: React hooks + localStorage (no global state manager)

### Project Structure

```
src/
├── app/                    # Routing, layouts, guards
│   ├── App.tsx            # Root router
│   ├── QuizRoutes.tsx     # Quiz feature routes & business logic (~695 lines)
│   ├── guards.tsx         # RequireAuth, RedirectIfAuthenticated
│   └── layouts/           # Header, NavigationSidebar
├── config/env.ts          # Environment config
├── features/              # Domain modules
│   ├── auth/              # Magic link authentication
│   ├── quiz/              # Quiz CRUD, generation, editing
│   └── learning/          # Quiz attempts & evaluation
└── shared/
    ├── api/client.ts      # Centralized HTTP client (requestJson, buildApiUrl)
    └── ui/                # Reusable UI components (Button, Dialog, Input, etc.)
```

### Feature Module Pattern

Each feature in `/features` follows this structure:
- `pages/` - Route/screen components
- `hooks/` - Custom hooks for state & side effects
- `model/` - API types, mappers, business logic
- `entities/` - Domain type definitions
- `index.ts` - Public exports

### Key Patterns

**API Client**: All HTTP requests go through `shared/api/client.ts` which handles auth headers, timeouts, and error handling.

**Polling**: Quiz generation status uses polling (3s intervals) in `useQuizzes` hook - check for cleanup on unmount.

**Type Mapping**: API response types are separate from domain types with explicit mapper functions in `model/` directories.

**Route Guards**: `RequireAuth` wraps protected routes, `RedirectIfAuthenticated` prevents logged-in users from seeing auth screens.

### Environment Variables

Copy `.env.example` to `.env`. Key vars:
- `VITE_API_BASE_URL` - Backend API URL (default: http://localhost:8000)
- `VITE_USE_MOCKS` - Enable mock data mode

### Path Alias

`@` maps to `./src` (configured in vite.config.ts and tsconfig.json).
