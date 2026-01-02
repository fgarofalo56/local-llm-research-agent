# Frontend Developer Guide

Welcome to the Local LLM Research Agent frontend documentation. This guide will help you understand the architecture, patterns, and best practices used in this React application.

## Table of Contents

1. [Architecture Overview](./architecture.md)
2. [State Management](./state-management.md)
3. [Styling Guide](./styling-guide.md)
4. [API Integration](./api-integration.md)

## Quick Start

### Prerequisites

- Node.js 18+
- npm or pnpm
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Development URLs

- Frontend: http://localhost:5173
- API Proxy: `/api/*` -> `http://localhost:8000/api/*`
- WebSocket Proxy: `/ws/*` -> `ws://localhost:8000/ws/*`

## Tech Stack

### Core Framework

- **React 19** - UI framework with latest features
- **TypeScript** - Type safety and better DX
- **Vite** - Fast build tool and dev server

### State Management

- **Zustand** - Lightweight state management for UI state
- **TanStack Query (React Query)** - Server state management and caching
- **React Context** - Theme and global settings

### UI & Styling

- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible, unstyled component primitives
- **Lucide React** - Icon library
- **clsx + tailwind-merge** - Conditional className management

### Data Visualization

- **Recharts** - Declarative chart library
- **React Grid Layout** - Draggable dashboard widgets

### Additional Libraries

- **React Router DOM** - Client-side routing
- **React Markdown** - Markdown rendering for chat
- **React Syntax Highlighter** - Code syntax highlighting
- **xlsx** - Excel export
- **jsPDF** - PDF generation
- **html2canvas** - Chart image export
- **date-fns** - Date formatting

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/            # API client and request handlers
│   ├── components/     # React components
│   │   ├── chat/       # Chat interface components
│   │   ├── charts/     # Data visualization components
│   │   ├── dashboard/  # Dashboard components
│   │   ├── dialogs/    # Modal dialogs
│   │   ├── export/     # Export functionality
│   │   ├── layout/     # App layout components
│   │   ├── onboarding/ # User onboarding
│   │   ├── settings/   # Settings UI
│   │   ├── superset/   # Apache Superset integration
│   │   ├── ui/         # Reusable UI primitives
│   │   └── upload/     # File upload components
│   ├── contexts/       # React contexts
│   │   └── ThemeContext.tsx
│   ├── hooks/          # Custom React hooks
│   ├── lib/            # Utility libraries
│   │   ├── exports/    # Export utilities (CSV, Excel, PDF, etc.)
│   │   ├── chartSuggestion.ts
│   │   ├── themes.ts
│   │   └── utils.ts
│   ├── pages/          # Route page components
│   │   ├── ChatPage.tsx
│   │   ├── DashboardsPage.tsx
│   │   ├── DatabaseSettingsPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── MCPServersPage.tsx
│   │   ├── QueriesPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── SupersetPage.tsx
│   ├── stores/         # Zustand stores
│   │   ├── chatStore.ts
│   │   ├── dashboardStore.ts
│   │   └── uploadStore.ts
│   ├── types/          # TypeScript type definitions
│   │   ├── dashboard.ts
│   │   └── index.ts
│   ├── App.tsx         # Root component with routing
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles and theme variables
├── .eslintrc.cjs       # ESLint configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── tsconfig.json       # TypeScript configuration
├── vite.config.ts      # Vite configuration
└── package.json        # Dependencies and scripts
```

## Key Features

### 1. Real-time Chat Interface

- WebSocket-based streaming responses
- Markdown and code syntax highlighting
- Message ratings and feedback
- Conversation history management

### 2. Data Visualization

- Interactive charts (Line, Bar, Area, Pie, Scatter)
- KPI cards and metrics
- Data tables with sorting
- Export to PNG, PDF, CSV, Excel

### 3. Dashboard Builder

- Drag-and-drop widget layout
- Pin queries and charts to dashboards
- Save/load dashboard configurations
- Share dashboards

### 4. Document Management

- Multi-file upload with progress tracking
- Document processing status monitoring
- RAG (Retrieval Augmented Generation) integration
- Document search and filtering

### 5. MCP Server Management

- Enable/disable MCP servers dynamically
- View available tools and capabilities
- Server health monitoring

### 6. Theme System

- 9 built-in theme variants
- Light/dark mode support
- System theme detection
- HSL-based CSS variables for easy customization

## Development Patterns

### Component Organization

Components follow a hierarchical structure:

```
pages/           # Route-level components
  └── components/ # Feature-specific components
      └── ui/     # Reusable primitives
```

### Naming Conventions

- **Components**: PascalCase (e.g., `ChatInput.tsx`)
- **Hooks**: camelCase with `use` prefix (e.g., `useOnboardingStatus.ts`)
- **Utilities**: camelCase (e.g., `chartSuggestion.ts`)
- **Types**: PascalCase for interfaces (e.g., `Message`, `Document`)
- **Stores**: camelCase with `Store` suffix (e.g., `chatStore.ts`)

### File Structure

Each component file should export:

```typescript
// Named export for the component
export function ComponentName() {
  // ...
}

// Optional: Type exports
export type ComponentProps = {
  // ...
};
```

### Code Splitting

Large pages are lazy-loaded in `App.tsx`:

```typescript
const ChatPage = lazy(() =>
  import('@/pages/ChatPage').then(m => ({ default: m.ChatPage }))
);
```

### Path Aliases

Use `@/` alias for cleaner imports:

```typescript
import { api } from '@/api/client';
import { useChatStore } from '@/stores/chatStore';
import { Button } from '@/components/ui/Button';
```

## Testing

Currently, the project uses:

- **ESLint** - Code linting
- **TypeScript** - Type checking
- **Playwright** - E2E testing (configured but not fully implemented)

Future testing strategy:

- Unit tests with Vitest
- Component tests with React Testing Library
- E2E tests with Playwright

## Performance Optimization

### Code Splitting

- Pages are lazy-loaded
- Vendor chunks are split by category:
  - `vendor-react`: React core libraries
  - `vendor-ui`: Radix UI components
  - `vendor-charts`: Recharts
  - `vendor-query`: TanStack Query
  - `vendor-export`: Export libraries
  - `vendor-markdown`: Markdown rendering
  - `vendor-utils`: Utilities

### Query Optimization

- TanStack Query caching (1 minute stale time)
- Automatic refetching on window focus
- Optimistic updates for better UX

### Bundle Size

Current chunk size warning limit: 1500 KB

Monitor bundle size with:

```bash
npm run build
```

## Deployment

### Build

```bash
npm run build
```

Output: `dist/` directory

### Environment Variables

The frontend uses Vite's proxy configuration. No environment variables are required for the frontend itself - API URLs are proxied through Vite dev server.

Production deployments should configure reverse proxy to route:

- `/api/*` -> Backend API
- `/ws/*` -> WebSocket API

### Docker

The frontend can be built in Docker using the multi-stage Dockerfile in the root project.

## Next Steps

- Read the [Architecture Guide](./architecture.md) to understand component hierarchy and data flow
- Review [State Management](./state-management.md) to learn when to use Zustand vs TanStack Query
- Check the [Styling Guide](./styling-guide.md) for Tailwind CSS patterns and theme customization
- Explore [API Integration](./api-integration.md) for backend communication patterns

## Contributing

When adding new features:

1. Follow the existing folder structure
2. Use TypeScript for all new code
3. Keep components focused and single-responsibility
4. Add types for all props and state
5. Use Zustand for UI state, TanStack Query for server state
6. Follow Tailwind CSS conventions
7. Test locally with the backend running

## Resources

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
