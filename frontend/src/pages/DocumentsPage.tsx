import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { Document } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import {
  Upload,
  Trash2,
  FileText,
  Loader2,
  RefreshCw,
  Search,
  Tag,
  X,
  ChevronUp,
  ChevronDown,
  AlertCircle,
  CheckCircle,
  Clock,
  Cog,
  XCircle,
  FileUp,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

type SortField = 'original_filename' | 'created_at' | 'processing_status' | 'file_size';
type SortDirection = 'asc' | 'desc';

// Upload status tracking
type UploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

interface UploadState {
  status: UploadStatus;
  progress: number; // 0-100 for upload, then tracks processing
  fileName: string;
  fileSize: number;
  documentId: number | null;
  error: string | null;
  startedAt: number;
}

// Status icon component
function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'processing':
      return <Cog className="h-4 w-4 text-blue-500 animate-spin" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    default:
      return <Clock className="h-4 w-4 text-yellow-500" />;
  }
}

// Tag badge component
function TagBadge({ tag, onRemove }: { tag: string; onRemove?: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
      {tag}
      {onRemove && (
        <button onClick={onRemove} className="hover:text-destructive">
          <X className="h-3 w-3" />
        </button>
      )}
    </span>
  );
}

// Delete confirmation dialog
function DeleteDialog({
  document,
  onConfirm,
  onCancel,
  isDeleting,
}: {
  document: Document;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-96">
        <CardHeader>
          <CardTitle className="text-destructive">Delete Document</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>Are you sure you want to delete "{document.original_filename}"?</p>
          <p className="text-sm text-muted-foreground">
            This will permanently remove the document and its embeddings from the vector store.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onCancel} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={onConfirm} disabled={isDeleting}>
              {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Progress bar component
function ProgressBar({ percent, variant = 'default' }: { percent: number; variant?: 'default' | 'success' | 'error' }) {
  const colorClass = variant === 'success'
    ? 'bg-green-500'
    : variant === 'error'
    ? 'bg-red-500'
    : 'bg-primary';

  return (
    <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
      <div
        className={`h-full transition-all duration-300 ${colorClass}`}
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}

// Upload progress card component
function UploadProgressCard({
  uploads,
  onDismiss,
  onDismissAll,
}: {
  uploads: UploadState[];
  onDismiss: (fileName: string) => void;
  onDismissAll: () => void;
}) {
  // Track current time for elapsed time display - update every second when there are active uploads
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const hasActive = uploads.some(u => u.status === 'uploading' || u.status === 'processing');
    if (!hasActive) return;

    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => clearInterval(interval);
  }, [uploads]);

  if (uploads.length === 0) return null;

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getElapsedTime = (startedAt: number) => {
    const elapsed = Math.floor((now - startedAt) / 1000);
    if (elapsed < 60) return `${elapsed}s`;
    return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
  };

  const getStatusLabel = (upload: UploadState) => {
    switch (upload.status) {
      case 'uploading':
        return `Uploading... ${upload.progress}%`;
      case 'processing':
        return 'Processing document...';
      case 'completed':
        return 'Completed';
      case 'failed':
        return upload.error || 'Failed';
      default:
        return 'Waiting...';
    }
  };

  const getStatusIcon = (status: UploadStatus) => {
    switch (status) {
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
  };

  const activeUploads = uploads.filter(u => u.status === 'uploading' || u.status === 'processing');
  const completedUploads = uploads.filter(u => u.status === 'completed' || u.status === 'failed');

  return (
    <Card className="mb-6 border-primary/20 shadow-lg">
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Upload Progress
            {activeUploads.length > 0 && (
              <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                {activeUploads.length} active
              </span>
            )}
          </CardTitle>
          {completedUploads.length > 0 && (
            <Button variant="ghost" size="sm" onClick={onDismissAll} className="text-xs">
              Clear completed
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3 py-2">
        {uploads.map((upload) => (
          <div
            key={upload.fileName + upload.startedAt}
            className={`rounded-lg border p-3 ${
              upload.status === 'failed'
                ? 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30'
                : upload.status === 'completed'
                ? 'border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/30'
                : 'border-border bg-muted/30'
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                {getStatusIcon(upload.status)}
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm truncate">{upload.fileName}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-2">
                    <span>{formatFileSize(upload.fileSize)}</span>
                    <span>•</span>
                    <span>{getElapsedTime(upload.startedAt)}</span>
                    {upload.documentId && (
                      <>
                        <span>•</span>
                        <span>ID: {upload.documentId}</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
              {(upload.status === 'completed' || upload.status === 'failed') && (
                <button
                  onClick={() => onDismiss(upload.fileName)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Progress bar for uploading state */}
            {upload.status === 'uploading' && (
              <div className="mt-2">
                <ProgressBar percent={upload.progress} />
              </div>
            )}

            {/* Indeterminate progress for processing state */}
            {upload.status === 'processing' && (
              <div className="mt-2">
                <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                  <div className="h-full w-1/3 bg-primary animate-[shimmer_1.5s_ease-in-out_infinite] rounded-full" />
                </div>
              </div>
            )}

            {/* Status label */}
            <p className={`text-xs mt-2 ${
              upload.status === 'failed' ? 'text-red-600 dark:text-red-400' :
              upload.status === 'completed' ? 'text-green-600 dark:text-green-400' :
              'text-muted-foreground'
            }`}>
              {getStatusLabel(upload)}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Tag editor component
function TagEditor({
  documentId,
  currentTags,
  onClose,
}: {
  documentId: number;
  currentTags: string[];
  onClose: () => void;
}) {
  const [tags, setTags] = useState<string[]>(currentTags);
  const [newTag, setNewTag] = useState('');
  const queryClient = useQueryClient();

  const updateTagsMutation = useMutation({
    mutationFn: (tags: string[]) =>
      api.patch(`/documents/${documentId}/tags`, { tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['all-tags'] });
      onClose();
    },
  });

  const addTag = () => {
    const trimmed = newTag.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter((t) => t !== tag));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="w-96">
        <CardHeader>
          <CardTitle>Edit Tags</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <TagBadge key={tag} tag={tag} onRemove={() => removeTag(tag)} />
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add tag..."
              onKeyDown={(e) => e.key === 'Enter' && addTag()}
            />
            <Button variant="outline" onClick={addTag}>
              Add
            </Button>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={() => updateTagsMutation.mutate(tags)}>
              {updateTagsMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tagFilter, setTagFilter] = useState<string>('');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [deleteTarget, setDeleteTarget] = useState<Document | null>(null);
  const [tagEditTarget, setTagEditTarget] = useState<Document | null>(null);

  // Upload tracking state
  const [uploads, setUploads] = useState<UploadState[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Fetch documents with auto-refresh for processing status
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<DocumentsResponse>('/documents'),
    refetchInterval: (query) => {
      // Auto-refresh every 2 seconds if any document is processing or we have active uploads
      const hasProcessing = query.state.data?.documents.some(
        (doc) => doc.processing_status === 'processing' || doc.processing_status === 'pending'
      );
      const hasActiveUploads = uploads.some(u => u.status === 'uploading' || u.status === 'processing');
      return (hasProcessing || hasActiveUploads) ? 2000 : false;
    },
  });

  // Track processing status changes for uploaded documents
  useEffect(() => {
    if (!data?.documents) return;

    setUploads(prev => prev.map(upload => {
      // Skip if not in processing state or no document ID
      if (upload.status !== 'processing' || !upload.documentId) return upload;

      // Find the document in the list
      const doc = data.documents.find(d => d.id === upload.documentId);
      if (!doc) return upload;

      // Update status based on document processing status
      if (doc.processing_status === 'completed') {
        return { ...upload, status: 'completed' as UploadStatus };
      } else if (doc.processing_status === 'failed') {
        return {
          ...upload,
          status: 'failed' as UploadStatus,
          error: doc.error_message || 'Processing failed'
        };
      }

      return upload;
    }));
  }, [data?.documents]);

  // Fetch all unique tags
  const { data: allTagsData } = useQuery({
    queryKey: ['all-tags'],
    queryFn: () => api.get<{ tags: string[]; total: number }>('/documents/tags/all'),
  });

  // Delete mutation
  const deleteMutation = useCallback(async (id: number) => {
    try {
      await api.delete(`/documents/${id}`);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setDeleteTarget(null);
    } catch (error) {
      console.error('Delete failed:', error);
    }
  }, [queryClient]);

  // Reprocess mutation
  const reprocessMutation = useCallback(async (id: number) => {
    try {
      await api.post(`/documents/${id}/reprocess`);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (error) {
      console.error('Reprocess failed:', error);
    }
  }, [queryClient]);

  // Track delete/reprocess loading states
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [reprocessingId, setReprocessingId] = useState<number | null>(null);

  const handleDelete = async (id: number) => {
    setDeletingId(id);
    await deleteMutation(id);
    setDeletingId(null);
  };

  const handleReprocess = async (id: number) => {
    setReprocessingId(id);
    await reprocessMutation(id);
    setReprocessingId(null);
  };

  // Upload with progress tracking
  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const uploadState: UploadState = {
      status: 'uploading',
      progress: 0,
      fileName: file.name,
      fileSize: file.size,
      documentId: null,
      error: null,
      startedAt: Date.now(),
    };

    // Add to uploads list
    setUploads(prev => [uploadState, ...prev]);
    setIsUploading(true);

    try {
      // Upload with progress tracking
      const result = await api.uploadWithProgress<Document>(
        '/documents',
        file,
        (percent) => {
          setUploads(prev => prev.map(u =>
            u.fileName === file.name && u.startedAt === uploadState.startedAt
              ? { ...u, progress: percent }
              : u
          ));
        }
      );

      // Update to processing state with document ID
      setUploads(prev => prev.map(u =>
        u.fileName === file.name && u.startedAt === uploadState.startedAt
          ? {
              ...u,
              status: 'processing' as UploadStatus,
              progress: 100,
              documentId: result.id,
            }
          : u
      ));

      // Refresh document list
      queryClient.invalidateQueries({ queryKey: ['documents'] });

    } catch (error) {
      // Update to failed state
      const errorMessage = (error as { detail?: string })?.detail || 'Upload failed';
      setUploads(prev => prev.map(u =>
        u.fileName === file.name && u.startedAt === uploadState.startedAt
          ? { ...u, status: 'failed' as UploadStatus, error: errorMessage }
          : u
      ));
    } finally {
      setIsUploading(false);
    }
  }, [queryClient]);

  // Dismiss individual upload
  const dismissUpload = useCallback((fileName: string) => {
    setUploads(prev => prev.filter(u => u.fileName !== fileName));
  }, []);

  // Dismiss all completed/failed uploads
  const dismissAllCompleted = useCallback(() => {
    setUploads(prev => prev.filter(u => u.status === 'uploading' || u.status === 'processing'));
  }, []);

  // Sort handler
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Filter and sort documents
  const filteredDocuments = useMemo(() => {
    if (!data?.documents) return [];

    let docs = [...data.documents];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      docs = docs.filter((doc) =>
        doc.original_filename.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      docs = docs.filter((doc) => doc.processing_status === statusFilter);
    }

    // Tag filter
    if (tagFilter) {
      docs = docs.filter((doc) =>
        doc.tags?.some((tag) => tag.toLowerCase() === tagFilter.toLowerCase())
      );
    }

    // Sort
    docs.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'original_filename':
          cmp = a.original_filename.localeCompare(b.original_filename);
          break;
        case 'created_at':
          cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'processing_status':
          cmp = a.processing_status.localeCompare(b.processing_status);
          break;
        case 'file_size':
          cmp = a.file_size - b.file_size;
          break;
      }
      return sortDirection === 'asc' ? cmp : -cmp;
    });

    return docs;
  }, [data?.documents, searchQuery, statusFilter, tagFilter, sortField, sortDirection]);

  // Get unique tags from API or fallback to extracting from documents
  const allTags = useMemo(() => {
    if (allTagsData?.tags && allTagsData.tags.length > 0) {
      return allTagsData.tags;
    }
    // Fallback: extract tags from loaded documents
    if (!data?.documents) return [];
    const tagSet = new Set<string>();
    data.documents.forEach((doc) => {
      doc.tags?.forEach((tag) => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [allTagsData, data?.documents]);

  // Sort column header
  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center gap-1 font-medium hover:text-primary"
    >
      {label}
      {sortField === field &&
        (sortDirection === 'asc' ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        ))}
    </button>
  );

  // Handle upload button click
  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = ''; // Reset to allow re-selecting same file
      fileInputRef.current.click();
    }
  };

  return (
    <div className="space-y-6">
      {/* Hidden file input - placed at root level for better accessibility */}
      <input
        ref={fileInputRef}
        type="file"
        className="sr-only"
        accept=".pdf,.docx,.pptx,.xlsx,.html,.md,.txt"
        onChange={handleFileSelect}
        aria-label="Upload document"
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Documents</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button
            onClick={handleUploadClick}
            disabled={isUploading}
            type="button"
          >
            {isUploading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            Upload Document
          </Button>
        </div>
      </div>

      {/* Upload Progress Card */}
      <UploadProgressCard
        uploads={uploads}
        onDismiss={dismissUpload}
        onDismissAll={dismissAllCompleted}
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={tagFilter}
          onChange={(e) => setTagFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">All Tags</option>
          {allTags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>

      {/* Document count */}
      <p className="text-sm text-muted-foreground">
        {filteredDocuments.length} of {data?.total || 0} documents
      </p>

      {/* Loading state */}
      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : filteredDocuments.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-lg font-medium">No documents found</p>
            <p className="text-muted-foreground">
              {data?.total === 0
                ? 'Upload your first document to get started'
                : 'Try adjusting your filters'}
            </p>
          </CardContent>
        </Card>
      ) : (
        /* Document table */
        <div className="rounded-lg border">
          <table className="w-full">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left">
                  <SortHeader field="original_filename" label="Name" />
                </th>
                <th className="px-4 py-3 text-left">
                  <SortHeader field="processing_status" label="Status" />
                </th>
                <th className="px-4 py-3 text-left">Tags</th>
                <th className="px-4 py-3 text-left">
                  <SortHeader field="file_size" label="Size" />
                </th>
                <th className="px-4 py-3 text-left">Chunks</th>
                <th className="px-4 py-3 text-left">
                  <SortHeader field="created_at" label="Uploaded" />
                </th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredDocuments.map((doc) => (
                <tr key={doc.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{doc.original_filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <StatusIcon status={doc.processing_status} />
                      <span className="capitalize">{doc.processing_status}</span>
                    </div>
                    {doc.processing_status === 'failed' && doc.error_message && (
                      <p className="mt-1 text-xs text-destructive truncate max-w-[200px]">
                        {doc.error_message}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {doc.tags && doc.tags.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {doc.tags.slice(0, 3).map((tag) => (
                            <TagBadge key={tag} tag={tag} />
                          ))}
                          {doc.tags.length > 3 && (
                            <span className="text-xs text-muted-foreground">
                              +{doc.tags.length - 3}
                            </span>
                          )}
                        </div>
                      ) : null}
                      <button
                        onClick={() => setTagEditTarget(doc)}
                        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
                        title={doc.tags?.length ? 'Edit tags' : 'Add tags'}
                      >
                        <Tag className="h-3 w-3" />
                        {!doc.tags?.length && 'Add'}
                      </button>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {(doc.file_size / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {doc.chunk_count || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDistanceToNow(new Date(doc.created_at))} ago
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {doc.processing_status === 'failed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleReprocess(doc.id)}
                          disabled={reprocessingId === doc.id}
                        >
                          {reprocessingId === doc.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(doc)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete confirmation dialog */}
      {deleteTarget && (
        <DeleteDialog
          document={deleteTarget}
          onConfirm={() => handleDelete(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
          isDeleting={deletingId === deleteTarget.id}
        />
      )}

      {/* Tag editor dialog */}
      {tagEditTarget && (
        <TagEditor
          documentId={tagEditTarget.id}
          currentTags={tagEditTarget.tags || []}
          onClose={() => setTagEditTarget(null)}
        />
      )}
    </div>
  );
}
