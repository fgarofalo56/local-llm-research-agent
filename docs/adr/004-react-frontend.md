# ADR-004: React 19 + Vite + TypeScript Frontend

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The Local LLM Research Agent initially provided two user interfaces: a CLI (Typer + Rich) and a Streamlit web UI. While functional, Streamlit had limitations for building a modern, interactive data analytics application with real-time chat, dashboards, and complex state management.

### Requirements
- Real-time chat with WebSocket streaming
- Interactive dashboards with drag-and-drop widgets
- Complex UI state management (conversations, queries, documents)
- Fast, responsive user experience
- Modern UI/UX with dark/light themes
- Rich data visualization (charts, tables)
- Export functionality (PNG, PDF, CSV, Excel)
- Embeddable Superset dashboards
- Type-safe frontend codebase
- Hot module replacement for fast development

### Technical Context
- FastAPI backend with REST + WebSocket APIs
- Multiple data flows: agent chat, documents, queries, dashboards
- Real-time streaming responses from LLM
- Complex state (conversation history, MCP servers, theme settings)
- Need for production-ready build tooling
- Target: Modern browsers (Chrome, Firefox, Edge, Safari)

## Decision

We will build a **React 19 frontend** using **Vite** as the build tool and **TypeScript** for type safety, replacing Streamlit as the primary web UI.

### Tech Stack
| Package | Version | Purpose |
|---------|---------|---------|
| **React** | 19.2.0 | UI framework with latest features (19.x actions, transitions) |
| **Vite** | 7.2.4 | Fast build tool with hot module replacement |
| **TypeScript** | 5.9.3 | Type safety and developer experience |
| **TanStack Query** | 5.90.12 | Server state management (React Query) |
| **Zustand** | 5.0.9 | Client state management (lightweight) |
| **React Router** | 7.10.1 | Client-side routing |
| **Tailwind CSS** | 3.4.15 | Utility-first styling |
| **Recharts** | 3.5.1 | Data visualization |
| **Radix UI** | Latest | Accessible component primitives |
| **Lucide React** | 0.559.0 | Icon library |

