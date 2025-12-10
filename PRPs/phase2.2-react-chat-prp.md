# Phase 2.2: React UI & Chat Experience

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 2.2 |
| **Focus** | React, WebSocket, Chat Interface |
| **Estimated Effort** | 3-4 days |
| **Prerequisites** | Phase 2.1 complete |

## Goal

Build the React frontend application with chat interface, WebSocket real-time communication, conversation management, MCP server selection, and foundational UI components.

## Success Criteria

- [ ] React application starts with Vite at `localhost:5173`
- [ ] Theme system works (dark/light toggle)
- [ ] Chat interface sends messages and receives streamed responses
- [ ] WebSocket connection maintains real-time communication
- [ ] Conversations persist and can be resumed
- [ ] MCP servers can be selected for chat sessions
- [ ] Query history displays with search/filter
- [ ] Documents page shows upload functionality
- [ ] Settings page allows model and connection configuration
- [ ] All API calls use TanStack Query with proper caching

## Technology Stack

### Frontend Dependencies

```json
{
  "name": "local-llm-research-agent-ui",
  "version": "2.2.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.0.0",
    "@tanstack/react-query": "^5.62.0",
    "zustand": "^5.0.0",
    "lucide-react": "^0.468.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.0",
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.6.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-select": "^2.1.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.0",
    "@radix-ui/react-tooltip": "^1.1.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^8.0.0",
    "@typescript-eslint/parser": "^8.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.20",
    "eslint": "^9.0.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.15",
    "typescript": "^5.6.0",
    "vite": "^6.0.0"
  }
}
```

## Implementation Plan

### Step 1: Project Setup

#### 1.1 Create React application

```bash
cd /path/to/local-llm-research-agent
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

#### 1.2 Install dependencies

```bash
npm install react-router-dom @tanstack/react-query zustand lucide-react clsx tailwind-merge
npm install react-markdown react-syntax-highlighter date-fns
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select
npm install @radix-ui/react-switch @radix-ui/react-tabs @radix-ui/react-toast @radix-ui/react-tooltip
npm install -D tailwindcss postcss autoprefixer @types/react-syntax-highlighter
npx tailwindcss init -p
```

#### 1.3 Configure Tailwind

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
```

#### 1.4 Configure Vite

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
```

---

### Step 2: Base Styles & Theme System

#### 2.1 Global CSS

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

#### 2.2 Theme Context

```typescript
// frontend/src/contexts/ThemeContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

type Theme = 'dark' | 'light' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'dark' | 'light';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem('theme');
    return (stored as Theme) || 'dark'; // Default to dark
  });

  const [resolvedTheme, setResolvedTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    const root = window.document.documentElement;
    
    const updateTheme = () => {
      let resolved: 'dark' | 'light';
      
      if (theme === 'system') {
        resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      } else {
        resolved = theme;
      }
      
      root.classList.remove('light', 'dark');
      root.classList.add(resolved);
      setResolvedTheme(resolved);
    };

    updateTheme();
    localStorage.setItem('theme', theme);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => theme === 'system' && updateTheme();
    mediaQuery.addEventListener('change', handler);
    
    return () => mediaQuery.removeEventListener('change', handler);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

---

### Step 3: Core UI Components

#### 3.1 Utility functions

```typescript
// frontend/src/lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

#### 3.2 Button component

```typescript
// frontend/src/components/ui/Button.tsx
import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg' | 'icon';
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:pointer-events-none disabled:opacity-50',
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
            'border border-input bg-background hover:bg-accent hover:text-accent-foreground': variant === 'outline',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
            'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
          },
          {
            'h-8 px-3 text-sm': size === 'sm',
            'h-10 px-4 text-sm': size === 'md',
            'h-12 px-6 text-base': size === 'lg',
            'h-10 w-10': size === 'icon',
          },
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button };
```

#### 3.3 Input component

```typescript
// frontend/src/components/ui/Input.tsx
import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2',
          'text-sm ring-offset-background file:border-0 file:bg-transparent',
          'file:text-sm file:font-medium placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = 'Input';

