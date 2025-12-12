import { useMemo } from 'react';
import { suggestChartType } from '@/lib/chartSuggestion';

/**
 * Hook to get chart type suggestion for given data
 */
export function useChartSuggestion(data: Record<string, unknown>[]) {
  return useMemo(() => suggestChartType(data), [data]);
}
