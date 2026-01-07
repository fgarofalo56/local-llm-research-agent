/**
 * Documents Hook
 * Manages document fetching and upload status synchronization
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import { useUploadStore, useUploadProcessingSync } from '@/stores/uploadStore';
import type { Document } from '@/types';

interface DocumentsResponse {
  documents: Document[];
  total: number;
}

/**
 * Hook to fetch and manage documents with upload status sync
 */
export function useDocuments() {
  const { uploads } = useUploadStore();

  // Check if we have any processing uploads that need status updates
  const hasProcessingUploads = uploads.some(u => u.status === 'processing');

  const query = useQuery({
    queryKey: ['documents'],
    queryFn: () => api.getDocuments<DocumentsResponse>(),
    // Poll more frequently when there are processing uploads
    refetchInterval: hasProcessingUploads ? 2000 : false,
    staleTime: hasProcessingUploads ? 1000 : 30000,
  });

  // Sync upload status with document processing status
  useUploadProcessingSync(query.data?.documents);

  return {
    documents: query.data?.documents ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}

/**
 * Hook to fetch a single document by ID
 */
export function useDocument(id: number | null) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => api.getDocument<Document>(id!),
    enabled: id !== null,
  });
}

/**
 * Hook for RAG search
 */
export function useRAGSearch(query: string, topK = 5, hybridSearch = false) {
  return useQuery({
    queryKey: ['rag-search', query, topK, hybridSearch],
    queryFn: () => api.searchRAG<{ results: Array<{ content: string; score: number; metadata: Record<string, unknown> }> }>(
      query, topK, hybridSearch
    ),
    enabled: query.length > 0,
  });
}

/**
 * Hook to get vector store statistics
 */
export function useVectorStats() {
  return useQuery({
    queryKey: ['vector-stats'],
    queryFn: () => api.getVectorStats<{ total_documents: number; total_chunks: number; store_type: string }>(),
    staleTime: 60000, // Cache for 1 minute
  });
}
