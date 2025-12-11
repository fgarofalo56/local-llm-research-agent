import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Dialog from '@radix-ui/react-dialog';
import { X, Pin, BarChart3, LineChart, PieChart, Table, TrendingUp, ScatterChart as ScatterIcon } from 'lucide-react';
import { api } from '@/api/client';
import type { Dashboard, WidgetCreate } from '@/types/dashboard';
import { chartTypeToWidgetType } from '@/types/dashboard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { type ChartType, getAvailableChartTypes } from '@/lib/chartSuggestion';

interface PinToDashboardDialogProps {
  open: boolean;
  onClose: () => void;
  query: string;
  suggestedType: ChartType;
  data: Record<string, unknown>[];
  xKey?: string;
  yKeys?: string[];
}

interface DashboardsResponse {
  dashboards: Dashboard[];
  total: number;
}

const chartIcons: Record<ChartType, React.ElementType> = {
  bar: BarChart3,
  line: LineChart,
  area: TrendingUp,
  pie: PieChart,
  scatter: ScatterIcon,
  kpi: TrendingUp,
  table: Table,
};

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
  const [chartType, setChartType] = useState<ChartType>(suggestedType);
  const [refreshInterval, setRefreshInterval] = useState<string>('');

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setTitle('');
      setChartType(suggestedType);
      setRefreshInterval('');
    }
  }, [open, suggestedType]);

  // Fetch dashboards
  const { data: dashboardsData, isLoading } = useQuery({
    queryKey: ['dashboards'],
    queryFn: () => api.get<DashboardsResponse>('/dashboards'),
    enabled: open,
  });

  // Set default dashboard
  useEffect(() => {
    if (dashboardsData?.dashboards && dashboardsData.dashboards.length > 0 && !selectedDashboard) {
      const defaultDash = dashboardsData.dashboards.find(d => d.is_default)
        || dashboardsData.dashboards[0];
      setSelectedDashboard(defaultDash.id);
    }
  }, [dashboardsData, selectedDashboard]);

  // Pin widget mutation
  const pinMutation = useMutation({
    mutationFn: async () => {
      if (!selectedDashboard) return;

      const widgetData: WidgetCreate = {
        widget_type: chartTypeToWidgetType(chartType),
        title,
        query,
        chart_config: { xKey, yKeys },
        position: { x: 0, y: 0, w: 4, h: 3 },
        refresh_interval: refreshInterval ? parseInt(refreshInterval) : null,
      };

      return api.post(`/dashboards/${selectedDashboard}/widgets`, widgetData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-widgets'] });
      onClose();
    },
  });

  const chartTypes = getAvailableChartTypes();

  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold">
            <Pin className="h-5 w-5" />
            Pin to Dashboard
          </Dialog.Title>
          <Dialog.Description className="mt-2 text-sm text-muted-foreground">
            Create a widget from this query result and add it to a dashboard.
          </Dialog.Description>

          <div className="mt-4 space-y-4">
            {/* Title */}
            <div>
              <label className="mb-1 block text-sm font-medium">Widget Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter widget title"
              />
            </div>

            {/* Dashboard Selection */}
            <div>
              <label className="mb-1 block text-sm font-medium">Dashboard</label>
              {isLoading ? (
                <div className="text-sm text-muted-foreground">Loading dashboards...</div>
              ) : dashboardsData?.dashboards && dashboardsData.dashboards.length > 0 ? (
                <select
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={selectedDashboard || ''}
                  onChange={(e) => setSelectedDashboard(parseInt(e.target.value))}
                >
                  {dashboardsData.dashboards.map((dash) => (
                    <option key={dash.id} value={dash.id}>
                      {dash.name}
                      {dash.is_default ? ' (default)' : ''}
                    </option>
                  ))}
                </select>
              ) : (
                <div className="text-sm text-muted-foreground">
                  No dashboards available. Create a dashboard first.
                </div>
              )}
            </div>

            {/* Chart Type */}
            <div>
              <label className="mb-1 block text-sm font-medium">
                Chart Type
                {chartType === suggestedType && (
                  <span className="ml-2 text-xs text-muted-foreground">(suggested)</span>
                )}
              </label>
              <div className="grid grid-cols-4 gap-2">
                {chartTypes.map(({ value, label }) => {
                  const Icon = chartIcons[value];
                  return (
                    <button
                      key={value}
                      type="button"
                      className={`flex flex-col items-center justify-center rounded-md border p-2 text-xs transition-colors ${
                        chartType === value
                          ? 'border-primary bg-primary/10 text-primary'
                          : 'hover:bg-accent'
                      }`}
                      onClick={() => setChartType(value)}
                    >
                      <Icon className="mb-1 h-4 w-4" />
                      {label.replace(' Chart', '').replace(' Plot', '')}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Auto Refresh */}
            <div>
              <label className="mb-1 block text-sm font-medium">
                Auto-refresh interval (seconds)
                <span className="ml-2 text-xs text-muted-foreground">(optional)</span>
              </label>
              <Input
                type="number"
                min="10"
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(e.target.value)}
                placeholder="e.g., 60 for 1 minute"
              />
            </div>

            {/* Preview info */}
            <div className="rounded-md bg-muted p-3">
              <p className="text-xs text-muted-foreground">
                <strong>Data preview:</strong> {data.length} row(s)
                {xKey && <span> • X: {xKey}</span>}
                {yKeys && yKeys.length > 0 && <span> • Y: {yKeys.join(', ')}</span>}
              </p>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => pinMutation.mutate()}
              disabled={
                !title.trim() ||
                !selectedDashboard ||
                pinMutation.isPending ||
                (dashboardsData?.dashboards?.length || 0) === 0
              }
            >
              {pinMutation.isPending ? 'Pinning...' : 'Pin Widget'}
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
