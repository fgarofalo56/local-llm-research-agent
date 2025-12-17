/**
 * Global Upload Store
 * Manages document uploads across page navigation with multi-file support
 */

import { create } from 'zustand';
import { api } from '@/api/client';
import type { Document } from '@/types';

// Upload status tracking
export type UploadStatus = 'idle' | 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';

export interface UploadItem {
  id: string; // Unique ID for this upload
  status: UploadStatus;
  progress: number; // 0-100 for upload
  fileName: string;
  fileSize: number;
  file: File; // Keep reference to the file
  documentId: number | null;
  error: string | null;
  startedAt: number;
}

interface UploadState {
  // Upload queue
  uploads: UploadItem[];
  isProcessing: boolean; // Is any upload currently in progress

  // Actions
  addFiles: (files: File[]) => void;
  removeUpload: (id: string) => void;
  clearCompleted: () => void;
  clearAll: () => void;
  processQueue: () => Promise<void>;
  updateUploadStatus: (id: string, updates: Partial<UploadItem>) => void;

  // Computed
  hasActiveUploads: () => boolean;
  activeCount: () => number;
  completedCount: () => number;
}

// Generate unique ID for uploads
const generateUploadId = () => `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const useUploadStore = create<UploadState>((set, get) => ({
  uploads: [],
  isProcessing: false,

  addFiles: (files: File[]) => {
    const newUploads: UploadItem[] = files.map(file => ({
      id: generateUploadId(),
      status: 'pending',
      progress: 0,
      fileName: file.name,
      fileSize: file.size,
      file,
      documentId: null,
      error: null,
      startedAt: Date.now(),
    }));

    set(state => ({
      uploads: [...newUploads, ...state.uploads],
    }));

    // Start processing if not already
    if (!get().isProcessing) {
      get().processQueue();
    }
  },

  removeUpload: (id: string) => {
    set(state => ({
      uploads: state.uploads.filter(u => u.id !== id),
    }));
  },

  clearCompleted: () => {
    set(state => ({
      uploads: state.uploads.filter(u => u.status !== 'completed' && u.status !== 'failed'),
    }));
  },

  clearAll: () => {
    // Only clear if no active uploads
    const state = get();
    if (!state.hasActiveUploads()) {
      set({ uploads: [] });
    }
  },

  updateUploadStatus: (id: string, updates: Partial<UploadItem>) => {
    set(state => ({
      uploads: state.uploads.map(u =>
        u.id === id ? { ...u, ...updates } : u
      ),
    }));
  },

  processQueue: async () => {
    const state = get();
    if (state.isProcessing) return;

    set({ isProcessing: true });

    while (true) {
      const currentState = get();
      const pendingUpload = currentState.uploads.find(u => u.status === 'pending');

      if (!pendingUpload) {
        break; // No more pending uploads
      }

      // Start this upload
      const { updateUploadStatus } = get();

      updateUploadStatus(pendingUpload.id, {
        status: 'uploading',
        startedAt: Date.now()
      });

      try {
        // Upload with progress tracking
        const result = await api.uploadWithProgress<Document>(
          '/documents',
          pendingUpload.file,
          (percent) => {
            updateUploadStatus(pendingUpload.id, { progress: percent });
          }
        );

        // Move to processing state
        updateUploadStatus(pendingUpload.id, {
          status: 'processing',
          progress: 100,
          documentId: result.id,
        });

      } catch (error) {
        // Mark as failed
        const errorMessage = (error as { detail?: string })?.detail ||
                            (error as Error)?.message ||
                            'Upload failed';

        updateUploadStatus(pendingUpload.id, {
          status: 'failed',
          error: errorMessage,
        });
      }
    }

    set({ isProcessing: false });
  },

  hasActiveUploads: () => {
    const state = get();
    return state.uploads.some(u =>
      u.status === 'pending' ||
      u.status === 'uploading' ||
      u.status === 'processing'
    );
  },

  activeCount: () => {
    const state = get();
    return state.uploads.filter(u =>
      u.status === 'pending' ||
      u.status === 'uploading' ||
      u.status === 'processing'
    ).length;
  },

  completedCount: () => {
    const state = get();
    return state.uploads.filter(u =>
      u.status === 'completed' || u.status === 'failed'
    ).length;
  },
}));

// Hook to poll for document processing status updates
export function useUploadProcessingSync(documents: Document[] | undefined) {
  const { uploads, updateUploadStatus } = useUploadStore();

  // Update upload status based on document processing status
  if (documents) {
    uploads.forEach(upload => {
      if (upload.status !== 'processing' || !upload.documentId) return;

      const doc = documents.find(d => d.id === upload.documentId);
      if (!doc) return;

      if (doc.processing_status === 'completed') {
        updateUploadStatus(upload.id, { status: 'completed' });
      } else if (doc.processing_status === 'failed') {
        updateUploadStatus(upload.id, {
          status: 'failed',
          error: doc.error_message || 'Processing failed',
        });
      }
    });
  }
}
