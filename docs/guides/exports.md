# Exports Guide

> Comprehensive documentation for export features in the Local LLM Research Agent

---

## Overview

The export system provides multiple ways to share and save data from the application:

| Format | Extension | Use Case |
|--------|-----------|----------|
| PNG | `.png` | High-resolution chart images |
| PDF | `.pdf` | Reports with titles and timestamps |
| CSV | `.csv` | Standard data exchange format |
| Excel | `.xlsx` | Spreadsheet analysis |
| JSON | `.json` | Dashboard configuration backup |
| Markdown | `.md` | Documentation and chat logs |

---

## Chart Exports

### PNG Export

Export charts as high-resolution PNG images.

**Features:**
- 2x scale for high resolution
- Transparent background support
- Works with all chart types

**Usage (UI):**
1. Hover over any chart
2. Click the export menu (download icon)
3. Select "PNG"

**Programmatic Usage:**
```typescript
import { exportToPng } from '@/lib/exports/pngExport';

// Export chart element to PNG
const chartElement = document.getElementById('my-chart');
await exportToPng(chartElement, 'sales-chart.png');
```

### PDF Export

Export charts or full dashboards as PDF documents.

**Features:**
- Multi-page support for large dashboards
- Includes title and timestamp
- Configurable page orientation

**Usage (UI):**
1. Hover over any chart
2. Click the export menu
3. Select "PDF"

**Programmatic Usage:**
```typescript
import { exportToPdf, exportDashboardToPdf } from '@/lib/exports/pdfExport';

// Export single chart
await exportToPdf(chartElement, 'chart.pdf', {
  title: 'Monthly Sales Report'
});

// Export full dashboard
await exportDashboardToPdf(dashboardElement, 'My Dashboard');
```

---

## Data Exports

### CSV Export

Export query results as comma-separated values.

**Features:**
- Proper escaping of special characters
- Headers included
- Compatible with Excel, Google Sheets, etc.

**Usage (UI):**
1. View query results in chart/table
2. Click export menu
3. Select "CSV"

**Programmatic Usage:**
```typescript
import { exportToCsv } from '@/lib/exports/csvExport';

const data = [
  { name: 'Alice', score: 95 },
  { name: 'Bob', score: 87 }
];

exportToCsv(data, 'results.csv');
```

### Excel Export

Export data as Excel spreadsheets with formatting.

**Features:**
- Auto-calculated column widths
- Multi-sheet support
- Proper data type handling

**Usage (UI):**
1. View query results
2. Click export menu
3. Select "Excel"

**Programmatic Usage:**
```typescript
import { exportToExcel, exportMultipleSheetsToExcel } from '@/lib/exports/excelExport';

// Single sheet
exportToExcel(data, 'report.xlsx', {
  sheetName: 'Sales Data'
});

// Multiple sheets
exportMultipleSheetsToExcel([
  { name: 'Q1', data: q1Data },
  { name: 'Q2', data: q2Data }
], 'quarterly-report.xlsx');
```

---

## Dashboard Exports

### JSON Configuration

Export and import dashboard configurations for backup or sharing.

**Export Features:**
- Version information
- Export timestamp
- Complete dashboard settings
- All widget configurations

**Usage (UI):**

**Export:**
1. Navigate to `/dashboards`
2. Select a dashboard
3. Click "Export JSON"

**Import:**
1. Navigate to `/dashboards`
2. Click "Import"
3. Select a `.json` file

**Programmatic Usage:**
```typescript
import { exportDashboardToJson, importDashboardFromJson } from '@/lib/exports/jsonExport';

// Export
exportDashboardToJson(dashboard, widgets);

// Import
const file = /* File from input */;
const config = await importDashboardFromJson(file);
// config.dashboard - Dashboard settings
// config.widgets - Widget array
```

**JSON Structure:**
```json
{
  "version": "1.0",
  "exportedAt": "2025-12-11T10:30:00.000Z",
  "dashboard": {
    "id": 1,
    "name": "Sales Dashboard",
    "description": "Monthly sales metrics"
  },
  "widgets": [
    {
      "id": 1,
      "title": "Revenue",
      "chartType": "bar",
      "query": "SELECT ...",
      "position": { "x": 0, "y": 0, "w": 6, "h": 4 }
    }
  ]
}
```

---

## Chat Exports

