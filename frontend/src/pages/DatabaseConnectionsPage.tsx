import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  Database,
  Plus,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle,
  RefreshCw,
  Star,
  Edit,
  TestTube,
} from 'lucide-react';

interface DatabaseConnection {
  id: number;
  name: string;
  display_name: string | null;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string | null;
  has_password: boolean;
  ssl_enabled: boolean;
  trust_certificate: boolean;
  additional_options: Record<string, unknown> | null;
  is_default: boolean;
  is_active: boolean;
  last_tested_at: string | null;
  last_test_success: boolean | null;
  created_at: string;
  updated_at: string;
}

interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
  error: string | null;
  server_version: string | null;
}

type DatabaseType = 'mssql' | 'postgresql' | 'mysql';

const DB_TYPE_INFO: Record<DatabaseType, { label: string; icon: string; defaultPort: number }> = {
  mssql: { label: 'SQL Server', icon: '🗄️', defaultPort: 1433 },
  postgresql: { label: 'PostgreSQL', icon: '🐘', defaultPort: 5432 },
  mysql: { label: 'MySQL', icon: '🐬', defaultPort: 3306 },
};

function ConnectionForm({
  connection,
  onSave,
  onCancel,
  isSaving,
}: {
  connection: Partial<DatabaseConnection> | null;
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const isEdit = !!connection?.id;

  const [formData, setFormData] = useState({
    name: connection?.name || '',
    display_name: connection?.display_name || '',
    db_type: (connection?.db_type as DatabaseType) || 'mssql',
    host: connection?.host || 'localhost',
    port: connection?.port || 1433,
    database: connection?.database || '',
    username: connection?.username || '',
    password: '',
    ssl_enabled: connection?.ssl_enabled ?? true,
    trust_certificate: connection?.trust_certificate ?? false,
    is_default: connection?.is_default ?? false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const handleDbTypeChange = (dbType: DatabaseType) => {
    setFormData({
      ...formData,
      db_type: dbType,
      port: DB_TYPE_INFO[dbType].defaultPort,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Connection Name</label>
          <Input
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="my-database"
            required
            disabled={isEdit}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Display Name</label>
          <Input
            value={formData.display_name}
            onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
            placeholder="My Production Database"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-2">Database Type</label>
        <div className="flex gap-2">
          {(Object.keys(DB_TYPE_INFO) as DatabaseType[]).map((dbType) => (
            <button
              key={dbType}
              type="button"
              onClick={() => handleDbTypeChange(dbType)}
              className={`flex-1 p-3 rounded-lg border-2 transition-colors ${
                formData.db_type === dbType
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <div className="text-2xl mb-1">{DB_TYPE_INFO[dbType].icon}</div>
              <div className="text-sm font-medium">{DB_TYPE_INFO[dbType].label}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <label className="block text-sm font-medium mb-1">Host</label>
          <Input
            value={formData.host}
            onChange={(e) => setFormData({ ...formData, host: e.target.value })}
            placeholder="localhost"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Port</label>
          <Input
            type="number"
            value={formData.port}
            onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) || 0 })}
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Database Name</label>
        <Input
          value={formData.database}
          onChange={(e) => setFormData({ ...formData, database: e.target.value })}
          placeholder="mydb"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Username</label>
          <Input
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            placeholder="sa"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">
            Password {isEdit && connection?.has_password && '(leave blank to keep)'}
          </label>
          <Input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            placeholder="••••••••"
          />
        </div>
      </div>

      <div className="flex gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.ssl_enabled}
            onChange={(e) => setFormData({ ...formData, ssl_enabled: e.target.checked })}
            className="rounded"
          />
          <span className="text-sm">SSL/Encryption</span>
        </label>
        {formData.db_type === 'mssql' && (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={formData.trust_certificate}
              onChange={(e) => setFormData({ ...formData, trust_certificate: e.target.checked })}
              className="rounded"
            />
            <span className="text-sm">Trust Server Certificate</span>
          </label>
        )}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.is_default}
            onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
            className="rounded"
          />
          <span className="text-sm">Set as Default</span>
        </label>
      </div>

      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving}>
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isEdit ? 'Update' : 'Create'} Connection
        </Button>
      </div>
    </form>
  );
}

function ConnectionCard({
  connection,
  onEdit,
  onDelete,
  onTest,
  onSetDefault,
}: {
  connection: DatabaseConnection;
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
  onSetDefault: () => void;
}) {
  const dbInfo = DB_TYPE_INFO[connection.db_type as DatabaseType] || {
    label: connection.db_type,
    icon: '🗄️',
  };

  return (
    <Card className={`${!connection.is_active ? 'opacity-60' : ''}`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{dbInfo.icon}</span>
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {connection.display_name || connection.name}
                {connection.is_default && (
                  <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                )}
              </CardTitle>
              <p className="text-sm text-muted-foreground">{dbInfo.label}</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {connection.last_test_success !== null && (
              <div
                className={`p-1 rounded ${
                  connection.last_test_success
                    ? 'text-green-500 bg-green-500/10'
                    : 'text-red-500 bg-red-500/10'
                }`}
              >
                {connection.last_test_success ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <XCircle className="h-4 w-4" />
                )}
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Host:</span>
            <span className="font-mono">
              {connection.host}:{connection.port}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Database:</span>
            <span className="font-mono">{connection.database}</span>
          </div>
          {connection.username && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">User:</span>
              <span className="font-mono">{connection.username}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-muted-foreground">SSL:</span>
            <span>{connection.ssl_enabled ? 'Enabled' : 'Disabled'}</span>
          </div>
        </div>

        <div className="flex gap-2 mt-4 pt-4 border-t">
          <Button variant="outline" size="sm" onClick={onTest}>
            <TestTube className="h-4 w-4 mr-1" />
            Test
          </Button>
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit className="h-4 w-4 mr-1" />
            Edit
          </Button>
          {!connection.is_default && (
            <Button variant="outline" size="sm" onClick={onSetDefault}>
              <Star className="h-4 w-4 mr-1" />
              Default
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={onDelete} className="ml-auto text-destructive">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export function DatabaseConnectionsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingConnection, setEditingConnection] = useState<DatabaseConnection | null>(null);
  const [testResult, setTestResult] = useState<{
    connectionId: number;
    result: ConnectionTestResult;
  } | null>(null);

  // Fetch connections
  const { data: connections, isLoading } = useQuery({
    queryKey: ['database-connections'],
    queryFn: () => api.get<DatabaseConnection[]>('/database-connections'),
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      api.post<DatabaseConnection>('/database-connections', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database-connections'] });
      setShowForm(false);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) =>
      api.put<DatabaseConnection>(`/database-connections/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database-connections'] });
      setEditingConnection(null);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/database-connections/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database-connections'] });
    },
  });

  // Test mutation
  const testMutation = useMutation({
    mutationFn: (id: number) =>
      api.post<ConnectionTestResult>(`/database-connections/${id}/test`),
    onSuccess: (result, id) => {
      setTestResult({ connectionId: id, result });
      queryClient.invalidateQueries({ queryKey: ['database-connections'] });
    },
  });

  // Set default mutation
  const setDefaultMutation = useMutation({
    mutationFn: (id: number) => api.post(`/database-connections/${id}/set-default`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['database-connections'] });
    },
  });

  const handleSave = (data: Record<string, unknown>) => {
    if (editingConnection) {
      updateMutation.mutate({ id: editingConnection.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (id: number) => {
    if (confirm('Are you sure you want to delete this connection?')) {
      deleteMutation.mutate(id);
    }
  };

  // Group connections by type
  const connectionsByType = (connections || []).reduce(
    (acc, conn) => {
      const type = conn.db_type as DatabaseType;
      if (!acc[type]) acc[type] = [];
      acc[type].push(conn);
      return acc;
    },
    {} as Record<DatabaseType, DatabaseConnection[]>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6" />
            Database Connections
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage connections to SQL Server, PostgreSQL, and MySQL databases
          </p>
        </div>
        <Button onClick={() => setShowForm(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Connection
        </Button>
      </div>

      {/* Connection Form Modal */}
      {(showForm || editingConnection) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-[600px] max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>
                {editingConnection ? 'Edit Connection' : 'New Database Connection'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ConnectionForm
                connection={editingConnection}
                onSave={handleSave}
                onCancel={() => {
                  setShowForm(false);
                  setEditingConnection(null);
                }}
                isSaving={createMutation.isPending || updateMutation.isPending}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Test Result Modal */}
      {testResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-[400px]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {testResult.result.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                Connection Test
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className={testResult.result.success ? 'text-green-600' : 'text-red-600'}>
                {testResult.result.message}
              </p>
              {testResult.result.latency_ms && (
                <p className="text-sm text-muted-foreground">
                  Latency: {testResult.result.latency_ms}ms
                </p>
              )}
              {testResult.result.server_version && (
                <p className="text-sm text-muted-foreground">
                  Version: {testResult.result.server_version}
                </p>
              )}
              {testResult.result.error && (
                <p className="text-sm text-red-500 font-mono bg-red-500/10 p-2 rounded">
                  {testResult.result.error}
                </p>
              )}
              <Button onClick={() => setTestResult(null)} className="w-full">
                Close
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!connections || connections.length === 0) && (
        <Card>
          <CardContent className="py-12 text-center">
            <Database className="h-12 w-12 mx-auto text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No Database Connections</h3>
            <p className="text-muted-foreground mt-2">
              Add your first database connection to get started
            </p>
            <Button className="mt-4" onClick={() => setShowForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Connection
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Connection Cards by Type */}
      {!isLoading &&
        Object.entries(connectionsByType).map(([type, conns]) => (
          <div key={type}>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <span>{DB_TYPE_INFO[type as DatabaseType]?.icon || '🗄️'}</span>
              {DB_TYPE_INFO[type as DatabaseType]?.label || type}
              <span className="text-sm font-normal text-muted-foreground">
                ({conns.length})
              </span>
            </h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {conns.map((conn) => (
                <ConnectionCard
                  key={conn.id}
                  connection={conn}
                  onEdit={() => setEditingConnection(conn)}
                  onDelete={() => handleDelete(conn.id)}
                  onTest={() => testMutation.mutate(conn.id)}
                  onSetDefault={() => setDefaultMutation.mutate(conn.id)}
                />
              ))}
            </div>
          </div>
        ))}

      {/* Refresh Button */}
      {connections && connections.length > 0 && (
        <div className="flex justify-center pt-4">
          <Button
            variant="outline"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['database-connections'] })}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      )}
    </div>
  );
}
