export type ChartType = 'bar' | 'line' | 'area' | 'pie' | 'scatter' | 'kpi' | 'table';

export interface ChartSuggestion {
  type: ChartType;
  confidence: number;
  xKey?: string;
  yKeys?: string[];
  reason: string;
}

function isNumericColumn(data: Record<string, unknown>[], key: string): boolean {
  return data.every(row => {
    const val = row[key];
    return val === null || val === undefined || typeof val === 'number' || !isNaN(Number(val));
  });
}

function isDateColumn(data: Record<string, unknown>[], key: string): boolean {
  const datePatterns = [
    /^\d{4}-\d{2}-\d{2}/, // YYYY-MM-DD
    /^\d{2}\/\d{2}\/\d{4}/, // MM/DD/YYYY
    /^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i, // Month names
    /^\d{4}$/, // Year only
    /^Q[1-4]\s*\d{4}$/i, // Quarter format Q1 2024
  ];

  return data.slice(0, 5).every(row => {
    const val = String(row[key] || '');
    return datePatterns.some(pattern => pattern.test(val));
  });
}

function getUniqueCount(data: Record<string, unknown>[], key: string): number {
  const unique = new Set(data.map(row => row[key]));
  return unique.size;
}

function hasMonotonicIncrease(data: Record<string, unknown>[], key: string): boolean {
  if (data.length < 2) return false;

  for (let i = 1; i < Math.min(data.length, 10); i++) {
    const prev = Number(data[i - 1][key]);
    const curr = Number(data[i][key]);
    if (!isNaN(prev) && !isNaN(curr) && curr < prev) {
      return false;
    }
  }
  return true;
}

export function suggestChartType(data: Record<string, unknown>[]): ChartSuggestion {
  if (!data || data.length === 0) {
    return { type: 'table', confidence: 1, reason: 'No data to visualize' };
  }

  const columns = Object.keys(data[0]);

  // Single value = KPI
  if (data.length === 1 && columns.length <= 2) {
    const numericCols = columns.filter(col => isNumericColumn(data, col));
    if (numericCols.length === 1) {
      return {
        type: 'kpi',
        confidence: 0.9,
        yKeys: numericCols,
        reason: 'Single numeric value detected',
      };
    }
  }

  // Find column types
  const categoricalCols = columns.filter(col => !isNumericColumn(data, col));
  const numericCols = columns.filter(col => isNumericColumn(data, col));
  const dateCols = columns.filter(col => isDateColumn(data, col));

  // Time series = Line chart
  if (dateCols.length > 0 && numericCols.length > 0) {
    return {
      type: 'line',
      confidence: 0.85,
      xKey: dateCols[0],
      yKeys: numericCols.slice(0, 3),
      reason: 'Time series data detected',
    };
  }

  // Index-like first column with numeric values = Line chart
  if (
    numericCols.length >= 2 &&
    hasMonotonicIncrease(data, columns[0]) &&
    data.length >= 5
  ) {
    return {
      type: 'line',
      confidence: 0.75,
      xKey: columns[0],
      yKeys: numericCols.filter(c => c !== columns[0]).slice(0, 3),
      reason: 'Sequential numeric data suitable for trend visualization',
    };
  }

  // Few categories with numeric values = Pie chart
  if (categoricalCols.length === 1 && numericCols.length === 1) {
    const uniqueCategories = getUniqueCount(data, categoricalCols[0]);
    if (uniqueCategories <= 8 && uniqueCategories === data.length) {
      return {
        type: 'pie',
        confidence: 0.8,
        xKey: categoricalCols[0],
        yKeys: numericCols,
        reason: 'Categorical distribution with small number of categories',
      };
    }
  }

  // Categories with numeric values = Bar chart
  if (categoricalCols.length >= 1 && numericCols.length >= 1) {
    return {
      type: 'bar',
      confidence: 0.75,
      xKey: categoricalCols[0],
      yKeys: numericCols.slice(0, 3),
      reason: 'Categorical comparison data',
    };
  }

  // Two numeric columns = Scatter
  if (numericCols.length >= 2 && categoricalCols.length === 0) {
    return {
      type: 'scatter',
      confidence: 0.7,
      xKey: numericCols[0],
      yKeys: [numericCols[1]],
      reason: 'Two numeric dimensions suitable for correlation',
    };
  }

  // Default to table
  return {
    type: 'table',
    confidence: 0.5,
    reason: 'Complex data structure, showing as table',
  };
}

export function getChartTypeLabel(type: ChartType): string {
  const labels: Record<ChartType, string> = {
    bar: 'Bar Chart',
    line: 'Line Chart',
    area: 'Area Chart',
    pie: 'Pie Chart',
    scatter: 'Scatter Plot',
    kpi: 'KPI Card',
    table: 'Data Table',
  };
  return labels[type];
}

export function getAvailableChartTypes(): { value: ChartType; label: string }[] {
  return [
    { value: 'bar', label: 'Bar Chart' },
    { value: 'line', label: 'Line Chart' },
    { value: 'area', label: 'Area Chart' },
    { value: 'pie', label: 'Pie Chart' },
    { value: 'scatter', label: 'Scatter Plot' },
    { value: 'kpi', label: 'KPI Card' },
    { value: 'table', label: 'Data Table' },
  ];
}