### Markdown Export

Export conversations as Markdown for documentation.

**Features:**
- Formatted message headers
- Timestamps included
- User/Assistant role indicators
- Code block preservation

**Usage (UI):**
1. Open a conversation in `/chat`
2. Click "Export MD"

**Programmatic Usage:**
```typescript
import { exportChatToMarkdown } from '@/lib/exports/chatExport';

exportChatToMarkdown(conversation, messages);
```

**Output Format:**
```markdown
# Sales Analysis Discussion

*Conversation ID: 123*
*Exported: 12/11/2025, 10:30:00 AM*

---

## User (10:25:00 AM)

Show me the top 5 products by revenue

---

## Assistant (10:25:05 AM)

Based on the query results...
```

### PDF Export

Export conversations as PDF documents.

**Features:**
- Professional formatting
- Includes all messages
- Timestamps and metadata

**Usage (UI):**
1. Open a conversation in `/chat`
2. Click "Export PDF"

**Programmatic Usage:**
```typescript
import { exportChatToPdf } from '@/lib/exports/chatExport';

exportChatToPdf(conversation, messages);
```

---

## Power BI Integration

### Power BI Export Dialog

Export query results directly to Power BI Desktop format.

**Features:**
- Custom table name
- Optional report name
- Creates `.pbix` files

**Usage (UI):**
1. View query results
2. Click export menu
3. Select "Power BI"
4. Configure table name and report name
5. Click "Create PBIX"

**API Endpoint:**
```http
POST /api/agent/powerbi-export
Content-Type: application/json

{
  "query": "SELECT * FROM Sales",
  "table_name": "SalesData",
  "report_name": "Monthly Sales Report"
}
```

**Response:**
```json
{
  "status": "success",
  "file_path": "/path/to/export.pbix",
  "message": "Power BI file created successfully"
}
```

---

## Export Menu Component

The `ExportMenu` component provides a unified export interface.

### Props

| Prop | Type | Description |
|------|------|-------------|
| `elementRef` | `RefObject<HTMLElement>` | Reference to chart element for PNG/PDF |
| `data` | `Record<string, unknown>[]` | Data array for CSV/Excel |
| `filename` | `string` | Base filename without extension |
| `title` | `string` | Title for PDF exports |
| `showPowerBI` | `boolean` | Show Power BI option |
| `onPowerBIExport` | `() => void` | Handler for Power BI button |

### Usage

```tsx
import { ExportMenu } from '@/components/export/ExportMenu';

function Chart() {
  const chartRef = useRef<HTMLDivElement>(null);
  const data = [...];

  return (
    <div>
      <ExportMenu
        elementRef={chartRef}
        data={data}
        filename="sales-chart"
        title="Sales Analysis"
        showPowerBI={true}
        onPowerBIExport={() => setShowPBIDialog(true)}
      />
      <div ref={chartRef}>
        {/* Chart content */}
      </div>
    </div>
  );
}
```

---

## File Locations

Exported files are downloaded to the user's default downloads folder, except for Power BI exports which may be saved to a configured server location.

---

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| PNG Export | Full | Full | Full | Full |
| PDF Export | Full | Full | Full | Full |
| CSV Export | Full | Full | Full | Full |
| Excel Export | Full | Full | Full | Full |
| Power BI | Full | Full | Full | Full |

---

## Troubleshooting

### PNG Export Issues

**Problem:** Black background instead of transparent
**Solution:** Ensure `backgroundColor: null` is set in html2canvas options

**Problem:** Low resolution image
**Solution:** The default scale is 2x. For higher resolution, modify `pngExport.ts`

### PDF Export Issues

**Problem:** Content cut off
**Solution:** Large dashboards are automatically paginated. Ensure the element fits within page dimensions.

### Excel Export Issues

**Problem:** Dates not formatted correctly
**Solution:** xlsx library handles dates as serial numbers. Format columns in Excel after export.

### Power BI Export Issues

**Problem:** File not creating
**Solution:** Check that the backend API is running and accessible. Verify the response in browser dev tools.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| html2canvas | 1.4.1 | Capture DOM as canvas for PNG |
| jspdf | 3.0.1 | PDF document generation |
| xlsx | 0.18.5 | Excel file creation |
| file-saver | 2.0.5 | Cross-browser file downloads |

---

*Last Updated: December 2025*
