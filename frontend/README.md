# Local LLM Research Agent - React Frontend

> Modern React frontend for the Local LLM Research Agent with real-time chat, dashboards, and comprehensive export capabilities.

---

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Real-time Chat** | WebSocket-based streaming responses from the AI agent |
| **Dark/Light Theme** | System-aware theming with manual override |
| **Conversation History** | Browse and continue past conversations |
| **MCP Server Selection** | Choose which tools the agent can use |
| **Document Management** | Upload and search documents for RAG |
| **Query History** | View and favorite SQL queries |

### Dashboard Features

| Feature | Description |
|---------|-------------|
| **Dashboard CRUD** | Create, edit, and delete dashboards |
| **Widget Pinning** | Pin query results directly to dashboards |
| **Chart Types** | Bar, Line, Area, Pie, Scatter charts via Recharts |
| **KPI Cards** | Single-value metrics with formatting |
| **Drag & Drop** | Resize and reposition widgets with react-grid-layout |
| **Auto-Refresh** | Per-widget refresh intervals |

### Export Features

| Feature | Description |
|---------|-------------|
| **PNG Export** | High-resolution chart images (2x scale) |
| **PDF Export** | Multi-page dashboard/chart reports with titles |
| **CSV Export** | Standard comma-separated data export |
| **Excel Export** | Spreadsheets with auto-calculated column widths |
| **Dashboard JSON** | Import/export dashboard configurations |
| **Chat Export** | Export conversations to Markdown or PDF |
| **Power BI** | Integration dialog for PBIX file creation |

---

## Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| React | 19.1.0 | UI framework |
| Vite | 7.2.7 | Build tool & dev server |
| TypeScript | 5.8.3 | Type safety |
| TanStack Query | 5.90.12 | Server state management |
| Zustand | 5.0.9 | Client state management |
| Tailwind CSS | 3.4.15 | Styling |
| React Router | 7.10.1 | Routing |
| Radix UI | Various | Accessible components |
| Lucide React | 0.513.0 | Icons |
| Recharts | 2.15.3 | Chart components |
| react-grid-layout | 1.5.1 | Dashboard drag & drop |
| html2canvas | 1.4.1 | Screenshot for PNG export |
| jspdf | 4.0.0 | PDF generation |
| exceljs | 4.4.0 | Excel file creation |
| file-saver | 2.0.5 | Cross-browser file downloads |

---

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm
- Running FastAPI backend (port 8000)

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Development URLs

| Service | URL |
|---------|-----|
| Frontend Dev Server | http://localhost:5173 |
| API Proxy | Requests to `/api/*` proxied to localhost:8000 |
| WebSocket Proxy | Connections to `/ws/*` proxied to localhost:8000 |

---

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts           # REST API client with fetch
│   │
│   ├── components/
│   │   ├── chat/               # Chat interface components
│   │   │   ├── ChatInput.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MCPServerSelector.tsx
│   │   │   └── ...
│   │   │
│   │   ├── charts/             # Recharts chart components
│   │   │   ├── BarChartComponent.tsx
│   │   │   ├── LineChartComponent.tsx
│   │   │   ├── AreaChartComponent.tsx
│   │   │   ├── PieChartComponent.tsx
│   │   │   ├── ScatterChartComponent.tsx
│   │   │   ├── KPICard.tsx
│   │   │   ├── ChartRenderer.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── QueryResultPanel.tsx
│   │   │   └── index.ts
│   │   │
│   │   ├── dashboard/          # Dashboard components
│   │   │   ├── DashboardGrid.tsx
│   │   │   ├── WidgetContainer.tsx
│   │   │   └── WidgetEditor.tsx
│   │   │
│   │   ├── dialogs/            # Modal dialogs
│   │   │   └── PowerBIExportDialog.tsx
│   │   │
│   │   ├── export/             # Export components
│   │   │   └── ExportMenu.tsx
│   │   │
│   │   ├── layout/             # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   │
│   │   └── ui/                 # Reusable UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       └── ...
│   │
│   ├── contexts/
│   │   └── ThemeContext.tsx    # Theme provider
│   │
│   ├── hooks/
│   │   ├── useConversations.ts # Conversation React Query hooks
│   │   ├── useDashboards.ts    # Dashboard React Query hooks
│   │   ├── useWebSocket.ts     # WebSocket connection hook
│   │   ├── useChartSuggestion.ts # AI chart type suggestions
│   │   └── usePowerBIExport.ts # Power BI export hook
│   │
│   ├── lib/
│   │   ├── chartSuggestion.ts  # Chart type suggestion logic
│   │   └── exports/            # Export utilities
│   │       ├── pngExport.ts
│   │       ├── pdfExport.ts
│   │       ├── csvExport.ts
│   │       ├── excelExport.ts
│   │       ├── jsonExport.ts
│   │       ├── chatExport.ts
│   │       └── index.ts
│   │
│   ├── pages/
│   │   ├── ChatPage.tsx        # Main chat interface
│   │   ├── DocumentsPage.tsx   # Document management
│   │   ├── DashboardsPage.tsx  # Dashboard list and detail
│   │   ├── QueriesPage.tsx     # Query history
│   │   ├── MCPServersPage.tsx  # MCP server status
│   │   └── SettingsPage.tsx    # App settings
│   │
│   ├── stores/
│   │   └── chatStore.ts        # Zustand chat state
│   │
│   ├── types/
│   │   └── index.ts            # TypeScript interfaces
│   │
│   ├── App.tsx                 # Main app component
│   ├── main.tsx                # Entry point
│   └── index.css               # Global styles + Tailwind
│
├── package.json
├── vite.config.ts              # Vite config with proxy
├── tailwind.config.js
├── tsconfig.json
└── README.md                   # This file
```

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (port 5173) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

---

## Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/chat` | ChatPage | Main chat interface with agent |
| `/chat/:id` | ChatPage | Specific conversation |
| `/documents` | DocumentsPage | Document upload and RAG search |
| `/dashboards` | DashboardsPage | Dashboard list and management |
| `/dashboards/:id` | DashboardsPage | Specific dashboard view |
| `/queries` | QueriesPage | Query history and favorites |
| `/mcp-servers` | MCPServersPage | MCP server status and tools |
| `/settings` | SettingsPage | Theme and app settings |

