import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Database,
  CheckCircle,
  XCircle,
  RefreshCw,
  Plus,
  Trash2,
  Edit,
  Power,
  PowerOff,
  Loader2,
  Terminal,
  Globe,
  X,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface MCPServer {
  id: string;
  name: string;
  description: string | null;
  type: 'stdio' | 'http';
  command: string | null;
  args: string[];
  url: string | null;
  enabled: boolean;
  built_in: boolean;
  status: 'connected' | 'disconnected' | 'error';
  tools: string[];
}

interface MCPServersResponse {
  servers: MCPServer[];
  total: number;
}

interface MCPServerCreate {
  id: string;
  name: string;
  description: string;
  type: 'stdio' | 'http';
  command: string | null;
  args: string[];
  url: string | null;
  env: Record<string, string>;
  enabled: boolean;
}

// Add/Edit Server Dialog
function ServerDialog({
  server,
  onClose,
  onSave,
  isSaving,
}: {
  server?: MCPServer;
  onClose: () => void;
  onSave: (data: MCPServerCreate) => void;
  isSaving: boolean;
}) {
  const isEdit = !!server;
  const [formData, setFormData] = useState<MCPServerCreate>({
    id: server?.id || '',
    name: server?.name || '',
    description: server?.description || '',
    type: server?.type || 'stdio',
    command: server?.command || '',
    args: server?.args || [],
    url: server?.url || '',
    env: {},
    enabled: server?.enabled ?? true,
  });
  const [argsText, setArgsText] = useState(server?.args?.join('\n') || '');
  const [envText, setEnvText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.id.trim()) {
      newErrors.id = 'ID is required';
    } else if (!/^[a-z0-9_-]+$/i.test(formData.id)) {
      newErrors.id = 'ID must be alphanumeric with dashes/underscores';
    }

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (formData.type === 'stdio' && !formData.command?.trim()) {
      newErrors.command = 'Command is required for stdio servers';
    }

    if (formData.type === 'http' && !formData.url?.trim()) {
      newErrors.url = 'URL is required for HTTP servers';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    // Parse args from text
    const args = argsText
      .split('\n')
      .map((arg) => arg.trim())
      .filter((arg) => arg.length > 0);

    // Parse env from text (KEY=VALUE format)
    const env: Record<string, string> = {};
    envText.split('\n').forEach((line) => {
      const idx = line.indexOf('=');
      if (idx > 0) {
        const key = line.substring(0, idx).trim();
        const value = line.substring(idx + 1).trim();
        if (key) env[key] = value;
      }
    });

    onSave({
      ...formData,
      args,
      env,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{isEdit ? 'Edit MCP Server' : 'Add MCP Server'}</CardTitle>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Server Type */}
          <div>
            <label className="mb-1 block text-sm font-medium">Server Type</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setFormData({ ...formData, type: 'stdio' })}
                className={`flex items-center gap-2 rounded-lg border px-4 py-2 ${
                  formData.type === 'stdio'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:bg-muted'
                }`}
              >
                <Terminal className="h-4 w-4" />
                Stdio
              </button>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, type: 'http' })}
                className={`flex items-center gap-2 rounded-lg border px-4 py-2 ${
                  formData.type === 'http'
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:bg-muted'
                }`}
              >
                <Globe className="h-4 w-4" />
                HTTP
              </button>
            </div>
          </div>

          {/* ID */}
          <div>
            <label className="mb-1 block text-sm font-medium">
              Server ID <span className="text-destructive">*</span>
            </label>
            <Input
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value })}
              placeholder="my-server"
              disabled={isEdit}
              className={errors.id ? 'border-destructive' : ''}
            />
            {errors.id && <p className="mt-1 text-xs text-destructive">{errors.id}</p>}
          </div>

          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium">
              Display Name <span className="text-destructive">*</span>
            </label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="My Server"
              className={errors.name ? 'border-destructive' : ''}
            />
            {errors.name && <p className="mt-1 text-xs text-destructive">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="mb-1 block text-sm font-medium">Description</label>
            <Input
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Optional description"
            />
          </div>

          {/* Stdio-specific fields */}
          {formData.type === 'stdio' && (
            <>
              <div>
                <label className="mb-1 block text-sm font-medium">
                  Command <span className="text-destructive">*</span>
                </label>
                <Input
                  value={formData.command || ''}
                  onChange={(e) => setFormData({ ...formData, command: e.target.value })}
                  placeholder="node"
                  className={errors.command ? 'border-destructive' : ''}
                />
                {errors.command && <p className="mt-1 text-xs text-destructive">{errors.command}</p>}
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium">Arguments (one per line)</label>
                <textarea
                  value={argsText}
                  onChange={(e) => setArgsText(e.target.value)}
                  placeholder="/path/to/script.js&#10;--option=value"
                  className="h-24 w-full rounded-lg border bg-background p-2 text-sm font-mono"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium">
                  Environment Variables (KEY=VALUE, one per line)
                </label>
                <textarea
                  value={envText}
                  onChange={(e) => setEnvText(e.target.value)}
                  placeholder="SERVER_NAME=localhost&#10;DATABASE_NAME=mydb"
                  className="h-24 w-full rounded-lg border bg-background p-2 text-sm font-mono"
                />
              </div>
            </>
          )}

          {/* HTTP-specific fields */}
          {formData.type === 'http' && (
            <div>
              <label className="mb-1 block text-sm font-medium">
                Server URL <span className="text-destructive">*</span>
              </label>
              <Input
                value={formData.url || ''}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="http://localhost:3000"
                className={errors.url ? 'border-destructive' : ''}
              />
              {errors.url && <p className="mt-1 text-xs text-destructive">{errors.url}</p>}
            </div>
          )}

          {/* Enabled toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable on creation</label>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, enabled: !formData.enabled })}
              className={`relative h-6 w-11 rounded-full transition-colors ${
                formData.enabled ? 'bg-primary' : 'bg-muted'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition-transform ${
                  formData.enabled ? 'translate-x-5' : ''
                }`}
              />
            </button>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={onClose} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSaving}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? 'Save Changes' : 'Add Server'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Delete confirmation dialog
function DeleteDialog({
  server,
  onConfirm,
  onCancel,
  isDeleting,
}: {
  server: MCPServer;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-96">
        <CardHeader>
          <CardTitle className="text-destructive">Delete MCP Server</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>
            Are you sure you want to delete "<strong>{server.name}</strong>"?
          </p>
          <p className="text-sm text-muted-foreground">
            This will remove the server configuration. Any tools provided by this server will no
            longer be available.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onCancel} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={onConfirm} disabled={isDeleting}>
              {isDeleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Server card component
function ServerCard({
  server,
  onEdit,
  onDelete,
  onToggleEnabled,
  isToggling,
}: {
  server: MCPServer;
  onEdit: () => void;
  onDelete: () => void;
  onToggleEnabled: () => void;
  isToggling: boolean;
}) {
  const [showTools, setShowTools] = useState(false);

  const statusColors = {
    connected: 'text-green-500',
    disconnected: 'text-yellow-500',
    error: 'text-red-500',
  };

  const StatusIcon = server.enabled ? (
    <CheckCircle className={`h-5 w-5 ${statusColors[server.status]}`} />
  ) : (
    <XCircle className="h-5 w-5 text-muted-foreground" />
  );

  return (
    <Card className={!server.enabled ? 'opacity-60' : ''}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            {server.type === 'stdio' ? (
              <Terminal className="h-5 w-5" />
            ) : (
              <Globe className="h-5 w-5" />
            )}
            {server.name}
            {server.built_in && (
              <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                Built-in
              </span>
            )}
          </span>
          {StatusIcon}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {server.description && (
          <p className="text-sm text-muted-foreground">{server.description}</p>
        )}

        {/* Connection info */}
        <div className="text-xs text-muted-foreground font-mono">
          {server.type === 'stdio' ? (
            <p>
              {server.command} {server.args.slice(0, 2).join(' ')}
              {server.args.length > 2 && '...'}
            </p>
          ) : (
            <p>{server.url}</p>
          )}
        </div>

        {/* Tools */}
        {server.tools.length > 0 && (
          <div>
            <button
              onClick={() => setShowTools(!showTools)}
              className="flex items-center gap-1 text-xs font-medium uppercase text-muted-foreground hover:text-foreground"
            >
              Available Tools ({server.tools.length})
              {showTools ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </button>
            {showTools && (
              <div className="mt-2 flex flex-wrap gap-1">
                {server.tools.map((tool) => (
                  <span key={tool} className="rounded-md bg-muted px-2 py-1 text-xs">
                    {tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleEnabled}
              disabled={isToggling}
              title={server.enabled ? 'Disable server' : 'Enable server'}
            >
              {isToggling ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : server.enabled ? (
                <PowerOff className="h-4 w-4" />
              ) : (
                <Power className="h-4 w-4" />
              )}
            </Button>
            <span className="text-xs text-muted-foreground">
              {server.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>

          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={onEdit} title="Edit server">
              <Edit className="h-4 w-4" />
            </Button>
            {!server.built_in && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDelete}
                title="Delete server"
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function MCPServersPage() {
  const queryClient = useQueryClient();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editServer, setEditServer] = useState<MCPServer | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MCPServer | null>(null);
  const [togglingServer, setTogglingServer] = useState<string | null>(null);

  // Fetch servers
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => api.get<MCPServersResponse>('/mcp-servers'),
  });

  // Create server mutation
  const createMutation = useMutation({
    mutationFn: (serverData: MCPServerCreate) =>
      api.post<MCPServer>('/mcp-servers', serverData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setShowAddDialog(false);
    },
  });

  // Update server mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MCPServerCreate> }) =>
      api.patch<MCPServer>(`/mcp-servers/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setEditServer(null);
    },
  });

  // Delete server mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/mcp-servers/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setDeleteTarget(null);
    },
  });

  // Toggle enabled mutation
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      api.post(`/mcp-servers/${id}/${enabled ? 'enable' : 'disable'}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] });
      setTogglingServer(null);
    },
    onError: () => {
      setTogglingServer(null);
    },
  });

  const handleToggleEnabled = (server: MCPServer) => {
    setTogglingServer(server.id);
    toggleMutation.mutate({ id: server.id, enabled: !server.enabled });
  };

  const handleSaveServer = (data: MCPServerCreate) => {
    if (editServer) {
      // Update existing server
      updateMutation.mutate({
        id: editServer.id,
        data: {
          name: data.name,
          description: data.description,
          command: data.command,
          args: data.args,
          url: data.url,
          env: data.env,
          enabled: data.enabled,
        },
      });
    } else {
      // Create new server
      createMutation.mutate(data);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">MCP Servers</h1>
          <p className="text-muted-foreground">
            Configure Model Context Protocol servers to extend agent capabilities.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()} disabled={isRefetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowAddDialog(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Server
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : data?.servers.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No MCP servers configured</h3>
            <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
              MCP servers provide tools that extend the agent's capabilities. Add a server to
              enable features like database access, file operations, or custom integrations.
            </p>
            <Button className="mt-4" onClick={() => setShowAddDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Server
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Status summary */}
          <div className="flex gap-4 text-sm">
            <span className="flex items-center gap-1">
              <CheckCircle className="h-4 w-4 text-green-500" />
              {data?.servers.filter((s) => s.enabled).length || 0} enabled
            </span>
            <span className="flex items-center gap-1">
              <XCircle className="h-4 w-4 text-muted-foreground" />
              {data?.servers.filter((s) => !s.enabled).length || 0} disabled
            </span>
          </div>

          {/* Server grid */}
          <div className="grid gap-4 md:grid-cols-2">
            {data?.servers.map((server) => (
              <ServerCard
                key={server.id}
                server={server}
                onEdit={() => setEditServer(server)}
                onDelete={() => setDeleteTarget(server)}
                onToggleEnabled={() => handleToggleEnabled(server)}
                isToggling={togglingServer === server.id}
              />
            ))}
          </div>
        </>
      )}

      {/* Add server dialog */}
      {showAddDialog && (
        <ServerDialog
          onClose={() => setShowAddDialog(false)}
          onSave={handleSaveServer}
          isSaving={createMutation.isPending}
        />
      )}

      {/* Edit server dialog */}
      {editServer && (
        <ServerDialog
          server={editServer}
          onClose={() => setEditServer(null)}
          onSave={handleSaveServer}
          isSaving={updateMutation.isPending}
        />
      )}

      {/* Delete confirmation dialog */}
      {deleteTarget && (
        <DeleteDialog
          server={deleteTarget}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
          isDeleting={deleteMutation.isPending}
        />
      )}

      {/* Error notifications */}
      {(createMutation.error || updateMutation.error || deleteMutation.error) && (
        <div className="fixed bottom-4 right-4 rounded-lg border bg-destructive/10 p-4 text-destructive">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            <span>
              {(createMutation.error as Error)?.message ||
                (updateMutation.error as Error)?.message ||
                (deleteMutation.error as Error)?.message ||
                'An error occurred'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
