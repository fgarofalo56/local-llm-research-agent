const API_BASE = '/api';

interface ApiError {
  detail: string;
  status: number;
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
  get: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`);
    return handleResponse<T>(response);
  },

  post: async <T>(path: string, data?: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    });
    return handleResponse<T>(response);
  },

  put: async <T>(path: string, data: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  delete: async <T>(path: string): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
    });
    return handleResponse<T>(response);
  },

  upload: async <T>(path: string, file: File): Promise<T> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<T>(response);
  },
};
