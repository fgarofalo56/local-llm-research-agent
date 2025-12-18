/**
 * SupersetEmbed Component
 * Phase 3: Enterprise BI Platform Integration
 *
 * Embeds an Apache Superset dashboard in an iframe with guest token authentication.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2, ExternalLink, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api } from '@/api/client';

interface SupersetEmbedProps {
  dashboardId: number;
  title?: string;
  height?: string;
}

interface EmbedResponse {
  embed_url: string;
  dashboard_id: string;
}

export function SupersetEmbed({
  dashboardId,
  title = 'Superset Dashboard',
  height = '600px',
}: SupersetEmbedProps) {
  const [refreshKey, setRefreshKey] = useState(0);

  const { data, isLoading, error, refetch } = useQuery<EmbedResponse>({
    queryKey: ['superset-embed', dashboardId, refreshKey],
    queryFn: () => api.get<EmbedResponse>(`/superset/embed/${dashboardId}`),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="rounded-lg border bg-card">
        <div className="flex h-96 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border bg-card">
        <div className="flex h-96 flex-col items-center justify-center text-destructive">
          <AlertCircle className="h-8 w-8 mb-2" />
          <p className="mb-4">Failed to load Superset dashboard</p>
          <p className="text-sm text-muted-foreground mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Extract base Superset URL from embed URL for external link
  const supersetBaseUrl = data?.embed_url
    ? data.embed_url.split('/embedded/')[0]
    : 'http://localhost:8088';

  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <div className="flex items-center justify-between border-b px-4 py-2">
        <h3 className="font-semibold">{title}</h3>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setRefreshKey((k) => k + 1)}
            title="Refresh dashboard"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              window.open(`${supersetBaseUrl}/superset/dashboard/${dashboardId}/`, '_blank')
            }
            title="Open in Superset"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="p-0">
        {data?.embed_url && (
          <iframe
            src={data.embed_url}
            width="100%"
            height={height}
            frameBorder="0"
            style={{ border: 'none' }}
            title={title}
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
          />
        )}
      </div>
    </div>
  );
}
