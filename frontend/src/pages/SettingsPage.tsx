import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { ThemeSelector } from '@/components/settings/ThemeSelector';
import { Save, RefreshCw } from 'lucide-react';
import type { HealthStatus } from '@/types';

interface Settings {
  ollama_host: string;
  ollama_model: string;
  embedding_model: string;
  sql_server_host: string;
  sql_database_name: string;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    ollama_host: 'http://localhost:11434',
    ollama_model: 'qwen3:30b',
    embedding_model: 'nomic-embed-text',
    sql_server_host: 'localhost',
    sql_database_name: 'ResearchAnalytics',
  });

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
  });

  const statusColors = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-yellow-500',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Theme Settings */}
      <ThemeSelector />

      {/* Health Status */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>System Health</CardTitle>
          <Button variant="ghost" size="icon" onClick={() => refetchHealth()}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {health?.services.map((service) => (
              <div key={service.name} className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${statusColors[service.status]}`} />
                <div>
                  <p className="font-medium capitalize">{service.name.replace('_', ' ')}</p>
                  {service.latency_ms && (
                    <p className="text-sm text-muted-foreground">{service.latency_ms}ms</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Ollama Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Ollama Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host URL</label>
            <Input
              value={settings.ollama_host}
              onChange={(e) => setSettings({ ...settings, ollama_host: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Model</label>
            <Input
              value={settings.ollama_model}
              onChange={(e) => setSettings({ ...settings, ollama_model: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Embedding Model</label>
            <Input
              value={settings.embedding_model}
              onChange={(e) => setSettings({ ...settings, embedding_model: e.target.value })}
            />
          </div>
        </CardContent>
      </Card>

      {/* SQL Server Settings */}
      <Card>
        <CardHeader>
          <CardTitle>SQL Server Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host</label>
            <Input
              value={settings.sql_server_host}
              onChange={(e) => setSettings({ ...settings, sql_server_host: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Database Name</label>
            <Input
              value={settings.sql_database_name}
              onChange={(e) => setSettings({ ...settings, sql_database_name: e.target.value })}
            />
          </div>
        </CardContent>
      </Card>

      <Button>
        <Save className="mr-2 h-4 w-4" />
        Save Settings
      </Button>
    </div>
  );
}