export { Input };
```

#### 3.4 Card component

```typescript
// frontend/src/components/ui/Card.tsx
import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 p-6', className)}
      {...props}
    />
  )
);
CardHeader.displayName = 'CardHeader';

const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-2xl font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
);
CardContent.displayName = 'CardContent';

export { Card, CardHeader, CardTitle, CardContent };
```

---

### Step 4: API Client & State Management

#### 4.1 API client setup

```typescript
// frontend/src/api/client.ts
const API_BASE = '/api';

interface ApiError {
  detail: string;
  status: number;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = {
      detail: 'An error occurred',
      status: response.status,
    };
    try {
      const data = await response.json();
      error.detail = data.detail || data.message || error.detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw error;
  }
  return response.json();
}

export const api = {
  get: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`);
    return handleResponse<T>(response);
  },

  post: async <T>(path: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  put: async <T>(path: string, data: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  delete: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
    });
    return handleResponse<T>(response);
  },

  upload: async <T>(path: string, file: File): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<T>(response);
  },
};
```

#### 4.2 Type definitions

```typescript
// frontend/src/types/index.ts
export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool_calls: string | null;
  tokens_used: number | null;
  created_at: string;
}

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  mime_type: string | null;
  file_size: number;
  chunk_count: number | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  type: 'stdio' | 'http';
  enabled: boolean;
  built_in: boolean;
}

export interface QueryHistory {
  id: number;
  conversation_id: number | null;
  natural_language: string;
  generated_sql: string;
  result_row_count: number | null;
  execution_time_ms: number | null;
  is_favorite: boolean;
  created_at: string;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  services: {
    name: string;
    status: 'healthy' | 'unhealthy' | 'unknown';
    message: string | null;
    latency_ms: number | null;
  }[];
}
```

#### 4.3 React Query hooks

```typescript
// frontend/src/hooks/useConversations.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Conversation, Message } from '@/types';

interface ConversationsResponse {
  conversations: Conversation[];
  total: number;
}

interface MessagesResponse {
  messages: Message[];
  total: number;
}

export function useConversations() {
  return useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.get<ConversationsResponse>('/conversations'),
  });
}

export function useConversation(id: number | null) {
  return useQuery({
    queryKey: ['conversation', id],
    queryFn: () => api.get<Conversation>(`/conversations/${id}`),
    enabled: id !== null,
  });
}

export function useMessages(conversationId: number | null) {
  return useQuery({
    queryKey: ['messages', conversationId],
    queryFn: () => api.get<MessagesResponse>(`/conversations/${conversationId}/messages`),
    enabled: conversationId !== null,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (title?: string) => 
      api.post<Conversation>('/conversations', { title }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => api.delete(`/conversations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}
```

#### 4.4 Chat state with Zustand

```typescript
// frontend/src/stores/chatStore.ts
import { create } from 'zustand';
import { Message } from '@/types';

interface ChatState {
  currentConversationId: number | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  selectedMCPServers: string[];
  
  setCurrentConversation: (id: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
  setSelectedMCPServers: (servers: string[]) => void;
  toggleMCPServer: (serverId: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  currentConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  selectedMCPServers: ['mssql', 'microsoft-learn'], // Default enabled servers

  setCurrentConversation: (id) => set({ currentConversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setIsStreaming: (isStreaming) => set({ isStreaming }),
  appendStreamingContent: (content) => 
    set((state) => ({ streamingContent: state.streamingContent + content })),
  clearStreamingContent: () => set({ streamingContent: '' }),
  setSelectedMCPServers: (servers) => set({ selectedMCPServers: servers }),
  toggleMCPServer: (serverId) => 
    set((state) => ({
      selectedMCPServers: state.selectedMCPServers.includes(serverId)
        ? state.selectedMCPServers.filter((id) => id !== serverId)
        : [...state.selectedMCPServers, serverId],
    })),
}));
```

---

### Step 5: WebSocket Connection

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '@/stores/chatStore';

interface WebSocketMessage {
  type: 'chunk' | 'complete' | 'error' | 'tool_call';
  content?: string;
  message?: Message;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  error?: string;
}

export function useAgentWebSocket(conversationId: number | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const { 
    appendStreamingContent, 
    clearStreamingContent, 
    setIsStreaming,
    addMessage,
    selectedMCPServers,
  } = useChatStore();

  const connect = useCallback(() => {
    if (!conversationId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/agent/${conversationId}`;
    
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);
      
