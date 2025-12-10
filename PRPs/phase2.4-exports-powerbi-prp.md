# Phase 2.4: Export System & Power BI Integration

## Overview

| Attribute | Value |
|-----------|-------|
| **Phase** | 2.4 |
| **Focus** | Export Formats, Power BI MCP |
| **Estimated Effort** | 2-3 days |
| **Prerequisites** | Phase 2.3 complete |

## Goal

Implement comprehensive export capabilities including PNG, PDF, CSV, Excel, JSON for charts and dashboards, chat transcript exports, and Power BI integration via MCP for PBIX file generation.

## Success Criteria

- [ ] Charts export to PNG
- [ ] Dashboards export to PDF with all widgets
- [ ] Query results export to CSV and Excel
- [ ] Dashboard configurations export/import as JSON
- [ ] Chat conversations export to Markdown and PDF
- [ ] Power BI MCP integration creates PBIX files
- [ ] Export dropdown menu on charts and dashboards
- [ ] Download links work correctly

## Technology Stack Additions

```bash
cd frontend
npm install html2canvas jspdf xlsx file-saver
npm install -D @types/file-saver
```

## Implementation Plan

### Step 1: Export Utilities

#### 1.1 PNG Export (html2canvas)

```typescript
// frontend/src/lib/exports/pngExport.ts
import html2canvas from 'html2canvas';

export async function exportToPng(
  element: HTMLElement,
  filename: string = 'chart.png'
): Promise<void> {
  const canvas = await html2canvas(element, {
    backgroundColor: null,
    scale: 2, // Higher resolution
    logging: false,
    useCORS: true,
  });

  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

export async function elementToDataUrl(element: HTMLElement): Promise<string> {
  const canvas = await html2canvas(element, {
    backgroundColor: null,
    scale: 2,
    logging: false,
    useCORS: true,
  });
  return canvas.toDataURL('image/png');
}
```

#### 1.2 PDF Export (jsPDF)

```typescript
// frontend/src/lib/exports/pdfExport.ts
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

interface PdfExportOptions {
  title?: string;
  orientation?: 'portrait' | 'landscape';
  includeTimestamp?: boolean;
}

export async function exportToPdf(
  element: HTMLElement,
  filename: string = 'export.pdf',
  options: PdfExportOptions = {}
): Promise<void> {
  const {
    title,
    orientation = 'landscape',
    includeTimestamp = true,
  } = options;

  const canvas = await html2canvas(element, {
    backgroundColor: '#ffffff',
    scale: 2,
    logging: false,
    useCORS: true,
  });

  const imgData = canvas.toDataURL('image/png');
  const pdf = new jsPDF({
    orientation,
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 10;

  // Add title if provided
  let yOffset = margin;
  if (title) {
    pdf.setFontSize(16);
    pdf.text(title, margin, yOffset + 5);
    yOffset += 15;
  }

  // Add timestamp
  if (includeTimestamp) {
    pdf.setFontSize(10);
    pdf.setTextColor(128);
    pdf.text(
      `Generated: ${new Date().toLocaleString()}`,
      margin,
      yOffset + 3
    );
    yOffset += 10;
    pdf.setTextColor(0);
  }

  // Calculate image dimensions to fit page
  const imgWidth = pageWidth - 2 * margin;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  // Add image (may span multiple pages)
  let remainingHeight = imgHeight;
  let sourceY = 0;

  while (remainingHeight > 0) {
    const availableHeight = pageHeight - yOffset - margin;
    const drawHeight = Math.min(remainingHeight, availableHeight);
    
    // Calculate source rectangle
    const sourceHeight = (drawHeight / imgHeight) * canvas.height;
    
    pdf.addImage(
      imgData,
      'PNG',
      margin,
      yOffset,
      imgWidth,
      drawHeight,
      undefined,
      'FAST'
    );

    remainingHeight -= drawHeight;
    sourceY += sourceHeight;

    if (remainingHeight > 0) {
      pdf.addPage();
      yOffset = margin;
    }
  }

  pdf.save(filename);
}

export async function exportDashboardToPdf(
  dashboardElement: HTMLElement,
  dashboardName: string
): Promise<void> {
  await exportToPdf(dashboardElement, `${dashboardName}.pdf`, {
    title: dashboardName,
    orientation: 'landscape',
    includeTimestamp: true,
  });
}
```

