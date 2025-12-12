# Phase 2.3: Data Visualization & Dashboards

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 2.3 |
| **Focus** | Recharts, Dashboard System, Drag-Drop |
| **Estimated Effort** | 3-4 days |
| **Prerequisites** | Phase 2.2 complete |

## Goal

Implement data visualization with Recharts, AI-driven chart suggestions, dashboard system with drag-drop layout, widget pinning from query results, and auto-refresh capabilities.

## Success Criteria

- [x] Query results render as interactive charts
- [x] AI suggests appropriate chart type based on data structure
- [x] Dashboard page displays grid of widgets
- [x] Widgets can be dragged and resized
- [x] "Pin to Dashboard" creates widget from query result
- [x] Widget configurations persist to database
- [x] Auto-refresh updates widget data on interval
- [x] Multiple dashboards can be created/managed
- [x] Chart types: Bar, Line, Area, Pie, Scatter, KPI Card, Table

## Technology Stack Additions

```bash
cd frontend
npm install recharts react-grid-layout
npm install -D @types/react-grid-layout
```

## Implementation Plan

### Step 1: Chart Components

#### 1.1 Base Chart Wrapper

```typescript
// frontend/src/components/charts/ChartWrapper.tsx
import { ReactNode } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { MoreHorizontal, Pin, RefreshCw, Maximize2 } from 'lucide-react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';

interface ChartWrapperProps {
  title: string;
  children: ReactNode;
  onPin?: () => void;
  onRefresh?: () => void;
  onExpand?: () => void;
  isRefreshing?: boolean;
}

export function ChartWrapper({
  title,
  children,
  onPin,
  onRefresh,
  onExpand,
  isRefreshing,
}: ChartWrapperProps) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenu.Trigger>
          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="min-w-[140px] rounded-md border bg-card p-1 shadow-md"
              sideOffset={5}
            >
              {onPin && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onPin}
                >
                  <Pin className="mr-2 h-4 w-4" />
                  Pin to Dashboard
                </DropdownMenu.Item>
              )}
              {onRefresh && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onRefresh}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </DropdownMenu.Item>
              )}
              {onExpand && (
                <DropdownMenu.Item
                  className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                  onClick={onExpand}
                >
                  <Maximize2 className="mr-2 h-4 w-4" />
                  Expand
                </DropdownMenu.Item>
              )}
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      </CardHeader>
      <CardContent className="h-[calc(100%-4rem)]">
        {children}
      </CardContent>
    </Card>
  );
}
```

#### 1.2 Bar Chart

```typescript
// frontend/src/components/charts/BarChartComponent.tsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface BarChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  colors?: string[];
}

const defaultColors = [
  'hsl(var(--primary))',
  'hsl(210, 70%, 50%)',
  'hsl(150, 70%, 50%)',
  'hsl(30, 70%, 50%)',
  'hsl(280, 70%, 50%)',
];

export function BarChartComponent({ data, xKey, yKeys, colors = defaultColors }: BarChartProps) {
  const { resolvedTheme } = useTheme();
  const textColor = resolvedTheme === 'dark' ? '#a1a1aa' : '#52525b';
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey={xKey} tick={{ fill: textColor }} tickLine={{ stroke: textColor }} />
        <YAxis tick={{ fill: textColor }} tickLine={{ stroke: textColor }} />
        <Tooltip
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
        {yKeys.map((key, index) => (
          <Bar
            key={key}
            dataKey={key}
            fill={colors[index % colors.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
```

#### 1.3 Line Chart

