import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Activity,
  Clock,
  Database,
  FileText,
  MessageSquare,
  Server,
  TrendingUp,
  Zap,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { api } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

// Types
interface QueryPerformanceStats {
  total_queries: number;
  avg_execution_time_ms: number | null;
  min_execution_time_ms: number | null;
  max_execution_time_ms: number | null;
  median_execution_time_ms: number | null;
  total_rows_returned: number;
  queries_today: number;
  queries_this_week: number;
  queries_this_month: number;
}

interface SystemMetrics {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  total_queries: number;
  avg_messages_per_conversation: number;
  active_mcp_servers: number;
  database_status: string;
  cache_status: string;
}

interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: string;
  evictions: number;
  size: number;
  max_size: number;
  ttl_seconds: number;
}

interface DashboardOverview {
  query_stats: QueryPerformanceStats;
  system_metrics: SystemMetrics;
  cache_stats: CacheStats | null;
}

interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

interface SlowQuery {
  id: number;
  natural_language: string;
  generated_sql: string | null;
  execution_time_ms: number;
  row_count: number | null;
  created_at: string;
}

interface ToolUsageStats {
  tool_name: string;
  usage_count: number;
  percentage: number;
}

interface ToolUsageResponse {
  total_tool_calls: number;
  tools: ToolUsageStats[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16'];

// Stat Card Component
function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp,
  className = '',
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  trendUp?: boolean;
  className?: string;
}) {
  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {trend && (
            <p className={`text-xs mt-1 ${trendUp ? 'text-green-500' : 'text-red-500'}`}>
              {trend}
            </p>
          )}
        </div>
        <div className="rounded-full bg-primary/10 p-3">
          <Icon className="h-5 w-5 text-primary" />
        </div>
      </div>
    </Card>
  );
}

