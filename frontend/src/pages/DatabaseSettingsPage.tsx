import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  Database,
  Save,
  TestTube,
  Loader2,
  Check,
  X,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import type { DatabaseSettings, DatabaseSettingsResponse, ConnectionTestResult } from '@/types';

export function DatabaseSettingsPage() {
  const queryClient = useQueryClient();

  // Form state
  const [host, setHost] = useState('localhost');
  const [port, setPort] = useState(1434);
  const [database, setDatabase] = useState('LLM_BackEnd');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [trustCertificate, setTrustCertificate] = useState(true);
  const [showPassword, setShowPassword] = useState(false);

  // UI state
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [testMessage, setTestMessage] = useState<{ type: 'success' | 'error'; message: string; latency?: number } | null>(null);

  // Fetch current settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['database-settings'],
    queryFn: () => api.getDatabaseSettings<DatabaseSettingsResponse>(),
  });

  // Update form when settings are loaded
  useEffect(() => {
    if (settings) {
      setHost(settings.host);
      setPort(settings.port);
      setDatabase(settings.database);
      setUsername(settings.username);
      setTrustCertificate(settings.trust_certificate);
      // Don't set password - it's not returned for security
    }
  }, [settings]);

  // Test connection mutation
  const testMutation = useMutation({
    mutationFn: (data: DatabaseSettings) =>
      api.testDatabaseConnection<ConnectionTestResult>(data),
    onSuccess: (result) => {
      if (result.success) {
        setTestMessage({
          type: 'success',
          message: result.message,
          latency: result.latency_ms || undefined,
        });
      } else {
        setTestMessage({
          type: 'error',
          message: result.message,
        });
      }
    },
    onError: (error: { detail: string }) => {
      setTestMessage({
        type: 'error',
        message: error.detail || 'Failed to test connection',
      });
    },
  });

  // Save settings mutation
  const saveMutation = useMutation({
    mutationFn: (data: DatabaseSettings) =>
      api.updateDatabaseSettings<void>(data),
    onSuccess: () => {
      setSaveMessage({
        type: 'success',
        message: 'Database settings saved successfully',
      });
      queryClient.invalidateQueries({ queryKey: ['database-settings'] });
      queryClient.invalidateQueries({ queryKey: ['health'] });
      // Clear save message after 5 seconds
      setTimeout(() => setSaveMessage(null), 5000);
    },
    onError: (error: { detail: string }) => {
      setSaveMessage({
        type: 'error',
        message: error.detail || 'Failed to save settings',
      });
      // Clear error message after 8 seconds
      setTimeout(() => setSaveMessage(null), 8000);
    },
  });

  const handleTestConnection = () => {
    setTestMessage(null);
    testMutation.mutate({
      host,
      port,
      database,
      username,
      password,
      trust_certificate: trustCertificate,
    });
  };

  const handleSave = () => {
    setSaveMessage(null);
    setTestMessage(null);
    saveMutation.mutate({
      host,
      port,
      database,
      username,
      password,
      trust_certificate: trustCertificate,
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading database settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Backend Database Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure connection to SQL Server 2025 backend database (LLM_BackEnd)
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            SQL Server 2025 Connection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Host */}
          <div>
            <label className="mb-1 block text-sm font-medium">Host</label>
            <Input
              type="text"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="localhost"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Database server hostname or IP address
            </p>
          </div>

          {/* Port */}
          <div>
            <label className="mb-1 block text-sm font-medium">Port</label>
            <Input
              type="number"
              value={port}
              onChange={(e) => setPort(parseInt(e.target.value) || 1434)}
              placeholder="1434"
              min={1}
              max={65535}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              SQL Server port (default: 1434 for backend database)
            </p>
          </div>

          {/* Database Name */}
          <div>
            <label className="mb-1 block text-sm font-medium">Database Name</label>
            <Input
              type="text"
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
              placeholder="LLM_BackEnd"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Name of the backend database
            </p>
          </div>

          {/* Username */}
          <div>
            <label className="mb-1 block text-sm font-medium">Username</label>
            <Input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="sa"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              SQL Server authentication username
            </p>
          </div>

          {/* Password */}
          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <div className="relative">
              <Input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={settings?.password_set ? '••••••••' : 'Enter password'}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              {settings?.password_set
                ? 'Leave blank to keep existing password'
                : 'SQL Server authentication password'}
            </p>
          </div>

          {/* Trust Server Certificate */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="trust-cert"
              checked={trustCertificate}
              onChange={(e) => setTrustCertificate(e.target.checked)}
              className="h-4 w-4 rounded border-input"
            />
            <label htmlFor="trust-cert" className="text-sm font-medium">
              Trust Server Certificate
            </label>
          </div>
          <p className="text-xs text-muted-foreground">
            Enable for self-signed certificates (required for local development)
          </p>

          {/* Test Connection Button */}
          <div className="pt-2">
            <Button
              onClick={handleTestConnection}
              disabled={testMutation.isPending || !username || !password}
              variant="outline"
              className="w-full"
            >
              {testMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing Connection...
                </>
              ) : (
                <>
                  <TestTube className="mr-2 h-4 w-4" />
                  Test Connection
                </>
              )}
            </Button>
          </div>

          {/* Test Result Message */}
          {testMessage && (
            <div
              className={`rounded-lg p-3 ${
                testMessage.type === 'success'
                  ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                  : 'bg-red-500/10 text-red-700 dark:text-red-400'
              }`}
            >
              <div className="flex items-center gap-2">
                {testMessage.type === 'success' ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <span className="font-medium">{testMessage.message}</span>
              </div>
              {testMessage.latency && (
                <p className="mt-1 text-sm">Response time: {testMessage.latency}ms</p>
              )}
            </div>
          )}

          {/* Save Button */}
          <div className="pt-2">
            <Button
              onClick={handleSave}
              disabled={saveMutation.isPending || !username || !password}
              className="w-full"
            >
              {saveMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Settings
                </>
              )}
            </Button>
          </div>

          {/* Save Result Message */}
          {saveMessage && (
            <div
              className={`rounded-lg p-3 ${
                saveMessage.type === 'success'
                  ? 'bg-green-500/10 text-green-700 dark:text-green-400'
                  : 'bg-red-500/10 text-red-700 dark:text-red-400'
              }`}
            >
              <div className="flex items-center gap-2">
                {saveMessage.type === 'success' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <X className="h-4 w-4" />
                )}
                <span className="font-medium">{saveMessage.message}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Connection Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Current Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Host:</span>
              <span className="font-mono">{settings?.host || 'Not configured'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Port:</span>
              <span className="font-mono">{settings?.port || 'Not configured'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Database:</span>
              <span className="font-mono">{settings?.database || 'Not configured'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Username:</span>
              <span className="font-mono">{settings?.username || 'Not configured'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Password:</span>
              <span className="flex items-center gap-1">
                {settings?.password_set ? (
                  <>
                    <Check className="h-3 w-3 text-green-500" />
                    <span className="text-green-600 dark:text-green-400">Configured</span>
                  </>
                ) : (
                  <>
                    <X className="h-3 w-3 text-red-500" />
                    <span className="text-red-600 dark:text-red-400">Not configured</span>
                  </>
                )}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Information Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Important Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            • This configures the connection to the SQL Server 2025 backend database (LLM_BackEnd)
          </p>
          <p>
            • The backend database stores conversation history, document metadata, and native vector embeddings
          </p>
          <p>
            • Default port 1434 is for the backend database (sample database uses port 1433)
          </p>
          <p>
            • Test the connection before saving to ensure credentials are correct
          </p>
          <p>
            • Changes take effect immediately after saving
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