#### 1.3 CSV Export

```typescript
// frontend/src/lib/exports/csvExport.ts
import { saveAs } from 'file-saver';

export function exportToCsv(
  data: Record<string, unknown>[],
  filename: string = 'data.csv'
): void {
  if (data.length === 0) return;

  const columns = Object.keys(data[0]);
  
  // Create header row
  const header = columns.map(col => `"${col}"`).join(',');
  
  // Create data rows
  const rows = data.map(row => {
    return columns.map(col => {
      const value = row[col];
      if (value === null || value === undefined) return '';
      if (typeof value === 'string') {
        // Escape quotes and wrap in quotes
        return `"${value.replace(/"/g, '""')}"`;
      }
      return String(value);
    }).join(',');
  });

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
  saveAs(blob, filename);
}
```

#### 1.4 Excel Export (SheetJS)

```typescript
// frontend/src/lib/exports/excelExport.ts
import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

interface ExcelExportOptions {
  sheetName?: string;
  includeHeaders?: boolean;
  columnWidths?: number[];
}

export function exportToExcel(
  data: Record<string, unknown>[],
  filename: string = 'data.xlsx',
  options: ExcelExportOptions = {}
): void {
  const {
    sheetName = 'Data',
    includeHeaders = true,
    columnWidths,
  } = options;

  // Create worksheet
  const worksheet = XLSX.utils.json_to_sheet(data, {
    header: includeHeaders ? undefined : Object.keys(data[0] || {}),
  });

  // Set column widths if provided
  if (columnWidths) {
    worksheet['!cols'] = columnWidths.map(w => ({ wch: w }));
  } else {
    // Auto-calculate column widths
    const columns = Object.keys(data[0] || {});
    worksheet['!cols'] = columns.map(col => {
      const maxLength = Math.max(
        col.length,
        ...data.map(row => String(row[col] || '').length)
      );
      return { wch: Math.min(maxLength + 2, 50) };
    });
  }

  // Create workbook
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);

  // Generate buffer
  const excelBuffer = XLSX.write(workbook, {
    bookType: 'xlsx',
    type: 'array',
  });

  const blob = new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  saveAs(blob, filename);
}

export function exportMultipleSheetsToExcel(
  sheets: { name: string; data: Record<string, unknown>[] }[],
  filename: string = 'data.xlsx'
): void {
  const workbook = XLSX.utils.book_new();

  sheets.forEach(({ name, data }) => {
    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, name.slice(0, 31)); // Sheet name max 31 chars
  });

  const excelBuffer = XLSX.write(workbook, {
    bookType: 'xlsx',
    type: 'array',
  });

  const blob = new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  saveAs(blob, filename);
}
```

#### 1.5 JSON Export (Dashboard Config)

```typescript
// frontend/src/lib/exports/jsonExport.ts
import { saveAs } from 'file-saver';
import { Dashboard, DashboardWidget } from '@/types/dashboard';