### Project Structure
```
frontend/
├── src/
│   ├── api/              # REST API client (axios/fetch)
│   ├── components/
│   │   ├── chat/         # Chat UI components
│   │   ├── charts/       # Recharts wrappers
│   │   ├── dashboard/    # Dashboard builder
│   │   ├── export/       # Export dialogs
│   │   ├── layout/       # App layout components
│   │   └── ui/           # Reusable UI (Radix wrappers)
│   ├── contexts/         # React contexts
│   ├── hooks/            # Custom hooks (useWebSocket, etc.)
│   ├── lib/              # Utilities
│   ├── pages/            # Route pages
│   ├── stores/           # Zustand stores
│   └── types/            # TypeScript interfaces
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### Key Features
- **Async Actions**: Leverage React 19's `useTransition` and `useActionState` for better UX
- **WebSocket Chat**: Real-time streaming with auto-reconnect
- **Dashboard Builder**: react-grid-layout for drag-and-drop
- **Theme System**: CSS variables for dark/light mode
- **Export System**: html2canvas + jspdf for chart/dashboard exports
- **Type Safety**: Full TypeScript coverage with strict mode

## Consequences

### Positive Consequences
- **Modern UX**: React enables rich interactions (drag-drop, real-time updates) impossible in Streamlit
- **Type Safety**: TypeScript catches errors at compile time across entire frontend
- **Developer Experience**: Vite hot reload (~50ms) vs Streamlit rerun (~2-3s)
- **Performance**: React virtual DOM + optimized re-renders vs Streamlit full page reruns
- **Ecosystem**: Massive React ecosystem for any UI component/library needed
- **Real-time**: Native WebSocket support without Streamlit limitations
- **Customization**: Complete control over UI/UX vs Streamlit constraints
- **Production Ready**: Vite build optimizations (code splitting, tree shaking, minification)
- **State Management**: Sophisticated state with Zustand + TanStack Query vs Streamlit session state
- **Testing**: Rich testing ecosystem (Vitest, Testing Library, Playwright)
- **Deployment**: Static build output can be served from CDN
- **Mobile**: Responsive design easier with Tailwind + React vs Streamlit

### Negative Consequences
- **Complexity**: More code to write/maintain vs Streamlit's simplicity
- **Learning Curve**: Team needs React/TypeScript expertise (higher than Streamlit)
- **Development Time**: Initial setup and component library took ~2 weeks
- **Bundle Size**: React + dependencies ~300KB (minified) vs Streamlit's server-side rendering
- **Maintenance**: Must keep up with React/Vite/TypeScript updates
- **Backend Coupling**: Need to maintain REST API alongside WebSocket
- **Initial Setup**: More configuration (Vite, TypeScript, Tailwind) vs `streamlit run`

### Neutral Consequences
- **Two UIs**: Streamlit still available for simple use cases; React for full-featured app
- **Build Step**: Production deployment requires `npm run build` vs Streamlit's direct run
- **Node.js Dependency**: Requires Node.js for development (team already has it)

## Alternatives Considered

### Alternative 1: Continue with Streamlit
- **Pros:**
  - Already implemented and working
  - Zero JavaScript/TypeScript required
  - Simple Python-only development
  - Fast prototyping
  - Built-in components
- **Cons:**
  - Limited real-time capabilities (polling-based, no true WebSocket)
  - Page reruns on every interaction (poor UX)
  - Limited styling/customization
  - Complex state management
  - No drag-and-drop support
  - Difficult to embed external content (iframes)
  - Not production-grade for complex apps
  - Mobile experience subpar
- **Reason for rejection:** Cannot meet UX requirements for dashboard builder, real-time chat

### Alternative 2: Vue.js 3
- **Pros:**
  - Simpler API than React
  - Excellent documentation
  - Good TypeScript support
  - Composition API similar to React hooks
  - Smaller bundle size
- **Cons:**
  - Smaller ecosystem than React
  - Fewer data visualization libraries
  - Less community support
  - Team unfamiliar with Vue
  - Fewer component libraries (vs Radix, MUI, etc.)
- **Reason for rejection:** React's ecosystem and team familiarity outweigh Vue's simplicity

### Alternative 3: Svelte/SvelteKit
- **Pros:**
  - Compile-time framework (smallest bundles)
  - Simple syntax
  - Good performance
  - TypeScript support
  - Built-in state management
- **Cons:**
  - Smaller ecosystem
  - Fewer component libraries
  - Less mature than React
  - Team learning curve
  - Fewer resources/tutorials
  - Limited enterprise adoption
- **Reason for rejection:** Ecosystem maturity and component libraries favor React

### Alternative 4: Angular
- **Pros:**
  - Full-featured framework
  - Excellent TypeScript integration
  - Enterprise-proven
  - Opinionated structure
  - Powerful CLI
- **Cons:**
  - Steep learning curve
  - Heavy framework (large bundle)
  - Over-engineered for this use case
  - Complex setup
  - RxJS learning requirement
  - Verbose syntax
- **Reason for rejection:** Too heavyweight; complexity exceeds project needs

### Alternative 5: Next.js (React)
- **Pros:**
  - React-based (familiar ecosystem)
  - Server-side rendering
  - File-based routing
  - API routes
  - Great developer experience
- **Cons:**
  - Overkill for client-only app
  - SSR not needed (backend is FastAPI)
  - More complex deployment
  - Backend logic should stay in FastAPI
  - File-based routing less flexible
- **Reason for rejection:** SSR unnecessary; Vite + React Router simpler for SPA

### Alternative 6: Remix (React)
- **Pros:**
  - Modern React patterns
  - Excellent data loading
  - Good TypeScript support
  - Focus on web fundamentals
- **Cons:**
  - Server-side focus (backend is FastAPI)
  - Newer framework (less mature)
  - Smaller ecosystem than Next.js
  - Learning curve for Remix patterns
- **Reason for rejection:** Server-side features unnecessary; Vite simpler

### Alternative 7: Vanilla JavaScript + Webpack
- **Pros:**
  - No framework overhead
  - Complete control
  - Minimal abstractions
- **Cons:**
  - Must implement state management from scratch
  - Component reusability difficult
  - No type safety (or complex TypeScript setup)
  - Slow development velocity
  - Complex WebSocket management
  - No ecosystem benefits
- **Reason for rejection:** Reinventing React; significant development time

## References

- **React 19 Documentation**: [react.dev](https://react.dev/)
- **Vite Documentation**: [vitejs.dev](https://vitejs.dev/)
- **TypeScript Handbook**: [typescriptlang.org/docs](https://www.typescriptlang.org/docs/)
- **Related ADRs**:
  - [ADR-005: WebSocket Real-time](005-websocket-realtime.md) - Real-time chat architecture
  - [ADR-007: Zustand State](007-zustand-state.md) - Client state management
- **Implementation Files**:
  - `frontend/vite.config.ts` - Vite configuration
  - `frontend/tsconfig.json` - TypeScript configuration
  - `frontend/tailwind.config.js` - Tailwind CSS configuration
  - `frontend/src/main.tsx` - Application entry point
  - `frontend/src/App.tsx` - Root component with routing
- **Key Dependencies**:
  - `package.json`: Full dependency list
  - `@tanstack/react-query`: Server state
  - `zustand`: Client state
  - `recharts`: Charts
  - `react-router-dom`: Routing
  - `tailwindcss`: Styling

---

**Note:** This decision should be revisited if:
1. React introduces breaking changes requiring major refactor
2. Streamlit adds real-time WebSocket support and advanced state management
3. Team expertise shifts away from React
4. Bundle size becomes problematic for users
5. A significantly better framework emerges and gains wide adoption
