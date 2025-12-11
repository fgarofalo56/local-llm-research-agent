import type { ChartType } from '@/lib/chartSuggestion';

export type WidgetType = 'bar_chart' | 'line_chart' | 'area_chart' | 'pie_chart' | 'scatter_chart' | 'kpi_card' | 'table';

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface WidgetChartConfig {
  xKey?: string;
  yKeys?: string[];
  colors?: string[];
}

export interface DashboardWidget {
  id: number;
  dashboard_id: number;
  widget_type: WidgetType;
  title: string;
  query: string;
  chart_config: WidgetChartConfig | null;
  position: WidgetPosition;
  refresh_interval: number | null;
  created_at?: string;
  updated_at?: string;
}

export interface Dashboard {
  id: number;
  name: string;
  description: string | null;
  layout: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
  widgets?: DashboardWidget[];
}

export interface DashboardCreate {
  name: string;
  description?: string | null;
}

export interface DashboardUpdate {
  name?: string;
  description?: string | null;
  is_default?: boolean;
}

export interface WidgetCreate {
  widget_type: WidgetType;
  title: string;
  query: string;
  chart_config?: WidgetChartConfig | null;
  position: WidgetPosition;
  refresh_interval?: number | null;
}

export interface WidgetUpdate {
  widget_type?: WidgetType;
  title?: string;
  query?: string;
  chart_config?: WidgetChartConfig | null;
  position?: WidgetPosition;
  refresh_interval?: number | null;
}

export interface LayoutUpdate {
  widgets: {
    id: number;
    position: WidgetPosition;
  }[];
}

// Utility to convert widget type to chart type
export function widgetTypeToChartType(widgetType: WidgetType): ChartType {
  const mapping: Record<WidgetType, ChartType> = {
    bar_chart: 'bar',
    line_chart: 'line',
    area_chart: 'area',
    pie_chart: 'pie',
    scatter_chart: 'scatter',
    kpi_card: 'kpi',
    table: 'table',
  };
  return mapping[widgetType];
}

// Utility to convert chart type to widget type
export function chartTypeToWidgetType(chartType: ChartType): WidgetType {
  const mapping: Record<ChartType, WidgetType> = {
    bar: 'bar_chart',
    line: 'line_chart',
    area: 'area_chart',
    pie: 'pie_chart',
    scatter: 'scatter_chart',
    kpi: 'kpi_card',
    table: 'table',
  };
  return mapping[chartType];
}
