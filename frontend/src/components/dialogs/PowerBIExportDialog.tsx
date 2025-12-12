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
  // Use key to remount component when dialog opens, resetting all state
  // This is handled by parent component
  const [tableName, setTableName] = useState(suggestedTableName);
  const [reportName, setReportName] = useState('');
  const { exportToPowerBI, isExporting, result, error, reset } = usePowerBIExport();

  const handleExport = () => {
    exportToPowerBI({
      query,
      tableName,
      reportName: reportName || undefined,
    });
  };

  const handleClose = () => {
    // Reset state for next open
    setTableName(suggestedTableName);
    setReportName('');
    reset();
    onClose();
  };

  return (
    <Dialog.Root open={open} onOpenChange={(isOpen) => !isOpen && handleClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <Dialog.Content className="fixed left-1/2 top-1/2 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-lg z-50">
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

                {error && (
                  <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                    Failed to export: {(error as Error).message}
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end gap-2">
                <Button variant="outline" onClick={handleClose}>
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
                    <code className="mt-1 block text-xs break-all">{result.file_path}</code>
                  </div>
                  <Button onClick={handleClose} className="w-full">
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
                  <Button variant="outline" onClick={handleClose}>
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
              onClick={handleClose}
            >
              <X className="h-4 w-4" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