interface DashboardExport {
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
    chart_config: Record<string, unknown>;
    position: { x: number; y: number; w: number; h: number };
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
    widgets: widgets.map(w => ({
      widget_type: w.widget_type,
      title: w.title,
      query: w.query,
      chart_config: w.chart_config,
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
```

---

### Step 2: Chat Export

#### 2.1 Markdown Export

```typescript
// frontend/src/lib/exports/chatExport.ts
import { saveAs } from 'file-saver';
import jsPDF from 'jspdf';
import { Conversation, Message } from '@/types';

export function exportChatToMarkdown(
  conversation: Conversation,
  messages: Message[]
): void {
  const lines: string[] = [];
  
  // Title
  lines.push(`# ${conversation.title || `Conversation ${conversation.id}`}`);
  lines.push('');
  lines.push(`*Exported: ${new Date().toLocaleString()}*`);
  lines.push('');
  lines.push('---');
  lines.push('');

  // Messages
  messages.forEach((msg) => {
    const role = msg.role === 'user' ? '**You**' : '**Assistant**';
    const timestamp = new Date(msg.created_at).toLocaleString();
    
    lines.push(`### ${role}`);
    lines.push(`*${timestamp}*`);
    lines.push('');
    lines.push(msg.content);
    lines.push('');
    
    // Include tool calls if present
    if (msg.tool_calls) {
      try {
        const tools = JSON.parse(msg.tool_calls);
        if (tools.length > 0) {
          lines.push('> **Tools used:**');
          tools.forEach((tool: { name: string }) => {
            lines.push(`> - ${tool.name}`);
          });
          lines.push('');
        }
      } catch {
        // Ignore parse errors
      }
    }
    
    lines.push('---');
    lines.push('');
  });

  const markdown = lines.join('\n');
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  saveAs(blob, `${conversation.title || 'conversation'}.md`);
}

export function exportChatToPdf(
  conversation: Conversation,
  messages: Message[]
): void {
  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 15;
  const maxWidth = pageWidth - 2 * margin;
  let yOffset = margin;

  // Title
  pdf.setFontSize(18);
  pdf.setFont('helvetica', 'bold');
  pdf.text(conversation.title || `Conversation ${conversation.id}`, margin, yOffset);
  yOffset += 10;

  // Export date
  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'italic');
  pdf.setTextColor(128);
  pdf.text(`Exported: ${new Date().toLocaleString()}`, margin, yOffset);
  yOffset += 10;
  pdf.setTextColor(0);

  // Separator
  pdf.setDrawColor(200);
  pdf.line(margin, yOffset, pageWidth - margin, yOffset);
  yOffset += 10;

  // Messages
  messages.forEach((msg) => {
    // Check if we need a new page
    if (yOffset > pageHeight - 30) {
      pdf.addPage();
      yOffset = margin;
    }

    // Role header
    pdf.setFontSize(11);
    pdf.setFont('helvetica', 'bold');
    const role = msg.role === 'user' ? 'You' : 'Assistant';
    pdf.text(role, margin, yOffset);
    
    // Timestamp
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    pdf.setTextColor(128);
    const timestamp = new Date(msg.created_at).toLocaleString();
    pdf.text(timestamp, margin + 30, yOffset);
    pdf.setTextColor(0);
    yOffset += 6;

    // Content
    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    
    // Split content into lines that fit
    const lines = pdf.splitTextToSize(msg.content, maxWidth);
    lines.forEach((line: string) => {
      if (yOffset > pageHeight - 15) {
        pdf.addPage();
        yOffset = margin;
      }
      pdf.text(line, margin, yOffset);
      yOffset += 5;
    });

    yOffset += 5;

    // Separator
    pdf.setDrawColor(230);
    pdf.line(margin, yOffset, pageWidth - margin, yOffset);
    yOffset += 8;
  });

  pdf.save(`${conversation.title || 'conversation'}.pdf`);
}
```

---

### Step 3: Export Menu Component

```typescript
// frontend/src/components/export/ExportMenu.tsx
import { useState } from 'react';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { 
  Download, 
  Image, 
  FileText, 
  Table, 
  FileSpreadsheet, 
  FileJson,
  FileType,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { exportToPng } from '@/lib/exports/pngExport';
import { exportToPdf } from '@/lib/exports/pdfExport';
import { exportToCsv } from '@/lib/exports/csvExport';
import { exportToExcel } from '@/lib/exports/excelExport';

interface ExportMenuProps {
  elementRef?: React.RefObject<HTMLElement>;
  data?: Record<string, unknown>[];
  filename?: string;
  title?: string;
  onPowerBIExport?: () => void;
  showPowerBI?: boolean;
}

export function ExportMenu({
  elementRef,
  data,
  filename = 'export',
  title,
  onPowerBIExport,
  showPowerBI = false,
}: ExportMenuProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (type: string) => {
    setIsExporting(true);
    try {
      switch (type) {
        case 'png':
          if (elementRef?.current) {
            await exportToPng(elementRef.current, `${filename}.png`);
          }
          break;
        case 'pdf':
          if (elementRef?.current) {
            await exportToPdf(elementRef.current, `${filename}.pdf`, { title });
          }
          break;
        case 'csv':
          if (data) {
            exportToCsv(data, `${filename}.csv`);
          }
          break;
        case 'excel':
          if (data) {
            exportToExcel(data, `${filename}.xlsx`);
          }
          break;
        case 'powerbi':
          onPowerBIExport?.();
          break;
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button variant="outline" size="sm" disabled={isExporting}>
          {isExporting ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Export
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          className="min-w-[160px] rounded-md border bg-card p-1 shadow-md"
          sideOffset={5}
        >
          {elementRef && (
            <>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('png')}
              >
                <Image className="mr-2 h-4 w-4" />
                PNG Image
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('pdf')}
              >
                <FileText className="mr-2 h-4 w-4" />
                PDF Document
              </DropdownMenu.Item>
              <DropdownMenu.Separator className="my-1 h-px bg-border" />
            </>
          )}
          
          {data && (
            <>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('csv')}
              >
                <Table className="mr-2 h-4 w-4" />
                CSV
              </DropdownMenu.Item>
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('excel')}
              >
                <FileSpreadsheet className="mr-2 h-4 w-4" />
                Excel
              </DropdownMenu.Item>
            </>
          )}

          {showPowerBI && (
            <>
              <DropdownMenu.Separator className="my-1 h-px bg-border" />
              <DropdownMenu.Item
                className="flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent"
                onClick={() => handleExport('powerbi')}
              >
                <FileType className="mr-2 h-4 w-4" />
                Power BI (.pbix)
              </DropdownMenu.Item>
            </>
          )}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
```

---

### Step 4: Dashboard Export Integration

```typescript
// frontend/src/components/dashboard/DashboardHeader.tsx
import { useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Download, Upload, Edit, Save, Plus, Settings } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ExportMenu } from '@/components/export/ExportMenu';
import { exportDashboardToJson, importDashboardFromJson } from '@/lib/exports/jsonExport';
import { exportDashboardToPdf } from '@/lib/exports/pdfExport';
import { Dashboard, DashboardWidget } from '@/types/dashboard';
import { api } from '@/api/client';

interface DashboardHeaderProps {
  dashboard: Dashboard;
  widgets: DashboardWidget[];
  gridRef: React.RefObject<HTMLDivElement>;
  isEditing: boolean;
  onEditToggle: () => void;
  onSave: () => void;
}

export function DashboardHeader({
  dashboard,
  widgets,
  gridRef,
  isEditing,
  onEditToggle,
  onSave,
}: DashboardHeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const importData = await importDashboardFromJson(file);
      
      // Create new dashboard
      const newDashboard = await api.post<Dashboard>('/dashboards', {
        name: `${importData.dashboard.name} (Imported)`,
        description: importData.dashboard.description,
      });

      // Create widgets
      for (const widget of importData.widgets) {
        await api.post(`/dashboards/${newDashboard.id}/widgets`, widget);
      }

      return newDashboard;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboards'] });
    },
  });

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      importMutation.mutate(file);
    }
  };

  const handleExportJson = () => {
    exportDashboardToJson(dashboard, widgets);
  };

  const handleExportPdf = async () => {
    if (gridRef.current) {
      await exportDashboardToPdf(gridRef.current, dashboard.name);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <h1 className="text-2xl font-bold">{dashboard.name}</h1>

      <div className="flex gap-2">
        {/* Import/Export */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          className="hidden"
          onChange={handleImport}
        />
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="mr-2 h-4 w-4" />
          Import
        </Button>

        <Button variant="outline" size="sm" onClick={handleExportJson}>
          <Download className="mr-2 h-4 w-4" />
          Export JSON
        </Button>

        <Button variant="outline" size="sm" onClick={handleExportPdf}>
          <Download className="mr-2 h-4 w-4" />
          Export PDF
        </Button>

        {/* Edit Mode */}
        {isEditing ? (
          <Button size="sm" onClick={onSave}>
            <Save className="mr-2 h-4 w-4" />
            Save
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={onEditToggle}>
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        )}
      </div>
    </div>
  );
}
```

---

### Step 5: Power BI MCP Integration

#### 5.1 Power BI Export Hook

```typescript
// frontend/src/hooks/usePowerBIExport.ts
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
  };
}
```

#### 5.2 Power BI Export Dialog

```typescript
// frontend/src/components/dialogs/PowerBIExportDialog.tsx
import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, FileType, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { usePowerBIExport } from '@/hooks/usePowerBIExport';