```typescript
// frontend/src/components/charts/LineChartComponent.tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface LineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  yKeys: string[];
  colors?: string[];
}

const defaultColors = [
  'hsl(var(--primary))',
  'hsl(210, 70%, 50%)',
  'hsl(150, 70%, 50%)',
  'hsl(30, 70%, 50%)',
];

export function LineChartComponent({ data, xKey, yKeys, colors = defaultColors }: LineChartProps) {
  const { resolvedTheme } = useTheme();
  const textColor = resolvedTheme === 'dark' ? '#a1a1aa' : '#52525b';
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey={xKey} tick={{ fill: textColor }} />
        <YAxis tick={{ fill: textColor }} />
        <Tooltip
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
        {yKeys.map((key, index) => (
          <Line
            key={key}
            type="monotone"
            dataKey={key}
            stroke={colors[index % colors.length]}
            strokeWidth={2}
            dot={{ fill: colors[index % colors.length] }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

#### 1.4 Pie Chart

```typescript
// frontend/src/components/charts/PieChartComponent.tsx
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface PieChartProps {
  data: { name: string; value: number }[];
  colors?: string[];
}

const defaultColors = [
  'hsl(var(--primary))',
  'hsl(210, 70%, 50%)',
  'hsl(150, 70%, 50%)',
  'hsl(30, 70%, 50%)',
  'hsl(280, 70%, 50%)',
  'hsl(0, 70%, 50%)',
];

