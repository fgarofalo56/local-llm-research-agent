import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { Document } from '@/types';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Upload, Trash2, FileText, Loader2 } from 'lucide-react';
import { useRef } from 'react';
import { formatDistanceToNow } from 'date-fns';

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.get<DocumentsResponse>('/documents'),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.upload<Document>('/documents', file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const statusColors = {
    pending: 'text-yellow-500',
    processing: 'text-blue-500',
    completed: 'text-green-500',
    failed: 'text-red-500',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Documents</h1>
        <Button onClick={() => fileInputRef.current?.click()}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Document
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.pptx,.xlsx,.html,.md,.txt"
          onChange={handleFileSelect}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.documents.map((doc) => (
            <Card key={doc.id}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  <FileText className="mr-2 inline h-4 w-4" />
                  {doc.original_filename}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => deleteMutation.mutate(doc.id)}
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm text-muted-foreground">
                  <p>Size: {(doc.file_size / 1024).toFixed(1)} KB</p>
                  <p>Chunks: {doc.chunk_count || '-'}</p>
                  <p className={statusColors[doc.processing_status]}>
                    Status: {doc.processing_status}
                  </p>
                  <p>Added {formatDistanceToNow(new Date(doc.created_at))} ago</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