interface PowerBIExportDialogProps {
  open: boolean;
  onClose: () => void;
  query: string;
  suggestedTableName?: string;
}

export function PowerBIExportDialog({
  open,
  onClose,
  query,
  suggestedTableName = 'QueryResults',
}: PowerBIExportDialogProps) {
  const [tableName, setTableName] = useState(suggestedTableName);
  const [reportName, setReportName] = useState('');
  const { exportToPowerBI, isExporting, result, error } = usePowerBIExport();

  const handleExport = () => {
    exportToPowerBI({
      query,
      tableName,
      reportName: reportName || undefined,
    });
  };

  return (
    <Dialog.Root open={open} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg">
          <Dialog.Title className="flex items-center gap-2 text-lg font-semibold">
            <FileType className="h-5 w-5" />
            Export to Power BI
          </Dialog.Title>

          {!result ? (
            <>
              <div className="mt-4 space-y-4">
                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Table Name
                  </label>
                  <Input
                    value={tableName}
                    onChange={(e) => setTableName(e.target.value)}
                    placeholder="e.g., SalesData"
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Name for the data table in Power BI
                  </p>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium">
                    Report Name (optional)
                  </label>
                  <Input
                    value={reportName}
                    onChange={(e) => setReportName(e.target.value)}
                    placeholder="e.g., Monthly Analytics"
                  />
                </div>

                <div className="rounded-md bg-muted p-3">
                  <p className="text-sm text-muted-foreground">
                    This will create a .pbix file that you can open in Power BI Desktop.
                    The file will contain your query results as a data table.
                  </p>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={handleExport} disabled={!tableName || isExporting}>
                  {isExporting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create PBIX'
                  )}
                </Button>
              </div>
            </>
          ) : (
            <div className="mt-4">
              {result.status === 'success' ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-500">
                    <CheckCircle className="h-5 w-5" />
                    <span>Power BI file created successfully!</span>
                  </div>
                  <div className="rounded-md bg-muted p-3">
                    <p className="text-sm font-medium">File location:</p>
                    <code className="mt-1 block text-xs">{result.file_path}</code>
                  </div>
                  <Button onClick={onClose} className="w-full">
                    Done
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-red-500">
                    <AlertCircle className="h-5 w-5" />
                    <span>Export failed</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{result.message}</p>
                  <Button variant="outline" onClick={onClose}>
                    Close
                  </Button>
                </div>
              )}
            </div>
          )}

          <Dialog.Close asChild>
            <button
              className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