---

## Export Usage

### Chart Export Menu

The `ExportMenu` component provides a dropdown menu for exporting charts:

```tsx
import { ExportMenu } from '@/components/export/ExportMenu';

function MyChart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const data = [...]; // Your chart data

  return (
    <div>
      <ExportMenu
        elementRef={chartRef}
        data={data}
        filename="my-chart"
        title="Sales Report"
      />
      <div ref={chartRef}>
        {/* Your chart component */}
      </div>
    </div>
  );
}
```

### Dashboard Export

```tsx
// Export dashboard as PDF
import { exportDashboardToPdf } from '@/lib/exports/pdfExport';

const handleExportPdf = async () => {
  if (dashboardRef.current) {
    await exportDashboardToPdf(dashboardRef.current, 'My Dashboard');
  }
};

// Export/Import dashboard configuration
import { exportDashboardToJson, importDashboardFromJson } from '@/lib/exports/jsonExport';

const handleExportJson = () => {
  exportDashboardToJson(dashboard, widgets);
};

const handleImportJson = async (file: File) => {
  const config = await importDashboardFromJson(file);
  // Use config.dashboard and config.widgets
};
```

### Chat Export

```tsx
import { exportChatToMarkdown, exportChatToPdf } from '@/lib/exports/chatExport';

const handleExport = () => {
  exportChatToMarkdown(conversation, messages);
  // or
  exportChatToPdf(conversation, messages);
};
```

---

## API Integration

The frontend communicates with the FastAPI backend through:

1. **REST API** - Standard HTTP requests via fetch
2. **WebSocket** - Real-time chat streaming

### API Client

```typescript
// src/api/client.ts
const API_BASE = '/api';

export const api = {
  conversations: {
    list: () => fetch(`${API_BASE}/conversations`),
    create: (title: string) => fetch(`${API_BASE}/conversations`, {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),
    // ...
  },
  // ...
};
```

### WebSocket Chat

```typescript
// src/hooks/useWebSocket.ts
export function useAgentWebSocket(conversationId: number | null) {
  // Connects to ws://localhost:8000/ws/agent/{conversationId}
  // Returns { sendMessage, isConnected }
}
```

---

## State Management

### Server State (TanStack Query)

Used for data that comes from the API:
- Conversations
- Messages
- Documents
- Dashboards
- Queries

### Client State (Zustand)

Used for UI state:
- Current conversation ID
- Message list (for real-time updates)
- UI preferences

---

## Theming

The app uses CSS variables for theming with Tailwind CSS:

```css
/* Light theme (default) */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  /* ... */
}

/* Dark theme */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... */
}
```

Theme is managed via `ThemeContext` with system detection and localStorage persistence.

---

## Development Notes

1. **Ensure backend is running** before starting the frontend
2. **Proxy configuration** in `vite.config.ts` handles API and WebSocket proxying
3. **Type definitions** are in `src/types/index.ts`
4. **React Query** handles caching and refetching automatically

---

*Last Updated: December 2025*
