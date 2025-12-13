import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useTheme } from '@/contexts/ThemeContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  Save,
  RefreshCw,
  Check,
  X,
  Loader2,
  Sun,
  Moon,
  Monitor,
  Zap,
  Database,
  Settings2,
  ChevronDown,
  AlertCircle,
} from 'lucide-react';
import type { HealthStatus } from '@/types';

interface ProviderInfo {
  id: string;
  name: string;
  display_name: string;
  icon: string;
  available: boolean;
  error: string | null;
  version: string | null;
}

interface ModelInfo {
  name: string;
  size: string | null;
  modified_at: string | null;
  family: string | null;
  parameter_size: string | null;
  quantization_level: string | null;
}

interface ProviderModelsResponse {
  provider: string;
  models: ModelInfo[];
  error: string | null;
}

interface ConnectionTestResult {
  success: boolean;
  provider: string;
  model: string | null;
  message: string;
  latency_ms: number | null;
  version: string | null;
  error: string | null;
}

interface ProviderConfig {
  provider: string;
  model: string;
  embeddingModel: string;
  host: string;
}

// Theme selector component
function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  const themes = [
    { id: 'light', label: 'Light', icon: Sun },
    { id: 'dark', label: 'Dark', icon: Moon },
    { id: 'system', label: 'System', icon: Monitor },
  ] as const;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          Theme
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          {themes.map((t) => {
            const Icon = t.icon;
            const isActive = theme === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTheme(t.id)}
                className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-colors ${
                  isActive
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border hover:border-primary/50 hover:bg-muted'
                }`}
              >
                <Icon className="h-6 w-6" />
                <span className="text-sm font-medium">{t.label}</span>
                {isActive && <Check className="h-4 w-4" />}
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-sm text-muted-foreground">
          Theme preference is saved and persists across sessions.
        </p>
      </CardContent>
    </Card>
  );
}

// Provider selector with icons
function ProviderSelector({
  providers,
  selectedProvider,
  onSelect,
  isLoading,
}: {
  providers: ProviderInfo[];
  selectedProvider: string;
  onSelect: (provider: string) => void;
  isLoading: boolean;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selected = providers.find((p) => p.id === selectedProvider);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className="flex w-full items-center justify-between rounded-lg border bg-background px-4 py-3 text-left hover:bg-muted disabled:opacity-50"
      >
        <div className="flex items-center gap-3">
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <span className="text-xl">{selected?.icon || '🤖'}</span>
          )}
          <div>
            <p className="font-medium">{selected?.display_name || 'Select Provider'}</p>
            {selected && (
              <p className="text-sm text-muted-foreground">
                {selected.available ? (
                  <span className="flex items-center gap-1 text-green-500">
                    <Check className="h-3 w-3" /> Available
                    {selected.version && ` (v${selected.version})`}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-500">
                    <X className="h-3 w-3" /> Unavailable
                  </span>
                )}
              </p>
            )}
          </div>
        </div>
        <ChevronDown className={`h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-lg border bg-popover shadow-lg">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => {
                onSelect(provider.id);
                setIsOpen(false);
              }}
              className={`flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-muted ${
                provider.id === selectedProvider ? 'bg-muted' : ''
              }`}
            >
              <span className="text-xl">{provider.icon}</span>
              <div className="flex-1">
                <p className="font-medium">{provider.display_name}</p>
                <p className="text-sm text-muted-foreground">
                  {provider.available ? (
                    <span className="text-green-500">
                      Available{provider.version && ` (v${provider.version})`}
                    </span>
                  ) : (
                    <span className="text-red-500">
                      {provider.error ? provider.error.slice(0, 50) : 'Unavailable'}
                    </span>
                  )}
                </p>
              </div>
              {provider.id === selectedProvider && <Check className="h-4 w-4 text-primary" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Model selector dropdown
function ModelSelector({
  models,
  selectedModel,
  onSelect,
  isLoading,
  error,
  onRefresh,
}: {
  models: ModelInfo[];
  selectedModel: string;
  onSelect: (model: string) => void;
  isLoading: boolean;
  error: string | null;
  onRefresh: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selected = models.find((m) => m.name === selectedModel);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">Model</label>
        <Button variant="ghost" size="sm" onClick={onRefresh} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>
      <div className="relative">
        <button
          onClick={() => !error && setIsOpen(!isOpen)}
          disabled={isLoading || !!error}
          className="flex w-full items-center justify-between rounded-lg border bg-background px-4 py-3 text-left hover:bg-muted disabled:opacity-50"
        >
          <div>
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading models...
              </span>
            ) : error ? (
              <span className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error.slice(0, 50)}
              </span>
            ) : selected ? (
              <div>
                <p className="font-medium">{selected.name}</p>
                {selected.size && (
                  <p className="text-sm text-muted-foreground">{selected.size}</p>
                )}
              </div>
            ) : (
              <span className="text-muted-foreground">Select a model</span>
            )}
          </div>
          <ChevronDown className={`h-5 w-5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && models.length > 0 && (
          <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-lg border bg-popover shadow-lg">
            {models.map((model) => (
              <button
                key={model.name}
                onClick={() => {
                  onSelect(model.name);
                  setIsOpen(false);
                }}
                className={`flex w-full items-center justify-between px-4 py-2 text-left hover:bg-muted ${
                  model.name === selectedModel ? 'bg-muted' : ''
                }`}
              >
                <div>
                  <p className="font-medium">{model.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {[model.size, model.family, model.parameter_size]
                      .filter(Boolean)
                      .join(' • ')}
                  </p>
                </div>
                {model.name === selectedModel && <Check className="h-4 w-4 text-primary" />}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Connection test button
function ConnectionTestButton({
  provider,
  model,
}: {
  provider: string;
  model: string | null;
}) {
  const testMutation = useMutation({
    mutationFn: (data: { provider: string; model: string | null }) =>
      api.post<ConnectionTestResult>('/settings/providers/test', data),
  });

  const handleTest = () => {
    testMutation.mutate({ provider, model });
  };

  return (
    <div className="space-y-2">
      <Button
        onClick={handleTest}
        disabled={testMutation.isPending}
        variant={testMutation.data?.success ? 'default' : 'outline'}
        className="w-full"
      >
        {testMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Testing...
          </>
        ) : (
          <>
            <Zap className="mr-2 h-4 w-4" />
            Test Connection
          </>
        )}
      </Button>

      {testMutation.data && (
        <div
          className={`rounded-lg p-3 ${
            testMutation.data.success
              ? 'bg-green-500/10 text-green-700 dark:text-green-400'
              : 'bg-red-500/10 text-red-700 dark:text-red-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {testMutation.data.success ? (
              <Check className="h-4 w-4" />
            ) : (
              <X className="h-4 w-4" />
            )}
            <span className="font-medium">{testMutation.data.message}</span>
          </div>
          {testMutation.data.latency_ms && (
            <p className="mt-1 text-sm">Response time: {testMutation.data.latency_ms}ms</p>
          )}
          {testMutation.data.error && (
            <p className="mt-1 text-sm">{testMutation.data.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

export function SettingsPage() {
  // Theme is handled by ThemeContext

  // Provider configuration state
  const [providerConfig, setProviderConfig] = useState<ProviderConfig>({
    provider: 'ollama',
    model: 'qwen3:30b',
    embeddingModel: 'nomic-embed-text',
    host: 'http://localhost:11434',
  });

  // Secondary provider config (for dual provider support)
  const [secondaryConfig, setSecondaryConfig] = useState<ProviderConfig>({
    provider: 'foundry_local',
    model: '',
    embeddingModel: '',
    host: 'http://localhost:5272',
  });

  // SQL Server settings
  const [sqlSettings, setSqlSettings] = useState({
    host: 'localhost',
    database: 'ResearchAnalytics',
  });

  // Fetch providers list
  const { data: providers = [], isLoading: providersLoading } = useQuery({
    queryKey: ['providers'],
    queryFn: () => api.get<ProviderInfo[]>('/settings/providers'),
    staleTime: 30000, // 30 seconds
  });

  // Fetch models for selected provider
  const { data: modelsData, isLoading: modelsLoading, refetch: refetchModels } = useQuery({
    queryKey: ['models', providerConfig.provider],
    queryFn: () =>
      api.get<ProviderModelsResponse>(`/settings/providers/${providerConfig.provider}/models`),
    enabled: !!providerConfig.provider,
  });

  // Fetch models for secondary provider
  const { data: secondaryModelsData, refetch: refetchSecondaryModels } = useQuery({
    queryKey: ['models', secondaryConfig.provider],
    queryFn: () =>
      api.get<ProviderModelsResponse>(`/settings/providers/${secondaryConfig.provider}/models`),
    enabled: !!secondaryConfig.provider && secondaryConfig.provider !== providerConfig.provider,
  });

  // Health status
  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<HealthStatus>('/health'),
  });

  const statusColors = {
    healthy: 'bg-green-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-yellow-500',
  };

  // Load saved settings from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('llm-settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.primary) setProviderConfig(parsed.primary);
        if (parsed.secondary) setSecondaryConfig(parsed.secondary);
        if (parsed.sql) setSqlSettings(parsed.sql);
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  // Save settings to localStorage
  const handleSave = () => {
    localStorage.setItem(
      'llm-settings',
      JSON.stringify({
        primary: providerConfig,
        secondary: secondaryConfig,
        sql: sqlSettings,
      })
    );
    // Show success notification
    alert('Settings saved successfully!');
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Theme Settings */}
      <ThemeSelector />

      {/* System Health */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            System Health
          </CardTitle>
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
                  {service.message && (
                    <p className="text-sm text-muted-foreground truncate max-w-[200px]">
                      {service.message}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Primary LLM Provider Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-xl">🦙</span>
            Primary LLM Provider
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ProviderSelector
            providers={providers}
            selectedProvider={providerConfig.provider}
            onSelect={(provider) => {
              setProviderConfig((prev) => ({ ...prev, provider, model: '' }));
            }}
            isLoading={providersLoading}
          />

          <ModelSelector
            models={modelsData?.models || []}
            selectedModel={providerConfig.model}
            onSelect={(model) => setProviderConfig((prev) => ({ ...prev, model }))}
            isLoading={modelsLoading}
            error={modelsData?.error || null}
            onRefresh={() => refetchModels()}
          />

          <div>
            <label className="mb-1 block text-sm font-medium">Host URL</label>
            <Input
              value={providerConfig.host}
              onChange={(e) => setProviderConfig((prev) => ({ ...prev, host: e.target.value }))}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Embedding Model</label>
            <Input
              value={providerConfig.embeddingModel}
              onChange={(e) =>
                setProviderConfig((prev) => ({ ...prev, embeddingModel: e.target.value }))
              }
              placeholder="nomic-embed-text"
            />
          </div>

          <ConnectionTestButton
            provider={providerConfig.provider}
            model={providerConfig.model || null}
          />
        </CardContent>
      </Card>

      {/* Secondary LLM Provider Configuration (Dual Provider Support) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-xl">🔧</span>
            Secondary LLM Provider (Optional)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Configure a secondary provider to switch between providers without re-entering
            configuration.
          </p>

          <ProviderSelector
            providers={providers.filter((p) => p.id !== providerConfig.provider)}
            selectedProvider={secondaryConfig.provider}
            onSelect={(provider) => {
              setSecondaryConfig((prev) => ({ ...prev, provider, model: '' }));
            }}
            isLoading={providersLoading}
          />

          {secondaryConfig.provider && (
            <>
              <ModelSelector
                models={secondaryModelsData?.models || []}
                selectedModel={secondaryConfig.model}
                onSelect={(model) => setSecondaryConfig((prev) => ({ ...prev, model }))}
                isLoading={false}
                error={secondaryModelsData?.error || null}
                onRefresh={() => refetchSecondaryModels()}
              />

              <div>
                <label className="mb-1 block text-sm font-medium">Host URL</label>
                <Input
                  value={secondaryConfig.host}
                  onChange={(e) =>
                    setSecondaryConfig((prev) => ({ ...prev, host: e.target.value }))
                  }
                />
              </div>

              <ConnectionTestButton
                provider={secondaryConfig.provider}
                model={secondaryConfig.model || null}
              />
            </>
          )}
        </CardContent>
      </Card>

      {/* SQL Server Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            SQL Server Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Host</label>
            <Input
              value={sqlSettings.host}
              onChange={(e) => setSqlSettings((prev) => ({ ...prev, host: e.target.value }))}
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Database Name</label>
            <Input
              value={sqlSettings.database}
              onChange={(e) => setSqlSettings((prev) => ({ ...prev, database: e.target.value }))}
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <Button onClick={handleSave} className="w-full">
        <Save className="mr-2 h-4 w-4" />
        Save Settings
      </Button>
    </div>
  );
}
