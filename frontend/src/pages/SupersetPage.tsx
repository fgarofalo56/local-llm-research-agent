/**
 * SupersetPage Component
 * Phase 3: Enterprise BI Platform Integration
 *
 * Page for viewing and embedding Apache Superset dashboards.
 * Lists available dashboards and allows embedding them in the React app.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ExternalLink,
  BarChart3,
  Loader2,
  RefreshCw,
  ArrowLeft,
  AlertCircle,
  Database,
  FileCode,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { SupersetEmbed } from '@/components/superset/SupersetEmbed';
import { api } from '@/api/client';

interface SupersetDashboard {
  id: number;
  dashboard_title: string;
  slug: string | null;
  description: string | null;
  published: boolean;
  charts: Array<{ id: number; slice_name: string }> | null;
  created_on: string | null;
  changed_on: string | null;
}

interface DashboardListResponse {
  dashboards: SupersetDashboard[];
  count: number;
}

interface SupersetHealthResponse {
  status: string;
  url: string;
  error: string | null;
}

export function SupersetPage() {
  const [selectedDashboard, setSelectedDashboard] = useState<number | null>(null);

  // Check Superset health
  const { data: healthData } = useQuery<SupersetHealthResponse>({
    queryKey: ['superset-health'],
    queryFn: () => api.get<SupersetHealthResponse>('/superset/health'),
    refetchInterval: 30000, // Check every 30 seconds
  });

  // Fetch dashboards
  const {
    data: dashboardsData,
    isLoading,
    error,
    refetch,
  } = useQuery<DashboardListResponse>({
    queryKey: ['superset-dashboards'],
    queryFn: () => api.get<DashboardListResponse>('/superset/dashboards'),
    enabled: healthData?.status === 'healthy',
  });

  const isSupersethealthy = healthData?.status === 'healthy';

  // If Superset is not healthy, show connection instructions
  if (healthData && !isSupersethealthy) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Superset Reports</h1>
          <p className="text-muted-foreground">
            Enterprise business intelligence dashboards powered by Apache Superset
          </p>
        </div>

        <div className="rounded-lg border bg-card p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-yellow-500 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Superset Not Available</h2>
          <p className="text-muted-foreground mb-4">
            Apache Superset is not running or not accessible.
          </p>
          <div className="bg-muted rounded-lg p-4 text-left max-w-lg mx-auto mb-4">
            <p className="font-mono text-sm mb-2">To start Superset:</p>
            <code className="text-xs bg-background px-2 py-1 rounded block">
              docker-compose -f docker/docker-compose.yml --env-file .env --profile superset up -d
            </code>
          </div>
          <p className="text-sm text-muted-foreground">
            Superset URL: {healthData.url}
            {healthData.error && <span className="block text-destructive">{healthData.error}</span>}
          </p>
          <Button variant="outline" className="mt-4" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Retry Connection
          </Button>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="rounded-lg border bg-card p-8 text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Failed to Load Dashboards</h2>
          <p className="text-muted-foreground mb-4">
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

  // If a dashboard is selected, show the embed view
  if (selectedDashboard !== null) {
    const dashboard = dashboardsData?.dashboards.find((d) => d.id === selectedDashboard);
    return (
      <div className="container mx-auto p-6">
        <Button variant="ghost" onClick={() => setSelectedDashboard(null)} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to dashboards
        </Button>
        <SupersetEmbed
          dashboardId={selectedDashboard}
          title={dashboard?.dashboard_title || 'Dashboard'}
          height="800px"
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Superset Reports</h1>
          <p className="text-muted-foreground">
            Enterprise business intelligence dashboards powered by Apache Superset
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => window.open('http://localhost:8088', '_blank')}>
            <ExternalLink className="mr-2 h-4 w-4" />
            Open Superset
          </Button>
        </div>
      </div>

      {/* Quick Links */}
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <button
          onClick={() => window.open('http://localhost:8088/sqllab/', '_blank')}
          className="flex items-center gap-3 rounded-lg border bg-card p-4 text-left hover:border-primary transition-colors"
        >
          <Database className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">SQL Lab</h3>
            <p className="text-sm text-muted-foreground">Run SQL queries directly</p>
          </div>
        </button>
        <button
          onClick={() => window.open('http://localhost:8088/chart/add', '_blank')}
          className="flex items-center gap-3 rounded-lg border bg-card p-4 text-left hover:border-primary transition-colors"
        >
          <BarChart3 className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">Create Chart</h3>
            <p className="text-sm text-muted-foreground">Build visualizations</p>
          </div>
        </button>
        <button
          onClick={() => window.open('http://localhost:8088/dashboard/list/', '_blank')}
          className="flex items-center gap-3 rounded-lg border bg-card p-4 text-left hover:border-primary transition-colors"
        >
          <FileCode className="h-8 w-8 text-primary" />
          <div>
            <h3 className="font-semibold">Manage Dashboards</h3>
            <p className="text-sm text-muted-foreground">Full dashboard management</p>
          </div>
        </button>
      </div>

      {/* Dashboard Grid */}
      {dashboardsData?.dashboards.length === 0 ? (
        <div className="rounded-lg border bg-card p-8 text-center">
          <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h2 className="text-xl font-semibold mb-2">No Dashboards Yet</h2>
          <p className="text-muted-foreground mb-4">
            Create your first dashboard in Superset to see it here.
          </p>
          <Button onClick={() => window.open('http://localhost:8088/dashboard/list/', '_blank')}>
            <ExternalLink className="mr-2 h-4 w-4" />
            Create Dashboard in Superset
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dashboardsData?.dashboards.map((dashboard) => (
            <button
              key={dashboard.id}
              className="rounded-lg border bg-card p-4 text-left hover:border-primary transition-colors"
              onClick={() => setSelectedDashboard(dashboard.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <BarChart3 className="h-6 w-6 text-primary" />
                {dashboard.published && (
                  <span className="text-xs bg-green-500/10 text-green-500 px-2 py-0.5 rounded">
                    Published
                  </span>
                )}
              </div>
              <h3 className="font-semibold mb-1">{dashboard.dashboard_title}</h3>
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                {dashboard.description || 'No description'}
              </p>
              <div className="text-xs text-muted-foreground">
                {dashboard.charts && (
                  <span className="mr-4">{dashboard.charts.length} charts</span>
                )}
                {dashboard.changed_on && (
                  <span>Updated: {new Date(dashboard.changed_on).toLocaleDateString()}</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