#### 5.3 Backend Power BI Export Endpoint

```python
# src/api/routes/agent.py (add to existing file)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from src.api.deps import get_mcp_manager

router = APIRouter()
logger = structlog.get_logger()


class PowerBIExportRequest(BaseModel):
    query: str
    table_name: str
    report_name: str | None = None


class PowerBIExportResponse(BaseModel):
    status: str
    file_path: str | None = None
    message: str | None = None


@router.post("/powerbi-export", response_model=PowerBIExportResponse)
async def export_to_powerbi(request: PowerBIExportRequest):
    """Export query results to Power BI PBIX file."""
    try:
        mcp_manager = get_mcp_manager()
        
        # Check if Power BI MCP is enabled
        powerbi_server = mcp_manager.get_mcp_server("powerbi-modeling")
        if not powerbi_server:
            return PowerBIExportResponse(
                status="error",
                message="Power BI MCP server is not enabled. Please configure it in MCP settings.",
            )
        
        # Use agent to execute Power BI MCP tools
        from pydantic_ai import Agent
        
        agent = Agent(
            model="ollama:qwen3:30b",
            mcp_servers=[powerbi_server],
        )
        
        # Create the PBIX file using MCP
        async with agent:
            result = await agent.run(f"""
                Create a Power BI report with the following:
                - Table name: {request.table_name}
                - Report name: {request.report_name or request.table_name}
                - Execute this SQL query and use the results: {request.query}
                
                Return the file path where the PBIX was saved.
            """)
        
        # Parse the result to get file path
        # (This depends on Power BI MCP response format)
        file_path = str(result.data)  # Adjust based on actual response
        
        return PowerBIExportResponse(
            status="success",
            file_path=file_path,
        )
        
    except Exception as e:
        logger.error("powerbi_export_error", error=str(e))
        return PowerBIExportResponse(
            status="error",
            message=str(e),
        )
```

