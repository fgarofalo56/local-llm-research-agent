import { useQuery } from '@tanstack/react-query';
import { Database, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface MCPServer {
  id: string;
  name: string;
  status?: 'connected' | 'disconnected' | 'error';
  tools?: string[];
  description: string | null;
  enabled?: boolean;
}

interface MCPServersResponse {
  servers: MCPServer[];
}

export function MCPServersPage() {
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => api.get<MCPServersResponse>('/mcp-servers'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">MCP Servers</h1>
          <p className="text-muted-foreground">
            View and manage Model Context Protocol server connections.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isRefetching}
        >
          <RefreshCw
            className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`}
          />
          Refresh
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : data?.servers.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Database className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No MCP servers configured</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Configure MCP servers in mcp_config.json to enable tool capabilities.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {data?.servers.map((server) => (
            <Card key={server.id}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    {server.name}
                  </span>
                  {server.status === 'connected' || server.enabled !== false ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {server.description && (
                  <p className="text-sm text-muted-foreground">
                    {server.description}
                  </p>
                )}
                {server.tools && server.tools.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                      Available Tools ({server.tools.length})
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {server.tools.map((tool) => (
                        <span
                          key={tool}
                          className="rounded-md bg-muted px-2 py-1 text-xs"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
