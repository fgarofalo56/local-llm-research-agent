import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit, Save, X, LayoutDashboard, Trash2, Download, Upload } from 'lucide-react';
import { api } from '@/api/client';
import type { Dashboard, DashboardWidget, DashboardCreate, WidgetCreate } from '@/types/dashboard';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { DashboardGrid } from '@/components/dashboard/DashboardGrid';
import { useDashboardStore } from '@/stores/dashboardStore';
import * as Select from '@radix-ui/react-select';
import * as Dialog from '@radix-ui/react-dialog';
import { ChevronDown, Check } from 'lucide-react';
import { exportDashboardToJson, importDashboardFromJson } from '@/lib/exports/jsonExport';
import { exportDashboardToPdf } from '@/lib/exports/pdfExport';

interface DashboardsResponse {
  dashboards: Dashboard[];
  total: number;
}

interface WidgetsResponse {
  widgets: DashboardWidget[];
}

export function DashboardsPage() {
  const queryClient = useQueryClient();
  const {
    currentDashboard,
    setCurrentDashboard,
    setWidgets,
    isEditing,
    widgets,
    hasUnsavedChanges,
    startEditing,
    cancelEditing,
    commitChanges,
  } = useDashboardStore();

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newDashboardName, setNewDashboardName] = useState('');
  const [newDashboardDescription, setNewDashboardDescription] = useState('');

  const dashboardGridRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch dashboards
  const { data: dashboardsData, isLoading: isDashboardsLoading } = useQuery({
    queryKey: ['dashboards'],
    queryFn: () => api.get<DashboardsResponse>('/dashboards'),
  });

  // Fetch widgets for current dashboard
  const { data: widgetsData, isLoading: isWidgetsLoading } = useQuery({
    queryKey: ['dashboard-widgets', currentDashboard?.id],
    queryFn: () => api.get<WidgetsResponse>(`/dashboards/${currentDashboard?.id}/widgets`),
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

  // Create dashboard mutation
  const createMutation = useMutation({
    mutationFn: async (data: DashboardCreate) => {
      return api.post<Dashboard>('/dashboards', data);
    },
    onSuccess: (newDashboard) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      setCurrentDashboard(newDashboard);
      setShowCreateDialog(false);
      setNewDashboardName('');
      setNewDashboardDescription('');
    },
  });

  // Delete dashboard mutation
  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!currentDashboard) return;
      return api.delete(`/dashboards/${currentDashboard.id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      setCurrentDashboard(null);
      setShowDeleteDialog(false);
    },
  });

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
      commitChanges();
      queryClient.invalidateQueries({ queryKey: ['dashboard-widgets'] });
    },
  });

  const handleSave = () => {
    saveLayoutMutation.mutate();
  };

  const handleCancel = () => {
    cancelEditing();
  };

  const handleCreateDashboard = () => {
    if (!newDashboardName.trim()) return;
    createMutation.mutate({
      name: newDashboardName.trim(),
      description: newDashboardDescription.trim() || null,
    });
  };

  // Import dashboard mutation
  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const importData = await importDashboardFromJson(file);

      // Create new dashboard
      const newDashboard = await api.post<Dashboard>('/dashboards', {
        name: `${importData.dashboard.name} (Imported)`,
        description: importData.dashboard.description,
      });

      // Create widgets
      for (const widget of importData.widgets) {
        await api.post<DashboardWidget>(`/dashboards/${newDashboard.id}/widgets`, {
          widget_type: widget.widget_type,
          title: widget.title,
          query: widget.query,
          chart_config: widget.chart_config,
          position: widget.position,
          refresh_interval: widget.refresh_interval,
        } as WidgetCreate);
      }

      return newDashboard;
    },
    onSuccess: (newDashboard) => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
      setCurrentDashboard(newDashboard);
    },
  });

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleExportJson = () => {
    if (currentDashboard) {
      exportDashboardToJson(currentDashboard, widgets);
    }
  };

  const handleExportPdf = async () => {
    if (dashboardGridRef.current && currentDashboard) {
      await exportDashboardToPdf(dashboardGridRef.current, currentDashboard.name);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Dashboards</h1>

          {/* Dashboard Selector */}
          {dashboardsData?.dashboards && dashboardsData.dashboards.length > 0 && (
            <Select.Root
              value={currentDashboard?.id?.toString()}
              onValueChange={(value) => {
                const dash = dashboardsData.dashboards.find(d => d.id === parseInt(value));
                if (dash) setCurrentDashboard(dash);
              }}
            >
              <Select.Trigger className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm hover:bg-accent">
                <LayoutDashboard className="h-4 w-4" />
                <Select.Value placeholder="Select dashboard" />
                <ChevronDown className="h-4 w-4 opacity-50" />
              </Select.Trigger>
              <Select.Portal>
                <Select.Content className="rounded-md border bg-card shadow-md z-50">
                  <Select.Viewport className="p-1">
                    {dashboardsData.dashboards.map((dash) => (
                      <Select.Item
                        key={dash.id}
                        value={dash.id.toString()}
                        className="relative flex cursor-pointer items-center rounded-sm px-8 py-1.5 text-sm outline-none hover:bg-accent"
                      >
                        <Select.ItemIndicator className="absolute left-2">
                          <Check className="h-4 w-4" />
                        </Select.ItemIndicator>
                        <Select.ItemText>
                          {dash.name}
                          {dash.is_default && (
                            <span className="ml-2 text-xs text-muted-foreground">(default)</span>
                          )}
                        </Select.ItemText>
                      </Select.Item>
                    ))}
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {/* Hidden file input for import */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleImport}
          />

          {isEditing ? (
            <>
              <Button variant="outline" onClick={handleCancel}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={saveLayoutMutation.isPending || !hasUnsavedChanges}
              >
                <Save className="mr-2 h-4 w-4" />
                {saveLayoutMutation.isPending ? 'Saving...' : 'Save Layout'}
              </Button>
            </>
          ) : (
            <>
              {currentDashboard && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={importMutation.isPending}
                  >
                    <Upload className="mr-2 h-4 w-4" />
                    {importMutation.isPending ? 'Importing...' : 'Import'}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleExportJson}>
                    <Download className="mr-2 h-4 w-4" />
                    Export JSON
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleExportPdf}>
                    <Download className="mr-2 h-4 w-4" />
                    Export PDF
                  </Button>
                  <Button variant="outline" onClick={() => setShowDeleteDialog(true)}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </Button>
                  <Button variant="outline" onClick={startEditing}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Layout
                  </Button>
                </>
              )}
              <Button onClick={() => setShowCreateDialog(true)}>
                <Plus className="mr-2 h-4 w-4" />
                New Dashboard
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Dashboard Grid */}
      {isDashboardsLoading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : currentDashboard ? (
        <div>
          {currentDashboard.description && (
            <p className="mb-4 text-sm text-muted-foreground">{currentDashboard.description}</p>
          )}
          {isWidgetsLoading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : (
            <div ref={dashboardGridRef}>
              <DashboardGrid />
            </div>
          )}
        </div>
      ) : (
        <div className="flex h-64 flex-col items-center justify-center text-muted-foreground">
          <LayoutDashboard className="mb-4 h-12 w-12" />
          <p className="text-lg font-medium">No dashboard selected</p>
          <p className="text-sm">Create a new dashboard to get started</p>
          <Button className="mt-4" onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Dashboard
          </Button>
        </div>
      )}

      {/* Create Dashboard Dialog */}
      <Dialog.Root open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
            <Dialog.Title className="text-lg font-semibold">Create Dashboard</Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              Create a new dashboard to organize your widgets and visualizations.
            </Dialog.Description>

            <div className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Name</label>
                <Input
                  value={newDashboardName}
                  onChange={(e) => setNewDashboardName(e.target.value)}
                  placeholder="My Dashboard"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Description (optional)</label>
                <Input
                  value={newDashboardDescription}
                  onChange={(e) => setNewDashboardDescription(e.target.value)}
                  placeholder="Dashboard description"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreateDashboard}
                disabled={!newDashboardName.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create'}
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

      {/* Delete Dashboard Dialog */}
      <Dialog.Root open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
            <Dialog.Title className="text-lg font-semibold">Delete Dashboard</Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              Are you sure you want to delete "{currentDashboard?.name}"? This will also delete all
              widgets on this dashboard. This action cannot be undone.
            </Dialog.Description>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
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
    </div>
  );
}
