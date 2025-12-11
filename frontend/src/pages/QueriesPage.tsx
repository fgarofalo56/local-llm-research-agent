import { useState } from 'react';
import { History, Star, Clock, Play } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface Query {
  id: number;
  sql: string;
  natural_language: string | null;
  is_favorite: boolean;
  execution_count: number;
  avg_execution_time: number | null;
  created_at: string;
}

interface QueriesResponse {
  queries: Query[];
  total: number;
}

export function QueriesPage() {
  const [showFavorites, setShowFavorites] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['queries', showFavorites],
    queryFn: () =>
      api.get<QueriesResponse>(
        showFavorites ? '/queries?is_favorite=true' : '/queries'
      ),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Query History</h1>
          <p className="text-muted-foreground">
            View and manage your saved SQL queries.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showFavorites ? 'default' : 'outline'}
            onClick={() => setShowFavorites(!showFavorites)}
          >
            <Star className="mr-2 h-4 w-4" />
            Favorites
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : data?.queries.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <History className="h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-medium">No queries yet</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Your SQL query history will appear here after you start chatting.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data?.queries.map((query) => (
            <Card key={query.id}>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    {query.is_favorite && (
                      <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" />
                    )}
                    {query.natural_language || 'SQL Query'}
                  </span>
                  <span className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Play className="h-3 w-3" />
                      {query.execution_count}x
                    </span>
                    {query.avg_execution_time && (
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {query.avg_execution_time.toFixed(0)}ms
                      </span>
                    )}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="overflow-x-auto rounded-md bg-muted p-3 text-sm">
                  <code>{query.sql}</code>
                </pre>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
