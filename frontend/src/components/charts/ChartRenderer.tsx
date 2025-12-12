import { useMemo } from 'react';
import { BarChartComponent } from './BarChartComponent';
import { LineChartComponent } from './LineChartComponent';
import { AreaChartComponent } from './AreaChartComponent';
import { PieChartComponent } from './PieChartComponent';
import { ScatterChartComponent } from './ScatterChartComponent';
import { KPICard } from './KPICard';
import { DataTable } from './DataTable';
import { suggestChartType, type ChartType } from '@/lib/chartSuggestion';

export interface ChartConfig {
  type: ChartType;
  xKey?: string;
  yKeys?: string[];
  title?: string;
  colors?: string[];
}

interface ChartRendererProps {
  data: Record<string, unknown>[];
  config?: Partial<ChartConfig>;
  autoSuggest?: boolean;
}

export function ChartRenderer({ data, config, autoSuggest = true }: ChartRendererProps) {
  const suggestion = useMemo(() => suggestChartType(data), [data]);

  const chartType = config?.type || (autoSuggest ? suggestion.type : 'table');
  const xKey = config?.xKey || suggestion.xKey;
  const yKeys = config?.yKeys || suggestion.yKeys || [];
  const colors = config?.colors;

  if (!data || data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        No data available
      </div>
    );
  }

  switch (chartType) {
    case 'bar':
      return xKey && yKeys.length > 0 ? (
        <BarChartComponent data={data} xKey={xKey} yKeys={yKeys} colors={colors} />
      ) : (
        <DataTable data={data} />
      );

    case 'line':
      return xKey && yKeys.length > 0 ? (
        <LineChartComponent data={data} xKey={xKey} yKeys={yKeys} colors={colors} />
      ) : (
        <DataTable data={data} />
      );

    case 'area':
      return xKey && yKeys.length > 0 ? (
        <AreaChartComponent data={data} xKey={xKey} yKeys={yKeys} colors={colors} />
      ) : (
        <DataTable data={data} />
      );

    case 'pie':
      if (xKey && yKeys.length > 0) {
        const pieData = data.map(row => ({
          name: String(row[xKey]),
          value: Number(row[yKeys[0]]) || 0,
        }));
        return <PieChartComponent data={pieData} colors={colors} />;
      }
      return <DataTable data={data} />;

    case 'scatter':
      if (xKey && yKeys.length > 0) {
        return (
          <ScatterChartComponent
            data={data}
            xKey={xKey}
            yKey={yKeys[0]}
            color={colors?.[0]}
          />
        );
      }
      return <DataTable data={data} />;

    case 'kpi':
      if (yKeys.length > 0 && data.length > 0) {
        return (
          <KPICard
            title={config?.title || yKeys[0]}
            value={Number(data[0][yKeys[0]]) || 0}
          />
        );
      }
      return <DataTable data={data} />;

    case 'table':
    default:
      return <DataTable data={data} />;
  }
}

// Export suggestion info for UI use
export function useChartSuggestion(data: Record<string, unknown>[]) {
  return useMemo(() => suggestChartType(data), [data]);
}