export function PieChartComponent({ data, colors = defaultColors }: PieChartProps) {
  const { resolvedTheme } = useTheme();
  const gridColor = resolvedTheme === 'dark' ? '#27272a' : '#e4e4e7';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: resolvedTheme === 'dark' ? '#18181b' : '#ffffff',
            border: `1px solid ${gridColor}`,
            borderRadius: '8px',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

#### 1.5 KPI Card

```typescript
// frontend/src/components/charts/KPICard.tsx
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  previousValue?: number;
  format?: 'number' | 'currency' | 'percent';
  prefix?: string;
  suffix?: string;
}

export function KPICard({
  title,
  value,
  previousValue,
  format = 'number',
  prefix = '',
  suffix = '',
}: KPICardProps) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  const formatValue = (val: number) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const change = previousValue ? ((numValue - previousValue) / previousValue) * 100 : null;
  
  const TrendIcon = change === null 
    ? Minus 
    : change > 0 
      ? ArrowUp 
      : change < 0 
        ? ArrowDown 
        : Minus;

  const trendColor = change === null
    ? 'text-muted-foreground'
    : change > 0
      ? 'text-green-500'
      : change < 0
        ? 'text-red-500'
        : 'text-muted-foreground';

  return (
    <div className="flex h-full flex-col justify-center p-4">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-3xl font-bold">
          {prefix}
          {formatValue(numValue)}
          {suffix}
        </span>
        {change !== null && (
          <span className={cn('flex items-center text-sm', trendColor)}>
            <TrendIcon className="mr-1 h-4 w-4" />
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}
```

#### 1.6 Data Table

```typescript
// frontend/src/components/charts/DataTable.tsx
import { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface DataTableProps {
  data: Record<string, unknown>[];
  columns?: string[];
}

export function DataTable({ data, columns }: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const cols = columns || (data.length > 0 ? Object.keys(data[0]) : []);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn) return 0;
    const aVal = a[sortColumn];
    const bVal = b[sortColumn];
    
    if (aVal === bVal) return 0;
    if (aVal === null || aVal === undefined) return 1;
    if (bVal === null || bVal === undefined) return -1;
    
    const comparison = aVal < bVal ? -1 : 1;
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  return (
    <div className="h-full overflow-auto">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-card">
          <tr className="border-b">
            {cols.map((col) => (
              <th
                key={col}
                className="cursor-pointer px-4 py-2 text-left font-medium hover:bg-accent"
                onClick={() => handleSort(col)}
              >
                <span className="flex items-center gap-1">
                  {col}
                  {sortColumn === col && (
                    sortDirection === 'asc' 
                      ? <ChevronUp className="h-4 w-4" />
                      : <ChevronDown className="h-4 w-4" />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr key={index} className="border-b hover:bg-muted/50">
              {cols.map((col) => (
                <td key={col} className="px-4 py-2">
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### Step 2: AI Chart Suggestion

#### 2.1 Chart Type Detection

```typescript
// frontend/src/lib/chartSuggestion.ts
export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'kpi' | 'table';

interface ChartSuggestion {
  type: ChartType;
  confidence: number;
  xKey?: string;
  yKeys?: string[];
  reason: string;
}

function isNumericColumn(data: Record<string, unknown>[], key: string): boolean {
  return data.every(row => {
    const val = row[key];
    return val === null || val === undefined || typeof val === 'number' || !isNaN(Number(val));
  });
}

function isDateColumn(data: Record<string, unknown>[], key: string): boolean {
  const datePatterns = [
    /^\d{4}-\d{2}-\d{2}/, // YYYY-MM-DD
    /^\d{2}\/\d{2}\/\d{4}/, // MM/DD/YYYY
    /^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i, // Month names
  ];
  
  return data.slice(0, 5).every(row => {
    const val = String(row[key] || '');
    return datePatterns.some(pattern => pattern.test(val));
  });
}

function getUniqueCount(data: Record<string, unknown>[], key: string): number {
  const unique = new Set(data.map(row => row[key]));
  return unique.size;
}

export function suggestChartType(data: Record<string, unknown>[]): ChartSuggestion {
  if (!data || data.length === 0) {
    return { type: 'table', confidence: 1, reason: 'No data to visualize' };
  }

  const columns = Object.keys(data[0]);
  
  // Single value = KPI
  if (data.length === 1 && columns.length <= 2) {
    const numericCols = columns.filter(col => isNumericColumn(data, col));
    if (numericCols.length === 1) {
      return {
        type: 'kpi',
        confidence: 0.9,
        yKeys: numericCols,
        reason: 'Single numeric value detected',
      };
    }
  }

  // Find categorical and numeric columns
  const categoricalCols = columns.filter(col => !isNumericColumn(data, col));
  const numericCols = columns.filter(col => isNumericColumn(data, col));
  const dateCols = columns.filter(col => isDateColumn(data, col));

  // Time series = Line chart
  if (dateCols.length > 0 && numericCols.length > 0) {
    return {
      type: 'line',
      confidence: 0.85,
      xKey: dateCols[0],
      yKeys: numericCols.slice(0, 3),
      reason: 'Time series data detected',
    };
  }

  // Few categories with numeric values = Pie chart
  if (categoricalCols.length === 1 && numericCols.length === 1) {
    const uniqueCategories = getUniqueCount(data, categoricalCols[0]);
    if (uniqueCategories <= 8 && uniqueCategories === data.length) {
      return {
        type: 'pie',
        confidence: 0.8,
        xKey: categoricalCols[0],
        yKeys: numericCols,
        reason: 'Categorical distribution with small number of categories',
      };
    }
  }

  // Categories with numeric values = Bar chart
  if (categoricalCols.length >= 1 && numericCols.length >= 1) {
    return {
      type: 'bar',
      confidence: 0.75,
      xKey: categoricalCols[0],
      yKeys: numericCols.slice(0, 3),
      reason: 'Categorical comparison data',
    };
  }

  // Two numeric columns = Scatter
  if (numericCols.length >= 2 && categoricalCols.length === 0) {
    return {
      type: 'scatter',
      confidence: 0.7,
      xKey: numericCols[0],
      yKeys: [numericCols[1]],
      reason: 'Two numeric dimensions suitable for correlation',
    };
  }

  // Default to table
  return {
    type: 'table',
    confidence: 0.5,
    reason: 'Complex data structure, showing as table',
  };
}
```

#### 2.2 Chart Renderer

```typescript
// frontend/src/components/charts/ChartRenderer.tsx
import { useMemo } from 'react';
import { BarChartComponent } from './BarChartComponent';
import { LineChartComponent } from './LineChartComponent';
import { PieChartComponent } from './PieChartComponent';
import { KPICard } from './KPICard';
import { DataTable } from './DataTable';
import { suggestChartType, ChartType } from '@/lib/chartSuggestion';

interface ChartConfig {
  type: ChartType;
  xKey?: string;
  yKeys?: string[];
  title?: string;
}

interface ChartRendererProps {
  data: Record<string, unknown>[];
  config?: Partial<ChartConfig>;
  autoSuggest?: boolean;
}

export function ChartRenderer({ data, config, autoSuggest = true }: ChartRendererProps) {
  const suggestion = useMemo(() => suggestChartType(data), [data]);
  
  const chartType = config?.type || (autoSuggest ? suggestion.type : 'table');
  const xKey = config?.xKey || suggestion.xKey;
  const yKeys = config?.yKeys || suggestion.yKeys || [];

  switch (chartType) {
    case 'bar':
      return xKey && yKeys.length > 0 ? (
        <BarChartComponent data={data} xKey={xKey} yKeys={yKeys} />
      ) : (
        <DataTable data={data} />
      );

    case 'line':
      return xKey && yKeys.length > 0 ? (
        <LineChartComponent data={data} xKey={xKey} yKeys={yKeys} />
      ) : (
        <DataTable data={data} />
      );

    case 'pie':
      if (xKey && yKeys.length > 0) {
        const pieData = data.map(row => ({
          name: String(row[xKey]),
          value: Number(row[yKeys[0]]) || 0,
        }));
        return <PieChartComponent data={pieData} />;
      }
      return <DataTable data={data} />;

    case 'kpi':
      if (yKeys.length > 0 && data.length > 0) {
        return (
          <KPICard
            title={config?.title || yKeys[0]}
            value={Number(data[0][yKeys[0]]) || 0}
          />
        );
      }
      return <DataTable data={data} />;

    case 'table':
    default:
      return <DataTable data={data} />;
  }
}
```

---

### Step 3: Dashboard System

#### 3.1 Dashboard Types

```typescript
// frontend/src/types/dashboard.ts
export interface DashboardWidget {
  id: number;
  dashboard_id: number;
  widget_type: 'bar_chart' | 'line_chart' | 'pie_chart' | 'kpi_card' | 'table';
  title: string;
  query: string;
  chart_config: {
    xKey?: string;
    yKeys?: string[];
    colors?: string[];
  };
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  refresh_interval: number | null;
}

export interface Dashboard {
  id: number;
  name: string;
  description: string | null;
  layout: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  widgets?: DashboardWidget[];
}
```

#### 3.2 Dashboard Store

```typescript
// frontend/src/stores/dashboardStore.ts
import { create } from 'zustand';
import { Dashboard, DashboardWidget } from '@/types/dashboard';

interface DashboardState {
  currentDashboard: Dashboard | null;
  widgets: DashboardWidget[];
  isEditing: boolean;
  
  setCurrentDashboard: (dashboard: Dashboard | null) => void;
  setWidgets: (widgets: DashboardWidget[]) => void;
  updateWidgetPosition: (id: number, position: { x: number; y: number; w: number; h: number }) => void;
  setIsEditing: (editing: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  currentDashboard: null,
  widgets: [],
  isEditing: false,

  setCurrentDashboard: (dashboard) => set({ currentDashboard: dashboard }),
  setWidgets: (widgets) => set({ widgets }),
  updateWidgetPosition: (id, position) =>
    set((state) => ({
      widgets: state.widgets.map((w) =>
        w.id === id ? { ...w, position } : w
      ),
    })),
  setIsEditing: (isEditing) => set({ isEditing }),
}));
```

#### 3.3 Dashboard Grid

```typescript
// frontend/src/components/dashboard/DashboardGrid.tsx
import { useCallback } from 'react';
import GridLayout, { Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { useDashboardStore } from '@/stores/dashboardStore';
import { DashboardWidgetComponent } from './DashboardWidget';

export function DashboardGrid() {
  const { widgets, isEditing, updateWidgetPosition } = useDashboardStore();

  const layout: Layout[] = widgets.map((widget) => ({
    i: String(widget.id),
    x: widget.position.x,
    y: widget.position.y,
    w: widget.position.w,
    h: widget.position.h,
    minW: 2,
    minH: 2,
  }));

  const handleLayoutChange = useCallback(
    (newLayout: Layout[]) => {
      if (!isEditing) return;
      
      newLayout.forEach((item) => {
        const widget = widgets.find((w) => String(w.id) === item.i);
        if (widget) {
          const positionChanged =
            widget.position.x !== item.x ||
            widget.position.y !== item.y ||
            widget.position.w !== item.w ||
            widget.position.h !== item.h;

          if (positionChanged) {
            updateWidgetPosition(widget.id, {
              x: item.x,
              y: item.y,
              w: item.w,
              h: item.h,
            });
          }
        }
      });
    },
    [widgets, isEditing, updateWidgetPosition]
  );

  return (
    <GridLayout
      className="layout"
      layout={layout}
      cols={12}
      rowHeight={80}
      width={1200}
      isDraggable={isEditing}
      isResizable={isEditing}
      onLayoutChange={handleLayoutChange}
      draggableHandle=".drag-handle"
    >
      {widgets.map((widget) => (
        <div key={widget.id} className="h-full">
          <DashboardWidgetComponent widget={widget} />
        </div>
      ))}
    </GridLayout>
  );
}
```

#### 3.4 Dashboard Widget Component

```typescript
// frontend/src/components/dashboard/DashboardWidget.tsx
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { GripHorizontal, Trash2, Settings } from 'lucide-react';
import { api } from '@/api/client';
import { DashboardWidget } from '@/types/dashboard';
import { ChartRenderer } from '@/components/charts/ChartRenderer';
import { ChartWrapper } from '@/components/charts/ChartWrapper';
import { Button } from '@/components/ui/Button';
import { useDashboardStore } from '@/stores/dashboardStore';

interface DashboardWidgetComponentProps {
  widget: DashboardWidget;
}

interface QueryResult {
  data: Record<string, unknown>[];
  columns: string[];
}

export function DashboardWidgetComponent({ widget }: DashboardWidgetComponentProps) {
  const { isEditing } = useDashboardStore();
  const [lastRefresh, setLastRefresh] = useState(Date.now());

  // Fetch widget data
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['widget-data', widget.id, lastRefresh],
    queryFn: async () => {
      const response = await api.post<QueryResult>('/queries/execute', {
        query: widget.query,
      });
      return response;
    },
    refetchInterval: widget.refresh_interval ? widget.refresh_interval * 1000 : false,
  });

  const handleRefresh = () => {
    setLastRefresh(Date.now());
    refetch();
  };

  const chartConfig = {
    type: widget.widget_type.replace('_chart', '').replace('_card', '') as any,
    xKey: widget.chart_config?.xKey,
    yKeys: widget.chart_config?.yKeys,
    title: widget.title,
  };

  return (
    <div className="relative h-full">
      {isEditing && (
        <div className="drag-handle absolute left-0 right-0 top-0 z-10 flex h-6 cursor-move items-center justify-center bg-muted/50">
          <GripHorizontal className="h-4 w-4 text-muted-foreground" />
        </div>
      )}
      
      <ChartWrapper
        title={widget.title}
        onRefresh={handleRefresh}
        isRefreshing={isLoading}
      >
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : data?.data ? (
          <ChartRenderer data={data.data} config={chartConfig} />
        ) : (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            No data available
          </div>
        )}
      </ChartWrapper>

      {isEditing && (
        <div className="absolute right-2 top-8 z-10 flex gap-1">
          <Button variant="ghost" size="icon" className="h-6 w-6">
            <Settings className="h-3 w-3" />
          </Button>
          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive">
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
}
```

#### 3.5 Dashboard Page

```typescript
// frontend/src/pages/DashboardsPage.tsx
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Save, X } from 'lucide-react';
import { api } from '@/api/client';
import { Dashboard, DashboardWidget } from '@/types/dashboard';
import { Button } from '@/components/ui/Button';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { useDashboardStore } from '@/stores/dashboardStore';
import * as Select from '@radix-ui/react-select';

