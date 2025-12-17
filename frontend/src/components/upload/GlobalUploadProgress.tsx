/**
 * Global Upload Progress Component
 * Displays upload progress in a fixed position panel across all pages
 */

import { useState, useEffect } from 'react';
import {
  Upload,
  X,
  CheckCircle,
  XCircle,
  FileUp,
  Cog,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useUploadStore, type UploadItem, type UploadStatus } from '@/stores/uploadStore';
import { cn } from '@/lib/utils';

// Format file size for display
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Format elapsed time
function formatElapsedTime(startedAt: number, now: number): string {
  const elapsed = Math.floor((now - startedAt) / 1000);
  if (elapsed < 60) return `${elapsed}s`;
  return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
}

// Get status icon
function getStatusIcon(status: UploadStatus) {
  switch (status) {
    case 'pending':
      return <Clock className="h-4 w-4 text-muted-foreground" />;
    case 'uploading':
      return <FileUp className="h-4 w-4 text-blue-500 animate-pulse" />;
    case 'processing':
      return <Cog className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <XCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-muted-foreground" />;
  }
}

// Get status label
function getStatusLabel(upload: UploadItem): string {
  switch (upload.status) {
    case 'pending':
      return 'Waiting...';
    case 'uploading':
      return `Uploading... ${upload.progress}%`;
    case 'processing':
      return 'Processing document...';
    case 'completed':
      return 'Completed';
    case 'failed':
      return upload.error || 'Failed';
    default:
      return 'Unknown';
  }
}

// Single upload item row
function UploadItemRow({ upload, now, onDismiss }: {
  upload: UploadItem;
  now: number;
  onDismiss: () => void;
}) {
  const canDismiss = upload.status === 'completed' || upload.status === 'failed';

  return (
    <div
      className={cn(
        'rounded-lg border p-2 text-sm',
        upload.status === 'failed' && 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30',
        upload.status === 'completed' && 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/30',
        (upload.status === 'uploading' || upload.status === 'processing' || upload.status === 'pending') && 'border-border bg-muted/30'
      )}
    >
      <div className="flex items-start gap-2">
        {getStatusIcon(upload.status)}
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate text-xs">{upload.fileName}</p>
          <p className="text-xs text-muted-foreground flex items-center gap-1">
            <span>{formatFileSize(upload.fileSize)}</span>
            <span>•</span>
            <span>{formatElapsedTime(upload.startedAt, now)}</span>
          </p>
        </div>
        {canDismiss && (
          <button
            onClick={onDismiss}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>

      {/* Progress bar for uploading */}
      {upload.status === 'uploading' && (
        <div className="mt-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${upload.progress}%` }}
          />
        </div>
      )}

      {/* Indeterminate progress for processing */}
      {upload.status === 'processing' && (
        <div className="mt-2 h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div className="h-full w-1/3 bg-primary animate-[shimmer_1.5s_ease-in-out_infinite] rounded-full" />
        </div>
      )}

      {/* Status text */}
      <p className={cn(
        'text-xs mt-1',
        upload.status === 'failed' && 'text-red-600 dark:text-red-400',
        upload.status === 'completed' && 'text-green-600 dark:text-green-400',
        (upload.status !== 'failed' && upload.status !== 'completed') && 'text-muted-foreground'
      )}>
        {getStatusLabel(upload)}
      </p>
    </div>
  );
}

export function GlobalUploadProgress() {
  const { uploads, removeUpload, clearCompleted, activeCount, completedCount } = useUploadStore();
  const [isExpanded, setIsExpanded] = useState(true);
  const [now, setNow] = useState(() => Date.now());

  // Update time every second when there are active uploads
  useEffect(() => {
    const hasActive = uploads.some(u =>
      u.status === 'pending' || u.status === 'uploading' || u.status === 'processing'
    );

    if (!hasActive) return;

    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(interval);
  }, [uploads]);

  // Don't render if no uploads
  if (uploads.length === 0) return null;

  const active = activeCount();
  const completed = completedCount();

  return (
    <div className="fixed bottom-4 right-4 z-50 w-80 rounded-lg border bg-card shadow-lg">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between px-4 py-3 hover:bg-muted/50"
      >
        <div className="flex items-center gap-2">
          <Upload className="h-4 w-4 text-primary" />
          <span className="font-medium text-sm">Uploads</span>
          {active > 0 && (
            <span className="rounded-full bg-primary/20 px-2 py-0.5 text-xs text-primary">
              {active} active
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {completed > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearCompleted();
              }}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Clear
            </button>
          )}
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="max-h-64 overflow-y-auto border-t p-2 space-y-2">
          {uploads.map((upload) => (
            <UploadItemRow
              key={upload.id}
              upload={upload}
              now={now}
              onDismiss={() => removeUpload(upload.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
