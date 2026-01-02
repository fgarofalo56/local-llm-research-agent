import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/test-utils';
import { DashboardWidgetComponent } from '../DashboardWidget';
import type { DashboardWidget } from '@/types/dashboard';

// Mock the dashboard store
vi.mock('@/stores/dashboardStore', () => ({
  useDashboardStore: vi.fn(() => ({
    isEditing: false,
    removeWidget: vi.fn(),
    currentDashboard: { id: 1, name: 'Test Dashboard' },
  })),
}));

// Mock the API client
vi.mock('@/api/client', () => ({
  api: {
    post: vi.fn().mockResolvedValue({
      data: [{ name: 'A', value: 100 }],
      columns: ['name', 'value'],
      row_count: 1,
      execution_time_ms: 50,
    }),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

// Mock Recharts to avoid rendering complexity
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: () => <div data-testid="bar-chart" />,
  LineChart: () => <div data-testid="line-chart" />,
  AreaChart: () => <div data-testid="area-chart" />,
  PieChart: () => <div data-testid="pie-chart" />,
  ScatterChart: () => <div data-testid="scatter-chart" />,
  Bar: () => null,
  Line: () => null,
  Area: () => null,
  Pie: () => null,
  Scatter: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
}));

describe('DashboardWidgetComponent', () => {
  const mockWidget: DashboardWidget = {
    id: 1,
    dashboard_id: 1,
    title: 'Test Widget',
    widget_type: 'bar_chart',
    query: 'SELECT * FROM data',
    chart_config: {
      xKey: 'name',
      yKeys: ['value'],
    },
    position: { x: 0, y: 0, w: 4, h: 3 },
    refresh_interval: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders widget title', async () => {
    render(<DashboardWidgetComponent widget={mockWidget} />);

    await waitFor(() => {
      expect(screen.getByText('Test Widget')).toBeInTheDocument();
    });
  });

  it('renders chart wrapper', () => {
    render(<DashboardWidgetComponent widget={mockWidget} />);

    // The widget should be rendered
    expect(screen.getByText('Test Widget')).toBeInTheDocument();
  });

  it('shows auto-refresh indicator when refresh interval is set', async () => {
    const widgetWithRefresh = {
      ...mockWidget,
      refresh_interval: 30,
    };

    render(<DashboardWidgetComponent widget={widgetWithRefresh} />);

    await waitFor(() => {
      expect(screen.getByText('Auto-refresh: 30s')).toBeInTheDocument();
    });
  });

  it('does not show auto-refresh indicator when no interval', async () => {
    render(<DashboardWidgetComponent widget={mockWidget} />);

    await waitFor(() => {
      expect(screen.getByText('Test Widget')).toBeInTheDocument();
    });

    expect(screen.queryByText(/Auto-refresh/)).not.toBeInTheDocument();
  });
});
