import { useState, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

type SortField = 'original_filename' | 'created_at' | 'processing_status' | 'file_size';
type SortDirection = 'asc' | 'desc';

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
      api.post(`/documents/${documentId}/tags`, { tags }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
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

  // Fetch documents with auto-refresh for processing status
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<DocumentsResponse>('/documents'),
    refetchInterval: (query) => {
      // Auto-refresh every 3 seconds if any document is processing
      const hasProcessing = query.state.data?.documents.some(
        (doc) => doc.processing_status === 'processing' || doc.processing_status === 'pending'
      );
      return hasProcessing ? 3000 : false;
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.upload<Document>('/documents', file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setDeleteTarget(null);
    },
  });

  // Reprocess mutation
  const reprocessMutation = useMutation({
    mutationFn: (id: number) => api.post(`/documents/${id}/reprocess`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

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

    // Tag filter (placeholder - tags not yet implemented in backend)
    // if (tagFilter) {
    //   docs = docs.filter((doc) => doc.tags?.includes(tagFilter));
    // }

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
  }, [data?.documents, searchQuery, statusFilter, sortField, sortDirection]);

  // Get unique tags from all documents (placeholder)
  const allTags = useMemo(() => {
    // In future, aggregate tags from all documents
    return ['research', 'ml', 'data', 'report'];
  }, []);

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Documents</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={() => fileInputRef.current?.click()}>
            {uploadMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            Upload Document
          </Button>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.pptx,.xlsx,.html,.md,.txt"
          onChange={handleFileSelect}
        />
      </div>

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
                    <button
                      onClick={() => setTagEditTarget(doc)}
                      className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
                    >
                      <Tag className="h-3 w-3" />
                      Add tags
                    </button>
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
                          onClick={() => reprocessMutation.mutate(doc.id)}
                          disabled={reprocessMutation.isPending}
                        >
                          {reprocessMutation.isPending ? (
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
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
          isDeleting={deleteMutation.isPending}
        />
      )}

      {/* Tag editor dialog */}
      {tagEditTarget && (
        <TagEditor
          documentId={tagEditTarget.id}
          currentTags={[]}
          onClose={() => setTagEditTarget(null)}
        />
      )}
    </div>
  );
}
