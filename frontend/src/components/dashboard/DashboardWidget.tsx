import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GripHorizontal, Trash2, Settings, RefreshCw } from 'lucide-react';
import { api } from '@/api/client';
import type { DashboardWidget } from '@/types/dashboard';
import { widgetTypeToChartType } from '@/types/dashboard';
import { ChartRenderer } from '@/components/charts/ChartRenderer';
import { ChartWrapper } from '@/components/charts/ChartWrapper';
import { Button } from '@/components/ui/Button';
import { useDashboardStore } from '@/stores/dashboardStore';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';

interface DashboardWidgetComponentProps {
  widget: DashboardWidget;
}

interface QueryResult {
  data: Record<string, unknown>[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
}

export function DashboardWidgetComponent({ widget }: DashboardWidgetComponentProps) {
  const queryClient = useQueryClient();
  const { isEditing, removeWidget, currentDashboard } = useDashboardStore();
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Fetch widget data
  const {
    data,
    isLoading,
    refetch,
    isRefetching,
    error,
  } = useQuery({
    queryKey: ['widget-data', widget.id, widget.query],
    queryFn: async () => {
      const response = await api.post<QueryResult>('/queries/execute', {
        query: widget.query,
      });
      return response;
    },
    refetchInterval: widget.refresh_interval ? widget.refresh_interval * 1000 : false,
    staleTime: 30000, // Consider data fresh for 30 seconds
    retry: 1,
  });

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  // Delete widget mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!currentDashboard) return;
      return api.delete(`/dashboards/${currentDashboard.id}/widgets/${widget.id}`);
    },
    onSuccess: () => {
      removeWidget(widget.id);
      queryClient.invalidateQueries({ queryKey: ['dashboard-widgets'] });
      setShowDeleteConfirm(false);
    },
  });

  const chartConfig = {
    type: widgetTypeToChartType(widget.widget_type),
    xKey: widget.chart_config?.xKey,
    yKeys: widget.chart_config?.yKeys,
    title: widget.title,
    colors: widget.chart_config?.colors,
  };

  return (
    <div className="relative h-full">
      {/* Drag handle */}
      {isEditing && (
        <div className="drag-handle absolute left-0 right-0 top-0 z-10 flex h-6 cursor-move items-center justify-center rounded-t-lg bg-muted/80 backdrop-blur">
          <GripHorizontal className="h-4 w-4 text-muted-foreground" />
        </div>
      )}

      <ChartWrapper
        title={widget.title}
        onRefresh={handleRefresh}
        isRefreshing={isLoading || isRefetching}
      >
        <div className={isEditing ? 'pt-4' : ''}>
          {isLoading ? (
            <div className="flex h-full items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : error ? (
            <div className="flex h-full flex-col items-center justify-center text-destructive">
              <p className="font-medium">Error loading data</p>
              <p className="text-sm text-muted-foreground">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={handleRefresh}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Retry
              </Button>
            </div>
          ) : data?.data ? (
            <ChartRenderer data={data.data} config={chartConfig} autoSuggest={false} />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No data available
            </div>
          )}
        </div>
      </ChartWrapper>

      {/* Edit mode controls */}
      {isEditing && (
        <div className="absolute right-2 top-8 z-10 flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 bg-background/80 backdrop-blur hover:bg-background"
            title="Widget settings"
          >
            <Settings className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 bg-background/80 text-destructive backdrop-blur hover:bg-background hover:text-destructive"
            title="Delete widget"
            onClick={() => setShowDeleteConfirm(true)}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog.Root open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
            <Dialog.Title className="text-lg font-semibold">Delete Widget</Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              Are you sure you want to delete "{widget.title}"? This action cannot be undone.
            </Dialog.Description>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowDeleteConfirm(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
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

      {/* Auto-refresh indicator */}
      {widget.refresh_interval && (
        <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
          Auto-refresh: {widget.refresh_interval}s
        </div>
      )}
    </div>
  );
}