      switch (data.type) {
        case 'chunk':
          appendStreamingContent(data.content || '');
          break;
        case 'complete':
          if (data.message) {
            addMessage(data.message);
          }
          clearStreamingContent();
          setIsStreaming(false);
          break;
        case 'tool_call':
          // Could show tool call indicator in UI
          console.log('Tool call:', data.tool_name, data.tool_args);
          break;
        case 'error':
          console.error('Agent error:', data.error);
          setIsStreaming(false);
          break;
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket closed');
    };
  }, [conversationId, appendStreamingContent, clearStreamingContent, setIsStreaming, addMessage]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    clearStreamingContent();
    setIsStreaming(true);

    wsRef.current.send(JSON.stringify({
      type: 'message',
      content,
      mcp_servers: selectedMCPServers,
    }));
  }, [clearStreamingContent, setIsStreaming, selectedMCPServers]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { sendMessage, disconnect, reconnect: connect };
}
```

---

### Step 6: Layout Components

#### 6.1 Main Layout

```typescript
// frontend/src/components/layout/Layout.tsx
import { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

#### 6.2 Sidebar

```typescript
// frontend/src/components/layout/Sidebar.tsx
import { Link, useLocation } from 'react-router-dom';
import { 
  MessageSquare, 
  FileText, 
  LayoutDashboard, 
  Settings, 
  Database,
  History,
  Plus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { useConversations, useCreateConversation } from '@/hooks/useConversations';
import { useChatStore } from '@/stores/chatStore';

const navItems = [
  { path: '/chat', icon: MessageSquare, label: 'Chat' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/dashboards', icon: LayoutDashboard, label: 'Dashboards' },
  { path: '/queries', icon: History, label: 'Query History' },
  { path: '/mcp-servers', icon: Database, label: 'MCP Servers' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export function Sidebar() {
  const location = useLocation();
  const { data: conversationsData } = useConversations();
  const createConversation = useCreateConversation();
  const { setCurrentConversation } = useChatStore();

  const handleNewChat = async () => {
    const conversation = await createConversation.mutateAsync();
    setCurrentConversation(conversation.id);
  };

  return (
    <aside className="flex w-64 flex-col border-r bg-card">
      {/* Logo/Brand */}
      <div className="flex h-14 items-center border-b px-4">
        <Database className="mr-2 h-6 w-6 text-primary" />
        <span className="font-semibold">Research Analytics</span>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <Button 
          className="w-full" 
          onClick={handleNewChat}
          disabled={createConversation.isPending}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              'flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
              location.pathname === item.path
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <item.icon className="mr-3 h-4 w-4" />
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Recent Conversations */}
      <div className="border-t p-4">
        <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
          Recent Chats
        </h3>
        <div className="space-y-1">
          {conversationsData?.conversations.slice(0, 5).map((conv) => (
            <Link
              key={conv.id}
              to={`/chat/${conv.id}`}
              className="block truncate rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              {conv.title || `Chat ${conv.id}`}
            </Link>
          ))}
        </div>
      </div>
    </aside>
  );
}
```

#### 6.3 Header

```typescript
// frontend/src/components/layout/Header.tsx
import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex h-14 items-center justify-between border-b px-6">
      <div>
        {/* Breadcrumb or page title could go here */}
      </div>

      <div className="flex items-center gap-2">
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon">
              {theme === 'dark' ? (
                <Moon className="h-5 w-5" />
              ) : theme === 'light' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Monitor className="h-5 w-5" />
              )}
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[120px] rounded-md border bg-card p-1 shadow-md"
              sideOffset={5}
            >
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('light')}
              >
                <Sun className="mr-2 inline h-4 w-4" />
                Light
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('dark')}
              >
                <Moon className="mr-2 inline h-4 w-4" />
                Dark
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="cursor-pointer rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => setTheme('system')}
              >
                <Monitor className="mr-2 inline h-4 w-4" />
                System
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </div>
    </header>
  );
}
```

---

### Step 7: Chat Interface

#### 7.1 Chat Page

```typescript
// frontend/src/pages/ChatPage.tsx
import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { MCPServerSelector } from '@/components/chat/MCPServerSelector';
import { useMessages, useCreateConversation } from '@/hooks/useConversations';
import { useAgentWebSocket } from '@/hooks/useWebSocket';
import { useChatStore } from '@/stores/chatStore';

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { currentConversationId, setCurrentConversation, setMessages } = useChatStore();
  const createConversation = useCreateConversation();

  // Parse conversation ID
  const parsedId = conversationId ? parseInt(conversationId, 10) : null;

  // Set current conversation
  useEffect(() => {
    if (parsedId) {
      setCurrentConversation(parsedId);
    }
  }, [parsedId, setCurrentConversation]);

  // Fetch messages
  const { data: messagesData } = useMessages(currentConversationId);

  // Update messages in store
  useEffect(() => {
    if (messagesData?.messages) {
      setMessages(messagesData.messages);
    }
  }, [messagesData, setMessages]);

  // WebSocket connection
  const { sendMessage } = useAgentWebSocket(currentConversationId);

  const handleSendMessage = async (content: string) => {
    // Create conversation if needed
    if (!currentConversationId) {
      const conversation = await createConversation.mutateAsync(content.slice(0, 50));
      setCurrentConversation(conversation.id);
      // Wait for WebSocket to connect before sending
      setTimeout(() => sendMessage(content), 100);
    } else {
      sendMessage(content);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* MCP Server Selection */}
      <div className="border-b p-4">
        <MCPServerSelector />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-auto">
        <MessageList />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <ChatInput onSend={handleSendMessage} />
      </div>
    </div>
  );
}
```

#### 7.2 Message List

```typescript
// frontend/src/components/chat/MessageList.tsx
import { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { User, Bot } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { cn } from '@/lib/utils';

export function MessageList() {
  const { messages, isStreaming, streamingContent } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  return (
    <div className="space-y-4 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={cn(
            'flex gap-3',
            message.role === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          {message.role === 'assistant' && (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
              <Bot className="h-4 w-4 text-primary-foreground" />
            </div>
          )}
          
          <div
            className={cn(
              'max-w-[80%] rounded-lg px-4 py-2',
              message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted'
            )}
          >
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className={cn('rounded bg-muted px-1', className)} {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {message.role === 'user' && (
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
              <User className="h-4 w-4 text-secondary-foreground" />
            </div>
          )}
        </div>
      ))}

      {/* Streaming response */}
      {isStreaming && (
        <div className="flex gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary">
            <Bot className="h-4 w-4 text-primary-foreground" />
          </div>
          <div className="max-w-[80%] rounded-lg bg-muted px-4 py-2">
            <ReactMarkdown>{streamingContent || '...'}</ReactMarkdown>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
```

#### 7.3 Chat Input

```typescript
// frontend/src/components/chat/ChatInput.tsx
import { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useChatStore } from '@/stores/chatStore';

interface ChatInputProps {
  onSend: (content: string) => void;
}

export function ChatInput({ onSend }: ChatInputProps) {
  const [input, setInput] = useState('');
  const { isStreaming } = useChatStore();

  const handleSubmit = () => {
    if (!input.trim() || isStreaming) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex gap-2">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about your data... (Ctrl+Enter to send)"
        className="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        rows={3}
        disabled={isStreaming}
      />
      <Button
        onClick={handleSubmit}
        disabled={!input.trim() || isStreaming}
        size="icon"
        className="h-auto"
      >
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

#### 7.4 MCP Server Selector

```typescript
// frontend/src/components/chat/MCPServerSelector.tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { MCPServer } from '@/types';
import { useChatStore } from '@/stores/chatStore';
import * as Switch from '@radix-ui/react-switch';
import { Database, Globe, BarChart } from 'lucide-react';

const serverIcons: Record<string, typeof Database> = {
  mssql: Database,
  'microsoft-learn': Globe,
  'powerbi-modeling': BarChart,
};

export function MCPServerSelector() {
  const { data: servers } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => api.get<MCPServer[]>('/mcp-servers'),
  });

  const { selectedMCPServers, toggleMCPServer } = useChatStore();

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground">Active Tools</h3>
      <div className="flex flex-wrap gap-3">
        {servers?.filter(s => s.enabled).map((server) => {
          const Icon = serverIcons[server.id] || Database;
          const isSelected = selectedMCPServers.includes(server.id);

          return (
            <div
              key={server.id}
              className="flex items-center gap-2 rounded-md border bg-card px-3 py-2"
            >
              <Icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{server.name}</span>
              <Switch.Root
                checked={isSelected}
                onCheckedChange={() => toggleMCPServer(server.id)}
                className="relative h-5 w-9 rounded-full bg-muted data-[state=checked]:bg-primary"
              >
                <Switch.Thumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform data-[state=checked]:translate-x-4" />
              </Switch.Root>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

### Step 8: Additional Pages (Stubs)

#### 8.1 Documents Page

```typescript
// frontend/src/pages/DocumentsPage.tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Document } from '@/types';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Upload, Trash2, FileText, Loader2 } from 'lucide-react';
import { useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<DocumentsResponse>('/documents'),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.upload<Document>('/documents', file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const statusColors = {
    pending: 'text-yellow-500',
    processing: 'text-blue-500',
    completed: 'text-green-500',
    failed: 'text-red-500',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Documents</h1>
        <Button onClick={() => fileInputRef.current?.click()}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Document
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.pptx,.xlsx,.html,.md,.txt"
          onChange={handleFileSelect}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.documents.map((doc) => (
            <Card key={doc.id}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  <FileText className="mr-2 inline h-4 w-4" />
                  {doc.original_filename}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => deleteMutation.mutate(doc.id)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>Size: {(doc.file_size / 1024).toFixed(1)} KB</p>
                  <p>Chunks: {doc.chunk_count || '-'}</p>
                  <p className={statusColors[doc.processing_status]}>
                    Status: {doc.processing_status}
                  </p>
                  <p>Added {formatDistanceToNow(new Date(doc.created_at))} ago</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 8.2 Settings Page

```typescript
// frontend/src/pages/SettingsPage.tsx
import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Save, RefreshCw } from 'lucide-react';
import { HealthStatus } from '@/types';

interface Settings {
  ollama_host: string;
  ollama_model: string;
  embedding_model: string;
  sql_server_host: string;
  sql_database_name: string;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    ollama_host: 'http://localhost:11434',
    ollama_model: 'qwen3:30b',
    embedding_model: 'nomic-embed-text',
    sql_server_host: 'localhost',
    sql_database_name: 'ResearchAnalytics',
  });

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
  });

  const statusColors = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-yellow-500',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Health Status */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>System Health</CardTitle>
          <Button variant="ghost" size="icon" onClick={() => refetchHealth()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {health?.services.map((service) => (
              <div key={service.name} className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${statusColors[service.status]}`} />
                <div>
                  <p className="font-medium capitalize">{service.name.replace('_', ' ')}</p>
                  {service.latency_ms && (
                    <p className="text-sm text-muted-foreground">{service.latency_ms}ms</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Ollama Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Ollama Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host URL</label>
            <Input
              value={settings.ollama_host}
              onChange={(e) => setSettings({ ...settings, ollama_host: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Model</label>
            <Input
              value={settings.ollama_model}
              onChange={(e) => setSettings({ ...settings, ollama_model: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Embedding Model</label>
            <Input
              value={settings.embedding_model}
              onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
            />
          </div>
        </CardContent>
      </Card>

      {/* SQL Server Settings */}
      <Card>
        <CardHeader>
          <CardTitle>SQL Server Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host</label>
            <Input
              value={settings.sql_server_host}
              onChange={(e) => setSettings({ ...settings, sql_server_host: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Database Name</label>
            <Input
              value={settings.sql_database_name}
              onChange={(e) => setSettings({ ...settings, sql_database_name: e.target.value })}
            />
          </div>
        </CardContent>
      </Card>

      <Button>
        <Save className="mr-2 h-4 w-4" />
        Save Settings
      </Button>
    </div>
  );
}
```

---

### Step 9: App Router

```typescript
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { Layout } from '@/components/layout/Layout';
import { ChatPage } from '@/pages/ChatPage';
import { DocumentsPage } from '@/pages/DocumentsPage';
import { SettingsPage } from '@/pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/chat/:conversationId" element={<ChatPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/dashboards" element={<div>Dashboards - Phase 2.3</div>} />
              <Route path="/queries" element={<div>Query History - Coming Soon</div>} />
              <Route path="/mcp-servers" element={<div>MCP Servers - Coming Soon</div>} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Layout>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
```

---

### Step 10: Backend WebSocket Endpoint

Add to FastAPI backend:

```python
# src/api/routes/agent.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json
import structlog

from src.api.deps import get_db, get_mcp_manager
from src.api.models.database import Conversation, Message
from src.agent.research_agent import create_research_agent

router = APIRouter()
logger = structlog.get_logger()


@router.websocket("/ws/agent/{conversation_id}")
async def agent_websocket(
    websocket: WebSocket,
    conversation_id: int,
):
    """WebSocket endpoint for agent interactions."""
    await websocket.accept()
    logger.info("websocket_connected", conversation_id=conversation_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                mcp_server_ids = data.get("mcp_servers", [])
                
                # Get MCP servers
                mcp_manager = get_mcp_manager()
                servers = mcp_manager.get_servers_by_ids(mcp_server_ids)
                
                # Create agent with selected servers
                agent = create_research_agent(toolsets=servers)
                
                # Stream response
                full_response = ""
                async with agent:
                    async for chunk in agent.run_stream(content):
                        if hasattr(chunk, 'content'):
                            full_response += chunk.content
                            await websocket.send_json({
                                "type": "chunk",
                                "content": chunk.content,
                            })
                        elif hasattr(chunk, 'tool_name'):
                            await websocket.send_json({
                                "type": "tool_call",
                                "tool_name": chunk.tool_name,
                                "tool_args": chunk.tool_args,
                            })
                
                # Save messages to database
                # (Implementation depends on session management)
                
                # Send completion
                await websocket.send_json({
                    "type": "complete",
                    "message": {
                        "id": 0,  # Will be set by database
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": full_response,
                        "tool_calls": None,
                        "tokens_used": None,
                        "created_at": None,
                    },
                })
                
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        await websocket.send_json({
            "type": "error",
            "error": str(e),
        })
```

---

## File Structure After Phase 2.2

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── api/
│   │   └── client.ts
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── index.ts
│   │   ├── layout/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   └── chat/
│   │       ├── MessageList.tsx
│   │       ├── ChatInput.tsx
│   │       └── MCPServerSelector.tsx
│   ├── contexts/
│   │   └── ThemeContext.tsx
│   ├── hooks/
│   │   ├── useConversations.ts
│   │   └── useWebSocket.ts
│   ├── lib/
│   │   └── utils.ts
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   └── SettingsPage.tsx
│   ├── stores/
│   │   └── chatStore.ts
│   └── types/
│       └── index.ts
```

---

## Validation Checkpoints

1. **React app starts:**
   ```bash
   cd frontend
   npm run dev
   # Visit http://localhost:5173
   ```

2. **Theme toggle works:**
   - Click theme button in header
   - Toggle between light/dark/system
   - Verify theme persists on refresh

3. **Chat interface works:**
   - Create new conversation
   - Send message
   - Receive streamed response
   - Messages render with Markdown

4. **MCP server selection:**
   - Toggle servers on/off
   - Verify selection persists during session

5. **Documents page:**
   - Upload document
   - See processing status
   - Delete document

6. **API proxy works:**
   - All `/api/*` requests route to backend
   - No CORS errors in console

---

## Notes for Implementation

- **DO NOT modify** backend files from Phase 2.1 unless adding WebSocket endpoint
- Keep components small and focused
- Use TanStack Query for all API calls
- Use Zustand for client-side state only
- Test with browser DevTools open for errors
- Ensure dark mode is default
