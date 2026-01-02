import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { ChartRenderer } from '../ChartRenderer';

// Mock chart suggestion
vi.mock('@/lib/chartSuggestion', () => ({
  suggestChartType: vi.fn(() => ({
    type: 'table',
    xKey: 'name',
    yKeys: ['value'],
  })),
}));

// Mock Recharts components to avoid rendering issues in tests
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

describe('ChartRenderer', () => {
  const testData = [
    { name: 'A', value: 100 },
    { name: 'B', value: 200 },
    { name: 'C', value: 300 },
  ];

  it('shows empty state when data is empty', () => {
    render(<ChartRenderer data={[]} />);

    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('shows empty state when data is undefined', () => {
    render(<ChartRenderer data={undefined as unknown as Record<string, unknown>[]} />);

    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders table by default when autoSuggest is false', () => {
    render(<ChartRenderer data={testData} autoSuggest={false} />);

    // Should render a table
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders table when chart type is table', () => {
    render(<ChartRenderer data={testData} config={{ type: 'table' }} />);

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders bar chart when configured', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'bar', xKey: 'name', yKeys: ['value'] }}
      />
    );

    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('renders line chart when configured', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'line', xKey: 'name', yKeys: ['value'] }}
      />
    );

    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders area chart when configured', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'area', xKey: 'name', yKeys: ['value'] }}
      />
    );

    expect(screen.getByTestId('area-chart')).toBeInTheDocument();
  });

  it('renders pie chart when configured', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'pie', xKey: 'name', yKeys: ['value'] }}
      />
    );

    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });

  it('renders scatter chart when configured', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'scatter', xKey: 'name', yKeys: ['value'] }}
      />
    );

    expect(screen.getByTestId('scatter-chart')).toBeInTheDocument();
  });

  it('renders KPI card when configured', () => {
    render(
      <ChartRenderer
        data={[{ metric: 500 }]}
        config={{ type: 'kpi', yKeys: ['metric'], title: 'Total' }}
      />
    );

    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();
  });

  it('renders bar chart even when xKey comes from suggestion', () => {
    // When xKey is not provided, it's populated from suggestion
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'bar', yKeys: ['value'] }}
      />
    );

    // Since our mock suggestChartType returns xKey: 'name', bar chart renders
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
  });

  it('falls back to table when bar chart has no yKeys', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'bar', xKey: 'name', yKeys: [] }}
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('handles unknown chart type by rendering table', () => {
    render(
      <ChartRenderer
        data={testData}
        config={{ type: 'unknown' as 'table' }}
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders table with correct data', () => {
    render(<ChartRenderer data={testData} config={{ type: 'table' }} />);

    // Check table contains data
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByText('B')).toBeInTheDocument();
    expect(screen.getByText('C')).toBeInTheDocument();
  });
});