export function AnalyticsPage() {
  const [performancePeriod, setPerformancePeriod] = useState<'hour' | 'day' | 'week' | 'month'>('day');
  const [activityPeriod, setActivityPeriod] = useState<'day' | 'week' | 'month'>('week');

  // Fetch dashboard overview
  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useQuery<DashboardOverview>({
    queryKey: ['analytics', 'overview'],
    queryFn: () => api.get<DashboardOverview>('/analytics/overview'),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch query performance timeline
  const { data: performanceData } = useQuery<{ data: TimeSeriesPoint[] }>({
    queryKey: ['analytics', 'performance', performancePeriod],
    queryFn: () => api.get<{ data: TimeSeriesPoint[] }>(`/analytics/queries/performance?period=${performancePeriod}`),
  });

  // Fetch slow queries
  const { data: slowQueries } = useQuery<{ queries: SlowQuery[] }>({
    queryKey: ['analytics', 'slow-queries'],
    queryFn: () => api.get<{ queries: SlowQuery[] }>('/analytics/queries/slow?limit=10&threshold_ms=500'),
  });

  // Fetch tool usage
  const { data: toolUsage } = useQuery<ToolUsageResponse>({
    queryKey: ['analytics', 'tool-usage'],
    queryFn: () => api.get<ToolUsageResponse>('/analytics/tools/usage?days=30'),
  });

  // Fetch conversation activity
  const { data: activityData } = useQuery<TimeSeriesPoint[]>({
    queryKey: ['analytics', 'activity', activityPeriod],
    queryFn: () => api.get<TimeSeriesPoint[]>(`/analytics/conversations/activity?period=${activityPeriod}`),
  });

  // Fetch document stats
  const { data: docStats } = useQuery<{
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    total_chunks: number;
  }>({
    queryKey: ['analytics', 'documents'],
    queryFn: () => api.get<{
      by_status: Record<string, number>;
      by_type: Record<string, number>;
      total_chunks: number;
    }>('/analytics/documents/stats'),
  });

  if (overviewLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const queryStats = overview?.query_stats;
  const systemMetrics = overview?.system_metrics;
  const cacheStats = overview?.cache_stats;

  // Prepare chart data
  const performanceChartData = performanceData?.data?.map((p) => ({
    name: p.timestamp,
    avgTime: p.value,
  })) || [];

  const activityChartData = activityData?.map((p) => ({
    name: p.timestamp,
    messages: p.value,
  })) || [];

  const toolPieData = toolUsage?.tools.map((t) => ({
    name: t.tool_name,
    value: t.usage_count,
  })) || [];

  const docStatusData = docStats?.by_status
    ? Object.entries(docStats.by_status).map(([status, count]) => ({
        name: status,
        value: count,
      }))
    : [];

  return (
    <div className="container mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">Monitor query performance and system metrics</p>
        </div>
        <Button variant="outline" onClick={() => refetchOverview()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Queries"
          value={queryStats?.total_queries || 0}
          icon={Database}
        />
        <StatCard
          title="Avg Execution Time"
          value={queryStats?.avg_execution_time_ms ? `${queryStats.avg_execution_time_ms.toFixed(0)}ms` : 'N/A'}
          icon={Clock}
        />
        <StatCard
          title="Queries Today"
          value={queryStats?.queries_today || 0}
          icon={TrendingUp}
          trend={queryStats?.queries_this_week ? `${queryStats.queries_this_week} this week` : undefined}
          trendUp={true}
        />
        <StatCard
          title="Total Messages"
          value={systemMetrics?.total_messages || 0}
          icon={MessageSquare}
        />
      </div>

      {/* System Status */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Conversations"
          value={systemMetrics?.total_conversations || 0}
          icon={MessageSquare}
        />
        <StatCard
          title="Documents"
          value={systemMetrics?.total_documents || 0}
          icon={FileText}
        />
        <StatCard
          title="Active MCP Servers"
          value={systemMetrics?.active_mcp_servers || 0}
          icon={Server}
        />
        <StatCard
          title="Cache Hit Rate"
          value={cacheStats?.hit_rate || 'N/A'}
          icon={Zap}
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Query Performance Timeline */}
        <Card className="p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold">Query Execution Time</h3>
            <div className="flex gap-1">
              {(['hour', 'day', 'week', 'month'] as const).map((period) => (
                <Button
                  key={period}
                  variant={performancePeriod === period ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setPerformancePeriod(period)}
                >
                  {period.charAt(0).toUpperCase() + period.slice(1)}
                </Button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="avgTime"
                name="Avg Time (ms)"
                stroke="#3b82f6"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        {/* Conversation Activity */}
        <Card className="p-4">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-semibold">Message Activity</h3>
            <div className="flex gap-1">
              {(['day', 'week', 'month'] as const).map((period) => (
                <Button
                  key={period}
                  variant={activityPeriod === period ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setActivityPeriod(period)}
                >
                  {period.charAt(0).toUpperCase() + period.slice(1)}
                </Button>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={activityChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="messages" name="Messages" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Tool Usage Pie Chart */}
        <Card className="p-4">
          <h3 className="mb-4 font-semibold">MCP Tool Usage (Last 30 Days)</h3>
          {toolPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={toolPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {toolPieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              No tool usage data available
            </div>
          )}
          <div className="mt-2 text-center text-sm text-muted-foreground">
            Total Tool Calls: {toolUsage?.total_tool_calls || 0}
          </div>
        </Card>

        {/* Document Status */}
        <Card className="p-4">
          <h3 className="mb-4 font-semibold">Document Processing Status</h3>
          {docStatusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={docStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {docStatusData.map((entry, index) => {
                    let color = COLORS[index % COLORS.length];
                    if (entry.name === 'completed') color = '#10b981';
                    else if (entry.name === 'failed') color = '#ef4444';
                    else if (entry.name === 'processing') color = '#f59e0b';
                    else if (entry.name === 'pending') color = '#6b7280';
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              No document data available
            </div>
          )}
          <div className="mt-2 text-center text-sm text-muted-foreground">
            Total Chunks: {docStats?.total_chunks || 0}
          </div>
        </Card>
      </div>

      {/* Slow Queries Table */}
      <Card className="p-4">
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          <h3 className="font-semibold">Top Slow Queries (&gt;500ms)</h3>
        </div>
        {slowQueries?.queries && slowQueries.queries.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="py-2 text-left font-medium">Query</th>
                  <th className="py-2 text-right font-medium">Time (ms)</th>
                  <th className="py-2 text-right font-medium">Rows</th>
                  <th className="py-2 text-right font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {slowQueries.queries.map((q) => (
                  <tr key={q.id} className="border-b last:border-0">
                    <td className="max-w-md truncate py-2" title={q.natural_language}>
                      {q.natural_language}
                    </td>
                    <td className="py-2 text-right font-mono text-amber-500">
                      {q.execution_time_ms}
                    </td>
                    <td className="py-2 text-right font-mono">
                      {q.row_count ?? '-'}
                    </td>
                    <td className="py-2 text-right text-muted-foreground">
                      {new Date(q.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-muted-foreground">
            <Activity className="mx-auto mb-2 h-8 w-8 opacity-50" />
            <p>No slow queries found</p>
            <p className="text-xs">Queries taking over 500ms will appear here</p>
          </div>
        )}
      </Card>

      {/* Cache Stats (if available) */}
      {cacheStats && (
        <Card className="p-4">
          <h3 className="mb-4 font-semibold">Cache Performance</h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">Hits</p>
              <p className="text-xl font-bold text-green-500">{cacheStats.hits.toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">Misses</p>
              <p className="text-xl font-bold text-red-500">{cacheStats.misses.toLocaleString()}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">Hit Rate</p>
              <p className="text-xl font-bold text-blue-500">{cacheStats.hit_rate}</p>
            </div>
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">Evictions</p>
              <p className="text-xl font-bold">{cacheStats.evictions.toLocaleString()}</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
