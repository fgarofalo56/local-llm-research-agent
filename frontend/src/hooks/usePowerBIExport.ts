import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/api/client';

interface PowerBIExportOptions {
  query: string;
  tableName: string;
  reportName?: string;
}

interface PowerBIExportResult {
  status: 'success' | 'error';
  file_path?: string;
  message?: string;
}

export function usePowerBIExport() {
  const [isExporting, setIsExporting] = useState(false);

  const exportMutation = useMutation({
    mutationFn: async (options: PowerBIExportOptions) => {
      setIsExporting(true);
      try {
        const result = await api.post<PowerBIExportResult>('/agent/powerbi-export', {
          query: options.query,
          table_name: options.tableName,
          report_name: options.reportName,
        });
        return result;
      } finally {
        setIsExporting(false);
      }
    },
  });

  return {
    exportToPowerBI: exportMutation.mutate,
    isExporting,
    result: exportMutation.data,
    error: exportMutation.error,
    reset: exportMutation.reset,
  };
}
