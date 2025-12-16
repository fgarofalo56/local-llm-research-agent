import { useRef, useState } from 'react';
import { ExportMenu } from '@/components/export/ExportMenu';
import { PowerBIExportDialog } from '@/components/dialogs/PowerBIExportDialog';
import { ChartRenderer } from './ChartRenderer';
import { DataTable } from './DataTable';
import { suggestChartType } from '@/lib/chartSuggestion';
import { Button } from '@/components/ui/Button';
import { BarChart2, Table } from 'lucide-react';

interface QueryResultPanelProps {
  data: Record<string, unknown>[];
  query: string;
  title?: string;
}

export function QueryResultPanel({ data, query, title }: QueryResultPanelProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [showPowerBIDialog, setShowPowerBIDialog] = useState(false);
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');

  const suggestion = suggestChartType(data);

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b p-3">
        <h3 className="font-medium">{title || 'Query Results'}</h3>
        <div className="flex gap-2">
          {/* View toggle */}
          <div className="flex rounded-md border">
            <Button
              variant={viewMode === 'chart' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-r-none"
              onClick={() => setViewMode('chart')}
            >
              <BarChart2 className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'table' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-l-none"
              onClick={() => setViewMode('table')}
            >
              <Table className="h-4 w-4" />
            </Button>
          </div>

          <ExportMenu
            elementRef={chartRef}
            data={data}
            filename={title || 'query-result'}
            title={title}
            showPowerBI={true}
            onPowerBIExport={() => setShowPowerBIDialog(true)}
          />
        </div>
      </div>

      <div ref={chartRef} className="min-h-[300px] p-4">
        {viewMode === 'chart' ? (
          <ChartRenderer data={data} config={{ type: suggestion.type }} />
        ) : (
          <DataTable data={data} />
        )}
      </div>

      <PowerBIExportDialog
        open={showPowerBIDialog}
        onClose={() => setShowPowerBIDialog(false)}
        query={query}
        suggestedTableName={title?.replace(/\s+/g, '') || 'QueryResults'}
      />
    </div>
  );
}
