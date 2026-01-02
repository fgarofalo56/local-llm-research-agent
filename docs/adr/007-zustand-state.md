# ADR-007: Zustand for Client State Management

**Date:** 2025-01-15

**Status:** Accepted

---

## Context

The React frontend needed a state management solution to handle client-side application state including:
- UI state (theme, sidebar open/closed, modals)
- User preferences (selected MCP servers, display settings)
- Transient state (current conversation, draft messages)
- WebSocket connection status
- Chat interface state (input value, streaming status)

This is distinct from server state (conversations, documents, queries) which is managed by TanStack Query (React Query).

### Requirements
- Simple API for developers to use
- Type-safe with TypeScript
- Minimal boilerplate
- No prop drilling
- Good React 19 compatibility
- Small bundle size
- DevTools for debugging
- Support for derived state
- No context provider overhead
- Fast re-renders (optimized selectors)

### Technical Context
- React 19 with TypeScript
- TanStack Query handling server state
- Multiple components need shared state
- Theme switching (dark/light mode)
- WebSocket connection state
- MCP server selection state
- Chat interface state (streaming, input)

### State Categories
1. **Server State** (TanStack Query): Conversations, documents, queries, dashboards
2. **Client State** (Need solution): Theme, UI toggles, preferences, transient data
3. **URL State** (React Router): Current page, conversation ID

## Decision

We will use **Zustand** for client-side state management.

### Implementation Pattern

**Store Definition**:
```typescript
// stores/themeStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeState {
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'system',
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'theme-storage' }
  )
);
```

**Usage in Components**:
```typescript
// Component.tsx
import { useThemeStore } from '@/stores/themeStore';

function ThemeToggle() {
  // Only subscribes to theme changes (optimized)
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);

  return (
    <button onClick={() => setTheme('dark')}>
      {theme}
    </button>
  );
}
```

### Store Organization
```
frontend/src/stores/
├── themeStore.ts       # Theme preferences
├── chatStore.ts        # Chat UI state (input, streaming)
├── mcpStore.ts         # Selected MCP servers
├── websocketStore.ts   # WS connection state
└── uiStore.ts          # General UI state (sidebar, modals)
```

### Key Features Used
- **Selectors**: Component subscribes only to needed state slices
- **Persistence**: LocalStorage middleware for preferences
- **DevTools**: Redux DevTools integration for debugging
- **Middleware**: Logging, persistence, immer (for immutability)

## Consequences

### Positive Consequences
- **Simplicity**: Very simple API (`create`, selectors, `set`)
- **Zero Boilerplate**: No actions, reducers, or providers needed
- **TypeScript Native**: Excellent type inference out of the box
- **Small Bundle**: ~1KB minified (vs Redux ~10KB)
- **Fast**: No context overhead, direct store subscriptions
- **Granular Subscriptions**: Components only re-render when selected state changes
- **No Provider Hell**: No need to wrap app in context providers
- **Async Support**: Built-in async actions with no middleware
- **Persistence**: Easy localStorage persistence via middleware
- **DevTools**: Redux DevTools compatible for debugging
- **Learning Curve**: Minimal; team picks it up in <1 hour
- **React 19 Compatible**: No issues with React 19 features
- **Testable**: Easy to test stores in isolation

### Negative Consequences
- **Global State**: All stores are global (not scoped to component tree)
- **Less Opinionated**: No enforced patterns (team must establish conventions)
- **No Time Travel**: DevTools support but not as rich as Redux
- **Middleware Ecosystem**: Smaller middleware ecosystem vs Redux
- **Learning Resources**: Fewer tutorials/examples than Redux
- **No Built-in Undo**: Must implement undo/redo manually

### Neutral Consequences
- **Not for Server State**: Use TanStack Query for server data (intentional separation)
- **Flux-like**: Follows Flux pattern but simpler than Redux
- **Store Splitting**: Encourages multiple small stores vs single Redux store

## Alternatives Considered

### Alternative 1: Redux Toolkit
- **Pros:**
  - Industry standard
  - Massive ecosystem
  - Excellent DevTools
  - Rich middleware (sagas, thunks)
  - Time travel debugging
  - Strong conventions
  - Extensive documentation
- **Cons:**
  - Significant boilerplate (actions, reducers, slices)
  - ~10KB bundle size
  - Steeper learning curve
  - Context provider overhead
  - Complex async logic (thunks/sagas)
  - Overkill for simple UI state
  - Verbose TypeScript setup
- **Reason for rejection:** Too complex for client UI state; TanStack Query handles server state

