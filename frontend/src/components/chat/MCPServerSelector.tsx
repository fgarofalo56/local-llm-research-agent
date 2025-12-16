import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useChatStore } from '@/stores/chatStore';
import * as Switch from '@radix-ui/react-switch';
import { Database, Globe, BarChart } from 'lucide-react';

interface MCPServerListItem {
  id: string;
  name: string;
  enabled: boolean;
}

interface MCPServersResponse {
  servers: MCPServerListItem[];
  total: number;
}

const serverIcons: Record<string, typeof Database> = {
  mssql: Database,
  'microsoft-learn': Globe,
  'powerbi-modeling': BarChart,
};

export function MCPServerSelector() {
  const { data } = useQuery({
    queryKey: ['mcp-servers'],
    queryFn: () => api.get<MCPServersResponse>('/mcp-servers'),
  });

  const servers = data?.servers ?? [];
  const { selectedMCPServers, toggleMCPServer } = useChatStore();

  const servers = data?.servers;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground">Active Tools</h3>
      <div className="flex flex-wrap gap-3">
        {servers.filter(s => s.enabled !== false).map((server) => {
          const Icon = serverIcons[server.id] || Database;
          const isSelected = selectedMCPServers.includes(server.id);

          return (
            <div
              key={server.id}
              className="flex items-center gap-2 rounded-md border bg-card px-3 py-2"
            >
              <Icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">{server.name}</span>
              <Switch.Root
                checked={isSelected}
                onCheckedChange={() => toggleMCPServer(server.id)}
                className="relative h-5 w-9 rounded-full bg-muted data-[state=checked]:bg-primary"
              >
                <Switch.Thumb className="block h-4 w-4 translate-x-0.5 rounded-full bg-white transition-transform data-[state=checked]:translate-x-4" />
              </Switch.Root>
            </div>
          );
        })}
      </div>
    </div>
  );
}