---

### Step 6: Chat Export Integration

```typescript
// frontend/src/pages/ChatPage.tsx (add to existing file)
import { ExportMenu } from '@/components/export/ExportMenu';
import { exportChatToMarkdown, exportChatToPdf } from '@/lib/exports/chatExport';

// In the ChatPage component, add export functionality:
function ChatPageHeader({ conversation, messages }) {
  return (
    <div className="flex items-center justify-between border-b p-4">
      <h2 className="font-semibold">
        {conversation?.title || 'New Conversation'}
      </h2>
      
      <div className="flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => exportChatToMarkdown(conversation, messages)}
        >
          Export Markdown
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => exportChatToPdf(conversation, messages)}
        >
          Export PDF
        </Button>
      </div>
    </div>
  );
}
```

---

### Step 7: Query Result Export

```typescript
// frontend/src/components/chat/QueryResultPanel.tsx
import { useRef, useState } from 'react';
import { ExportMenu } from '@/components/export/ExportMenu';
import { ChartRenderer } from '@/components/charts/ChartRenderer';
import { PowerBIExportDialog } from '@/components/dialogs/PowerBIExportDialog';
import { suggestChartType } from '@/lib/chartSuggestion';

interface QueryResultPanelProps {
  data: Record<string, unknown>[];
  query: string;
  title?: string;
}

export function QueryResultPanel({ data, query, title }: QueryResultPanelProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [showPowerBIDialog, setShowPowerBIDialog] = useState(false);
  
  const suggestion = suggestChartType(data);

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between border-b p-3">
        <h3 className="font-medium">{title || 'Query Results'}</h3>
        <div className="flex gap-2">
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
      
      <div ref={chartRef} className="h-80 p-4">
        <ChartRenderer data={data} autoSuggest />
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
```

---

## File Structure After Phase 2.4

```
frontend/src/
├── lib/
│   └── exports/
│       ├── pngExport.ts
│       ├── pdfExport.ts
│       ├── csvExport.ts
│       ├── excelExport.ts
│       ├── jsonExport.ts
│       ├── chatExport.ts
│       └── index.ts
├── components/
│   ├── export/
│   │   └── ExportMenu.tsx
│   └── dialogs/
│       └── PowerBIExportDialog.tsx
└── hooks/
    └── usePowerBIExport.ts
```

---

## Validation Checkpoints

1. **PNG export works:**
   - Click Export → PNG on chart
   - File downloads with chart image

2. **PDF export works:**
   - Export dashboard to PDF
   - All widgets visible
   - Proper pagination for long content

3. **CSV/Excel export:**
   - Query results export correctly
   - Column headers present
   - Data formatting preserved

4. **Dashboard JSON:**
   - Export dashboard config
   - Import creates new dashboard
   - All widgets restored

5. **Chat export:**
   - Markdown export readable
   - PDF properly formatted

6. **Power BI integration:**
   - Dialog opens
   - (If MCP configured) PBIX file created

---

## Notes for Implementation

- Use `html2canvas` with `scale: 2` for high-resolution exports
- PDF pagination handles content longer than one page
- Excel auto-calculates column widths
- Power BI MCP requires separate installation
- File downloads use `file-saver` for cross-browser support