interface DashboardsResponse {
  dashboards: Dashboard[];
  total: number;
}

export function DashboardsPage() {
  const queryClient = useQueryClient();
  const { 
    currentDashboard, 
    setCurrentDashboard, 
    setWidgets, 
    isEditing, 
    setIsEditing,
    widgets,
  } = useDashboardStore();

  // Fetch dashboards
  const { data: dashboardsData } = useQuery({
    queryKey: ['dashboards'],
    queryFn: () => api.get<DashboardsResponse>('/dashboards'),
  });

  // Fetch widgets for current dashboard
  const { data: widgetsData } = useQuery({
    queryKey: ['dashboard-widgets', currentDashboard?.id],
    queryFn: () => api.get<{ widgets: DashboardWidget[] }>(`/dashboards/${currentDashboard?.id}/widgets`),
    enabled: !!currentDashboard?.id,
  });

  // Update widgets when data changes
  useEffect(() => {
    if (widgetsData?.widgets) {
      setWidgets(widgetsData.widgets);
    }
  }, [widgetsData, setWidgets]);

  // Set default dashboard
  useEffect(() => {
    if (dashboardsData?.dashboards && !currentDashboard) {
      const defaultDash = dashboardsData.dashboards.find(d => d.is_default) 
        || dashboardsData.dashboards[0];
      if (defaultDash) {
        setCurrentDashboard(defaultDash);
      }
    }
  }, [dashboardsData, currentDashboard, setCurrentDashboard]);

  // Save layout mutation
  const saveLayoutMutation = useMutation({
    mutationFn: async () => {
      const updates = widgets.map(w => ({
        id: w.id,
        position: w.position,
      }));
      return api.put(`/dashboards/${currentDashboard?.id}/layout`, { widgets: updates });
    },
    onSuccess: () => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['dashboard-widgets'] });
    },
  });

  const handleSave = () => {
    saveLayoutMutation.mutate();
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reload original widgets
    if (widgetsData?.widgets) {
      setWidgets(widgetsData.widgets);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Dashboards</h1>
          
          {/* Dashboard Selector */}
          <Select.Root
            value={currentDashboard?.id?.toString()}
            onValueChange={(value) => {
              const dash = dashboardsData?.dashboards.find(d => d.id === parseInt(value));
              if (dash) setCurrentDashboard(dash);
            }}
          >
            <Select.Trigger className="inline-flex items-center gap-2 rounded-md border px-3 py-2">
              <Select.Value placeholder="Select dashboard" />
            </Select.Trigger>
            <Select.Portal>
              <Select.Content className="rounded-md border bg-card shadow-md">
                <Select.Viewport className="p-1">
                  {dashboardsData?.dashboards.map((dash) => (
                    <Select.Item
                      key={dash.id}
                      value={dash.id.toString()}
                      className="cursor-pointer rounded-sm px-2 py-1.5 outline-none hover:bg-accent"
                    >
                      <Select.ItemText>{dash.name}</Select.ItemText>
                    </Select.Item>
                  ))}
                </Select.Viewport>
              </Select.Content>
            </Select.Portal>
          </Select.Root>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button variant="outline" onClick={handleCancel}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saveLayoutMutation.isPending}>
                <Save className="mr-2 h-4 w-4" />
                Save Layout
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Layout
              </Button>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Widget
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Dashboard Grid */}
      {currentDashboard ? (
        <DashboardGrid />
      ) : (
        <div className="flex h-64 items-center justify-center text-muted-foreground">
          No dashboard selected. Create one to get started.
        </div>
      )}
    </div>
  );
}
```

---

### Step 4: Pin to Dashboard Dialog

```typescript
// frontend/src/components/dialogs/PinToDashboardDialog.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { api } from '@/api/client';
import { Dashboard } from '@/types/dashboard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { ChartType } from '@/lib/chartSuggestion';

