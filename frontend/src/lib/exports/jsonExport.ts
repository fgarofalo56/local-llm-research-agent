import { saveAs } from 'file-saver';
import type { Dashboard, DashboardWidget, WidgetPosition } from '@/types/dashboard';

export interface DashboardExport {
  version: string;
  exportedAt: string;
  dashboard: {
    name: string;
    description: string | null;
  };
  widgets: {
    widget_type: string;
    title: string;
    query: string;
    chart_config: Record<string, unknown> | null;
    position: WidgetPosition;
    refresh_interval: number | null;
  }[];
}

export function exportDashboardToJson(
  dashboard: Dashboard,
  widgets: DashboardWidget[]
): void {
  const exportData: DashboardExport = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    dashboard: {
      name: dashboard.name,
      description: dashboard.description,
    },
    widgets: widgets.map((w) => ({
      widget_type: w.widget_type,
      title: w.title,
      query: w.query,
      chart_config: w.chart_config as Record<string, unknown> | null,
      position: w.position,
      refresh_interval: w.refresh_interval,
    })),
  };

  const json = JSON.stringify(exportData, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  saveAs(blob, `${dashboard.name.toLowerCase().replace(/\s+/g, '-')}.json`);
}

export async function importDashboardFromJson(
  file: File
): Promise<DashboardExport> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        // Validate structure
        if (!data.version || !data.dashboard || !data.widgets) {
          throw new Error('Invalid dashboard export format');
        }
        resolve(data);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}