### Alternative 2: Jotai
- **Pros:**
  - Atomic state (fine-grained reactivity)
  - Minimal API
  - Small bundle size
  - Good TypeScript support
  - Modern React patterns
- **Cons:**
  - Atomic model has learning curve
  - Less mature than Zustand
  - Smaller community
  - Different mental model (atoms vs stores)
  - More complex for complex state
- **Reason for rejection:** Atomic model overkill; Zustand simpler for team

### Alternative 3: Recoil
- **Pros:**
  - Facebook-backed
  - Atomic state model
  - Derived state (selectors)
  - Time travel support
  - Good for complex dependencies
- **Cons:**
  - Requires context providers
  - Still experimental (not 1.0)
  - Larger bundle than Zustand
  - Complex API for simple cases
  - Less TypeScript ergonomic
  - Updates less frequent
- **Reason for rejection:** Still experimental; more complex than needed

### Alternative 4: MobX
- **Pros:**
  - Simple API (observable objects)
  - No boilerplate
  - Automatic reactivity
  - Good for complex domains
  - Mature library
- **Cons:**
  - Decorator/proxy magic (less explicit)
  - TypeScript setup complex
  - Different paradigm (OOP vs functional)
  - Larger bundle size
  - Less popular in React community
  - Debugging less intuitive
- **Reason for rejection:** Magic reactivity harder to debug; team prefers explicit

### Alternative 5: Context API + useReducer
- **Pros:**
  - Built into React (no dependencies)
  - Zero bundle overhead
  - Standard React patterns
  - Full control
- **Cons:**
  - Verbose setup (providers, reducers, actions)
  - Provider hell for multiple contexts
  - Re-render optimization manual (useMemo/useCallback)
  - No persistence middleware
  - No DevTools
  - Boilerplate for each context
  - Testing more complex
- **Reason for rejection:** Too much boilerplate; optimization manual

### Alternative 6: Valtio
- **Pros:**
  - Proxy-based (simple API)
  - Minimal code
  - Good TypeScript support
  - Same author as Zustand
  - Mutable API
- **Cons:**
  - Smaller community than Zustand
  - Proxy-based can have gotchas
  - Less documentation
  - Newer/less mature
  - Team unfamiliar with proxy patterns
- **Reason for rejection:** Zustand more established; team prefers immutable pattern

### Alternative 7: XState
- **Pros:**
  - State machines (explicit states/transitions)
  - Excellent for complex workflows
  - Visualizer tool
  - Predictable state changes
  - Good TypeScript support
- **Cons:**
  - High learning curve
  - Overkill for simple UI state
  - Verbose state machine definitions
  - Larger bundle size
  - Complex for async operations
- **Reason for rejection:** State machines unnecessary for UI toggles/preferences

### Alternative 8: Nanostores
- **Pros:**
  - Tiny bundle (334 bytes)
  - Framework-agnostic
  - Simple API
  - Fast
- **Cons:**
  - Less React-specific
  - Smaller ecosystem
  - Less TypeScript ergonomic
  - Fewer examples
  - No persistence middleware
  - Limited DevTools
- **Reason for rejection:** Zustand's React integration and ecosystem better

## References

- **Zustand Documentation**: [github.com/pmndrs/zustand](https://github.com/pmndrs/zustand)
- **Zustand Examples**: [docs.pmnd.rs/zustand](https://docs.pmnd.rs/zustand/getting-started/introduction)
- **Related ADRs**:
  - [ADR-004: React Frontend](004-react-frontend.md) - React 19 + TypeScript foundation
- **Implementation Files**:
  - `frontend/src/stores/themeStore.ts` - Theme preferences
  - `frontend/src/stores/chatStore.ts` - Chat interface state
  - `frontend/src/stores/mcpStore.ts` - MCP server selection
  - `frontend/src/stores/websocketStore.ts` - WebSocket connection state
  - `frontend/src/stores/uiStore.ts` - General UI toggles
- **Dependencies**:
  - `package.json`: `zustand@5.0.9`
- **Bundle Size**:
  - Zustand: ~1.2KB minified + gzipped
  - TanStack Query: ~12KB (for server state)
  - Total state management: ~13KB

---

**Note:** This decision should be revisited if:
1. State complexity grows to need state machines (consider XState)
2. Redux Toolkit significantly simplifies API and reduces boilerplate
3. React introduces better built-in state management primitives
4. Zustand project becomes unmaintained
5. Team needs strict flux architecture patterns (consider Redux)
6. Bundle size becomes critical and every KB matters (consider Nanostores)