interface PinToDashboardDialogProps {
  open: boolean;
  onClose: () => void;
  query: string;
  suggestedType: ChartType;
  data: Record<string, unknown>[];
  xKey?: string;
  yKeys?: string[];
}

export function PinToDashboardDialog({
  open,
  onClose,
  query,
  suggestedType,
  data,
  xKey,
  yKeys,
}: PinToDashboardDialogProps) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [selectedDashboard, setSelectedDashboard] = useState<number | null>(null);
  const [chartType, setChartType] = useState(suggestedType);

  const { data: dashboards } = useQuery({
    queryKey: ['dashboards'],
    queryFn: () => api.get<{ dashboards: Dashboard[] }>('/dashboards'),
  });

  const pinMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/dashboards/${selectedDashboard}/widgets`, {
        widget_type: chartType === 'kpi' ? 'kpi_card' : `${chartType}_chart`,
        title,
        query,
        chart_config: { xKey, yKeys },
        position: { x: 0, y: 0, w: 4, h: 3 },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-widgets'] });
      onClose();
    },
  });

  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="text-lg font-semibold">Pin to Dashboard</Dialog.Title>
          
          <div className="mt-4 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Widget title"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Dashboard</label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2"
                value={selectedDashboard || ''}
                onChange={(e) => setSelectedDashboard(parseInt(e.target.value))}
              >
                <option value="">Select a dashboard</option>
                {dashboards?.dashboards.map((dash) => (
                  <option key={dash.id} value={dash.id}>
                    {dash.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">Chart Type</label>
              <select
                className="w-full rounded-md border bg-background px-3 py-2"
                value={chartType}
                onChange={(e) => setChartType(e.target.value as ChartType)}
              >
                <option value="bar">Bar Chart</option>
                <option value="line">Line Chart</option>
                <option value="pie">Pie Chart</option>
                <option value="kpi">KPI Card</option>
                <option value="table">Table</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => pinMutation.mutate()}
              disabled={!title || !selectedDashboard || pinMutation.isPending}
            >
              Pin Widget
            </Button>
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

---

### Step 5: Backend Dashboard API

```python
# src/api/routes/dashboards.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from src.api.deps import get_db
from src.api.models.database import Dashboard, DashboardWidget

