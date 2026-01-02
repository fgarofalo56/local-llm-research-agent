const API_BASE = '/api';

interface ApiError {
  detail: string;
  status: number;
}

interface RequestOptions {
  headers?: Record<string, string>;
}

// Get auth token from localStorage
function getAuthToken(): string | null {
  return localStorage.getItem('access_token');
}

// Build headers with optional auth
function buildHeaders(options?: RequestOptions): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };

  // Add auth token if available and not overridden
  const token = getAuthToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = {
      detail: 'An error occurred',
      status: response.status,
    };
    try {
      const data = await response.json();
      error.detail = data.detail || data.message || error.detail;
    } catch {
      // Ignore JSON parse errors
    }
    throw error;
  }
  return response.json();
}

export const api = {
  get: async <T>(path: string, options?: RequestOptions): Promise<T> => {
    const headers = buildHeaders(options);
    // Remove Content-Type for GET requests (not needed)
    delete headers['Content-Type'];
    const response = await fetch(`${API_BASE}${path}`, { headers });
    return handleResponse<T>(response);
  },

  post: async <T>(path: string, data?: unknown, options?: RequestOptions): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: buildHeaders(options),
      body: data ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  put: async <T>(path: string, data: unknown, options?: RequestOptions): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: buildHeaders(options),
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  patch: async <T>(path: string, data: unknown, options?: RequestOptions): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PATCH',
      headers: buildHeaders(options),
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  delete: async <T>(path: string, options?: RequestOptions): Promise<T> => {
    const headers = buildHeaders(options);
    delete headers['Content-Type'];
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse<T>(response);
  },

  upload: async <T>(path: string, file: File): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return handleResponse<T>(response);
  },

  /**
   * Upload a file with progress tracking
   * @param path API path
   * @param file File to upload
   * @param onProgress Callback with progress percentage (0-100)
   * @returns Promise with response data
   */
  uploadWithProgress: <T>(
    path: string,
    file: File,
    onProgress: (percent: number) => void
  ): Promise<T> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const percent = Math.round((event.loaded / event.total) * 100);
          onProgress(percent);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            resolve(data as T);
          } catch {
            reject({ detail: 'Failed to parse response', status: xhr.status });
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject({ detail: error.detail || 'Upload failed', status: xhr.status });
          } catch {
            reject({ detail: 'Upload failed', status: xhr.status });
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject({ detail: 'Network error during upload', status: 0 });
      });

      xhr.addEventListener('abort', () => {
        reject({ detail: 'Upload cancelled', status: 0 });
      });

      xhr.open('POST', `${API_BASE}${path}`);

      // Add auth token
      const token = getAuthToken();
      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }

      xhr.send(formData);
    });
  },

  // Database settings
  getDatabaseSettings: <T>() => api.get<T>('/settings/database'),
  updateDatabaseSettings: <T>(settings: unknown) => api.put<T>('/settings/database', settings),
  testDatabaseConnection: <T>(settings: unknown) => api.post<T>('/settings/database/test', settings),
};
