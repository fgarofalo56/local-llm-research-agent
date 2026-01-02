# Specialized Components

Feature-specific components for advanced functionality including export, settings, Superset integration, uploads, and onboarding.

## Table of Contents

- [Export Components](#export-components)
  - [ExportMenu](#exportmenu)
- [Settings Components](#settings-components)
  - [ThemeSelector](#themeselector)
- [Superset Components](#superset-components)
  - [SupersetEmbed](#supersetembed)
- [Upload Components](#upload-components)
  - [GlobalUploadProgress](#globaluploadprogress)
- [Dialog Components](#dialog-components)
  - [PinToDashboardDialog](#pintodashboarddialog)
  - [PowerBIExportDialog](#powerbiexportdialog)
  - [KeyboardShortcutsDialog](#keyboardshortcutsdialog)
- [Onboarding Components](#onboarding-components)
  - [OnboardingWizard](#onboardingwizard)

---

## Export Components

### ExportMenu

Multi-format export dropdown menu for charts and data.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `elementRef` | `RefObject<HTMLElement>` | - | Element to export as image/PDF |
| `data` | `Record<string, unknown>[]` | - | Data to export as CSV/Excel |
| `filename` | `string` | `'export'` | Base filename for downloads |
| `title` | `string` | - | Title for PDF export |
| `onPowerBIExport` | `() => void` | - | Power BI export callback |
| `showPowerBI` | `boolean` | `false` | Show Power BI export option |

#### Usage Example

```tsx
import { useRef } from 'react';
import { ExportMenu } from '@/components/export/ExportMenu';

function ChartCard({ data }) {
  const chartRef = useRef<HTMLDivElement>(null);

  return (
    <div>
      <div className="flex justify-between">
        <h2>Sales Chart</h2>
        <ExportMenu
          elementRef={chartRef}
          data={data}
          filename="sales-report"
          title="Monthly Sales"
        />
      </div>
      <div ref={chartRef}>
        <BarChart data={data} />
      </div>
    </div>
  );
}
```

#### Export Formats

**Image Exports** (requires `elementRef`)
- **PNG** - Raster image using html2canvas
- **PDF** - Document with embedded image

**Data Exports** (requires `data`)
- **CSV** - Comma-separated values
- **Excel** - XLSX format with formatting

**Business Intelligence** (requires `onPowerBIExport`)
- **Power BI** - PBIX file generation

#### Export Functions

```typescript
// PNG Export
import { exportToPng } from '@/lib/exports/pngExport';
await exportToPng(element, 'filename.png');

// PDF Export
import { exportToPdf } from '@/lib/exports/pdfExport';
await exportToPdf(element, 'filename.pdf', { title: 'Report Title' });

// CSV Export
import { exportToCsv } from '@/lib/exports/csvExport';
exportToCsv(data, 'filename.csv');

// Excel Export
import { exportToExcel } from '@/lib/exports/excelExport';
exportToExcel(data, 'filename.xlsx');
```

#### Features

- **Loading State**: Shows spinner during export
- **Error Handling**: Catches and displays export errors
- **Flexible**: Enable only relevant export types
- **Accessible**: Keyboard navigable dropdown

#### Notes
- PNG/PDF exports require the element to be rendered
- Excel exports include basic formatting (headers, borders)
- CSV exports use UTF-8 encoding with BOM for Excel compatibility

---

## Settings Components

### ThemeSelector

Comprehensive theme selection with presets and custom themes.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `showCustomBuilder` | `boolean` | `false` | Show custom theme builder UI |

#### Usage Example

```tsx
import { ThemeSelector } from '@/components/settings/ThemeSelector';

function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1>Appearance Settings</h1>
      <ThemeSelector showCustomBuilder={true} />
    </div>
  );
}
```

#### Features

**Mode Selection**
- Light mode
- Dark mode
- System (follows OS preference)

**Theme Presets**
- Default Dark/Light
- High Contrast
- Colorblind-friendly
- Custom themes

**Preset Preview**
- Visual color swatches
- Background, primary, accent colors
- Name and description

**Custom Theme Builder** (optional)
- Create custom color schemes
- Save to local storage
- Delete custom themes

#### Theme Presets

```typescript
interface ThemePreset {
  id: string;
  name: string;
  description: string;
  isDark: boolean;
  colors: {
    background: string;
    foreground: string;
    primary: string;
    secondary: string;
    accent: string;
    muted: string;
    // ... more color tokens
  };
}
```

#### Available Presets

**Dark Themes**
- Default Dark
- High Contrast Dark
- Blue Dark
- Purple Dark

**Light Themes**
- Default Light
- High Contrast Light
- Blue Light
- Soft Light

#### Theme Application

```typescript
import { applyThemePreset, getThemePreset } from '@/lib/themes';

const preset = getThemePreset('default-dark');
applyThemePreset(preset);
```

#### Persistence

Themes persist to localStorage:

```typescript
// Save selected preset
localStorage.setItem('themePreset', preset.id);

// Save custom themes
localStorage.setItem('customThemes', JSON.stringify(customThemes));
```

#### Accessibility
- High contrast options
- Keyboard navigable
- ARIA labels on controls
- Color preview with accessible labels

---

## Superset Components

### SupersetEmbed

Embeds Apache Superset dashboards with guest token authentication.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `dashboardId` | `number` | Required | Superset dashboard ID |
| `title` | `string` | `'Superset Dashboard'` | Dashboard title |
| `height` | `string` | `'600px'` | iframe height |

#### Usage Example

```tsx
import { SupersetEmbed } from '@/components/superset/SupersetEmbed';

function SupersetPage() {
  return (
    <div>
      <h1>Analytics Dashboard</h1>
      <SupersetEmbed
        dashboardId={1}
        title="Sales Analytics"
        height="800px"
      />
    </div>
  );
}
```

#### Features

**Guest Token Authentication**
- Automatic token generation
- Secure embedding
- Token refresh on expiry

**Dashboard Controls**
- Refresh button
- Open in Superset (new tab)
- Full-screen toggle

**Loading States**
- Spinner while loading
- Error display with retry
- Skeleton placeholder

**Security**
- Sandboxed iframe
- Restricted permissions
- CORS handling

#### API Integration

```typescript
// Backend endpoint
GET /api/superset/embed/:dashboardId

Response: {
  embed_url: string,
  dashboard_id: string
}
```

#### Embed URL Format

```
http://superset:8088/superset/dashboard/1/embedded?guest_token=...
```

#### Error Handling

```tsx
if (error) {
  return (
    <div className="error-state">
      <AlertCircle />
      <p>Failed to load dashboard</p>
      <Button onClick={() => refetch()}>Retry</Button>
    </div>
  );
}
```

#### Notes
- Requires Superset backend configured
- Guest token expires after configured duration
- Embedded dashboards have limited interactivity

---

## Upload Components

### GlobalUploadProgress

Fixed position panel showing document upload progress across all pages.

#### Props

No props required. Uses Zustand upload store.

#### Usage Example

```tsx
import { GlobalUploadProgress } from '@/components/upload/GlobalUploadProgress';

function App() {
  return (
    <>
      <Router>
        <Routes />
      </Router>
      <GlobalUploadProgress />
    </>
  );
}
```

#### Features

**Upload Tracking**
- Multiple simultaneous uploads
- Progress percentage
- File size display
- Elapsed time

**Status Indicators**
- Pending (clock icon)
- Uploading (pulsing icon + progress bar)
- Processing (spinning icon)
- Completed (checkmark)
- Failed (X icon with error message)

**Interactive Controls**
- Expand/collapse panel
- Dismiss completed uploads
- Clear all completed button
- Individual upload dismissal

**Auto-Updates**
- Real-time progress updates
- Time elapsed counter (updates every second)
- Status changes reflected immediately

#### Upload States

```typescript
type UploadStatus = 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';

interface UploadItem {
  id: string;
  fileName: string;
  fileSize: number;
  status: UploadStatus;
  progress: number;
  error?: string;
  startedAt: number;
}
```

#### Upload Store

```typescript
interface UploadStore {
  uploads: UploadItem[];
  addUpload: (file: File) => string;
  updateUpload: (id: string, update: Partial<UploadItem>) => void;
  removeUpload: (id: string) => void;
  clearCompleted: () => void;
  activeCount: () => number;
  completedCount: () => number;
}
```

#### Usage in Upload Components

```tsx
import { useUploadStore } from '@/stores/uploadStore';

function FileUploader() {
  const { addUpload, updateUpload } = useUploadStore();

  const handleUpload = async (file: File) => {
    const uploadId = addUpload(file);

    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        updateUpload(uploadId, { progress: i, status: 'uploading' });
        await sleep(100);
      }

      // Processing
      updateUpload(uploadId, { status: 'processing' });
      await processFile(file);

      // Complete
      updateUpload(uploadId, { status: 'completed' });
    } catch (error) {
      updateUpload(uploadId, {
        status: 'failed',
        error: error.message,
      });
    }
  };

  return <input type="file" onChange={e => handleUpload(e.target.files[0])} />;
}
```

#### Visual Features

**Progress Bars**
- Determinate (uploading): Shows percentage
- Indeterminate (processing): Shimmer animation

**Color Coding**
- Pending/Uploading/Processing: Blue
- Completed: Green
- Failed: Red

**Formatting**
- File sizes: B, KB, MB
- Time: seconds or minutes:seconds
- Truncated long filenames

#### Positioning

```css
.upload-panel {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  width: 20rem;
  z-index: 50;
}
```

#### Accessibility
- ARIA live regions for status updates
- Keyboard dismissible
- Screen reader announcements
- Proper button labels

---

## Dialog Components

### PinToDashboardDialog

Modal for pinning query results to a dashboard.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `isOpen` | `boolean` | Dialog open state |
| `onClose` | `() => void` | Close callback |
| `query` | `string` | SQL query to pin |
| `data` | `Record<string, unknown>[]` | Query result data |

#### Usage Example

```tsx
import { PinToDashboardDialog } from '@/components/dialogs/PinToDashboardDialog';

function QueryResult({ query, data }) {
  const [showDialog, setShowDialog] = useState(false);

  return (
    <>
      <Button onClick={() => setShowDialog(true)}>
        <Pin className="mr-2" />
        Pin to Dashboard
      </Button>

      <PinToDashboardDialog
        isOpen={showDialog}
        onClose={() => setShowDialog(false)}
        query={query}
        data={data}
      />
    </>
  );
}
```

#### Features
- Select target dashboard
- Configure widget title
- Choose visualization type
- Set refresh interval
- Auto-position assignment

---

### PowerBIExportDialog

Modal for exporting data to Power BI format.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `isOpen` | `boolean` | Dialog open state |
| `onClose` | `() => void` | Close callback |
| `data` | `Record<string, unknown>[]` | Data to export |
| `metadata` | `object` | Query metadata |

#### Features
- PBIX file generation
- Data model configuration
- Relationship mapping
- Column type detection

---

### KeyboardShortcutsDialog

Reference guide for keyboard shortcuts.

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `isOpen` | `boolean` | Dialog open state |
| `onClose` | `() => void` | Close callback |

#### Features
- Categorized shortcuts
- Search/filter shortcuts
- Printable format
- Customizable bindings

#### Shortcut Categories

**Navigation**
- `Ctrl/Cmd + K` - Command palette
- `Ctrl/Cmd + B` - Toggle sidebar
- `Ctrl/Cmd + /` - Search

**Chat**
- `Ctrl/Cmd + N` - New conversation
- `Enter` - Send message
- `Shift + Enter` - New line

**Dashboard**
- `Ctrl/Cmd + E` - Toggle edit mode
- `Ctrl/Cmd + S` - Save layout
- `Delete` - Remove widget

---

## Onboarding Components

### OnboardingWizard

Multi-step wizard for user onboarding.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onComplete` | `() => void` | Required | Completion callback |
| `onSkip` | `() => void` | - | Skip callback |

#### Usage Example

```tsx
import { OnboardingWizard } from '@/components/onboarding/OnboardingWizard';

function App() {
  const [showOnboarding, setShowOnboarding] = useState(() =>
    !localStorage.getItem('onboarding-complete')
  );

  const handleComplete = () => {
    localStorage.setItem('onboarding-complete', 'true');
    setShowOnboarding(false);
  };

  return (
    <>
      {showOnboarding && (
        <OnboardingWizard
          onComplete={handleComplete}
          onSkip={handleComplete}
        />
      )}
      <App />
    </>
  );
}
```

#### Wizard Steps

1. **Welcome**
   - App overview
   - Key features
   - Get started button

2. **Database Connection**
   - MCP server configuration
   - Test connection
   - Sample queries

3. **Document Upload**
   - RAG pipeline introduction
   - Upload sample documents
   - Search demonstration

4. **Dashboard Creation**
   - Create first dashboard
   - Add widgets
   - Customize layout

5. **Completion**
   - Summary of setup
   - Next steps
   - Resource links

#### Features

**Progress Indicator**
- Step counter (1 of 5)
- Progress bar
- Step titles

**Navigation**
- Next/Previous buttons
- Skip option
- Direct step navigation (optional)

**Validation**
- Required field checking
- Connection testing
- Success/error feedback

**Persistence**
- Save progress to localStorage
- Resume incomplete onboarding
- Mark as completed

#### Onboarding Status Hook

```tsx
import { useOnboardingStatus } from '@/hooks/useOnboardingStatus';

function MyComponent() {
  const {
    isComplete,
    currentStep,
    completeStep,
    skipOnboarding,
  } = useOnboardingStatus();

  if (!isComplete) {
    return <OnboardingWizard />;
  }

  return <MainApp />;
}
```

#### Accessibility
- Keyboard navigation (Tab, Enter, Escape)
- ARIA labels for steps
- Screen reader announcements
- Focus management between steps

---

## Common Dialog Patterns

All dialog components use Radix UI Dialog:

```tsx
import * as Dialog from '@radix-ui/react-dialog';

function MyDialog({ isOpen, onClose }) {
  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <Dialog.Title>Title</Dialog.Title>
          <Dialog.Description>Description</Dialog.Description>

          {/* Content */}

          <Dialog.Close asChild>
            <button>Close</button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

### Dialog Accessibility

- **Focus Trap**: Focus contained within dialog
- **Escape Key**: Closes dialog
- **Overlay Click**: Closes dialog (optional)
- **ARIA**: Proper roles and labels
- **Return Focus**: Focus returns to trigger on close

---

## Testing

### Example Tests

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ExportMenu } from '@/components/export/ExportMenu';

describe('ExportMenu', () => {
  it('shows export options', async () => {
    render(<ExportMenu data={[]} filename="test" />);

    const button = screen.getByText(/export/i);
    fireEvent.click(button);

    expect(screen.getByText(/csv/i)).toBeInTheDocument();
    expect(screen.getByText(/excel/i)).toBeInTheDocument();
  });

  it('exports CSV on selection', async () => {
    const data = [{ id: 1, name: 'Test' }];
    const exportCsv = vi.fn();

    render(<ExportMenu data={data} />);

    fireEvent.click(screen.getByText(/export/i));
    fireEvent.click(screen.getByText(/csv/i));

    expect(exportCsv).toHaveBeenCalledWith(data, expect.any(String));
  });
});
```

---

## Related Documentation

- [UI Components](./ui.md) - Button, Card, Dialog primitives
- [Chart Components](./charts.md) - Chart export functionality
- [Dashboard Components](./dashboard.md) - Pin to dashboard feature
- [API Documentation](../../api/fastapi.md) - Backend endpoints