router = APIRouter()


class WidgetPosition(BaseModel):
    x: int
    y: int
    w: int
    h: int


class ChartConfig(BaseModel):
    xKey: Optional[str] = None
    yKeys: Optional[List[str]] = None
    colors: Optional[List[str]] = None


class WidgetCreate(BaseModel):
    widget_type: str
    title: str
    query: str
    chart_config: Optional[ChartConfig] = None
    position: WidgetPosition
    refresh_interval: Optional[int] = None


class WidgetResponse(BaseModel):
    id: int
    dashboard_id: int
    widget_type: str
    title: str
    query: str
    chart_config: Optional[dict]
    position: dict
    refresh_interval: Optional[int]
    
    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DashboardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("", response_model=dict)
async def list_dashboards(db: AsyncSession = Depends(get_db)):
    """List all dashboards."""
    query = select(Dashboard).order_by(Dashboard.created_at.desc())
    result = await db.execute(query)
    dashboards = result.scalars().all()
    return {
        "dashboards": [DashboardResponse.model_validate(d) for d in dashboards],
        "total": len(dashboards),
    }


@router.post("", response_model=DashboardResponse)
async def create_dashboard(
    data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new dashboard."""
    dashboard = Dashboard(
        name=data.name,
        description=data.description,
    )
    db.add(dashboard)
    await db.commit()
    await db.refresh(dashboard)
    return DashboardResponse.model_validate(dashboard)


@router.get("/{dashboard_id}/widgets", response_model=dict)
async def get_dashboard_widgets(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get widgets for a dashboard."""
    query = select(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id)
    result = await db.execute(query)
    widgets = result.scalars().all()
    
    return {
        "widgets": [
            {
                "id": w.id,
                "dashboard_id": w.dashboard_id,
                "widget_type": w.widget_type,
                "title": w.title,
                "query": w.query,
                "chart_config": json.loads(w.chart_config) if w.chart_config else None,
                "position": json.loads(w.position) if w.position else {"x": 0, "y": 0, "w": 4, "h": 3},
                "refresh_interval": w.refresh_interval,
            }
            for w in widgets
        ]
    }


@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse)
async def create_widget(
    dashboard_id: int,
    data: WidgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new widget."""
    import json
    
    widget = DashboardWidget(
        dashboard_id=dashboard_id,
        widget_type=data.widget_type,
        title=data.title,
        query=data.query,
        chart_config=json.dumps(data.chart_config.model_dump() if data.chart_config else {}),
        position=json.dumps(data.position.model_dump()),
        refresh_interval=data.refresh_interval,
    )
    db.add(widget)
    await db.commit()
    await db.refresh(widget)
    
    return WidgetResponse(
        id=widget.id,
        dashboard_id=widget.dashboard_id,
        widget_type=widget.widget_type,
        title=widget.title,
        query=widget.query,
        chart_config=json.loads(widget.chart_config) if widget.chart_config else None,
        position=json.loads(widget.position),
        refresh_interval=widget.refresh_interval,
    )


@router.put("/{dashboard_id}/layout")
async def update_layout(
    dashboard_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update widget positions."""
    import json
    
    for widget_update in data.get("widgets", []):
        widget = await db.get(DashboardWidget, widget_update["id"])
        if widget and widget.dashboard_id == dashboard_id:
            widget.position = json.dumps(widget_update["position"])
    
    await db.commit()
    return {"status": "updated"}


@router.delete("/{dashboard_id}/widgets/{widget_id}")
async def delete_widget(
    dashboard_id: int,
    widget_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a widget."""
    widget = await db.get(DashboardWidget, widget_id)
    if not widget or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    await db.delete(widget)
    await db.commit()
    return {"status": "deleted"}
```

---

### Step 6: Query Execution Endpoint

```python
# src/api/routes/queries.py (add to existing file)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Any
import time

from src.api.deps import get_db
from src.api.models.database import QueryHistory

router = APIRouter()


class QueryExecute(BaseModel):
    query: str


class QueryResult(BaseModel):
    data: List[dict]
    columns: List[str]
    row_count: int
    execution_time_ms: int


@router.post("/execute", response_model=QueryResult)
async def execute_query(
    data: QueryExecute,
    db: AsyncSession = Depends(get_db),
):
    """Execute a SQL query and return results."""
    start_time = time.time()
    
    try:
        result = await db.execute(text(data.query))
        rows = result.fetchall()
        columns = list(result.keys())
        
        # Convert to list of dicts
        data_list = [dict(zip(columns, row)) for row in rows]
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return QueryResult(
            data=data_list,
            columns=columns,
            row_count=len(data_list),
            execution_time_ms=execution_time,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## File Structure After Phase 2.3

```
frontend/src/
├── components/
│   ├── charts/
│   │   ├── BarChartComponent.tsx
│   │   ├── LineChartComponent.tsx
│   │   ├── PieChartComponent.tsx
│   │   ├── KPICard.tsx
│   │   ├── DataTable.tsx
│   │   ├── ChartWrapper.tsx
│   │   ├── ChartRenderer.tsx
│   │   └── index.ts
│   ├── dashboard/
│   │   ├── DashboardGrid.tsx
│   │   ├── DashboardWidget.tsx
│   │   └── index.ts
│   └── dialogs/
│       └── PinToDashboardDialog.tsx
├── lib/
│   ├── utils.ts
│   └── chartSuggestion.ts
├── pages/
│   └── DashboardsPage.tsx
├── stores/
│   └── dashboardStore.ts
└── types/
    └── dashboard.ts
```

---

## Validation Checkpoints

1. **Charts render correctly:**
   - Bar chart with categorical data
   - Line chart with time series
   - Pie chart with distribution
   - KPI card with single value

2. **AI suggestion works:**
   - Time series → Line chart
   - Categories → Bar chart
   - Single value → KPI card

3. **Dashboard grid:**
   - Widgets display in grid
   - Edit mode enables drag/resize
   - Layout saves correctly

4. **Pin to dashboard:**
   - Dialog opens from chat result
   - Widget created on dashboard
   - Data loads in widget

5. **Auto-refresh:**
   - Widget with interval refreshes
   - Loading indicator shows

---

## Notes for Implementation

- Use `ResponsiveContainer` for all Recharts components
- Theme colors should use CSS variables for dark/light mode
- Keep chart components pure - data transformation in parent
- Widget positions use 12-column grid (x: 0-11, w: 1-12)
- Default widget size: w=4, h=3 (1/3 width, medium height)
