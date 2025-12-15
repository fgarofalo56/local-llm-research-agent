export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool_calls: string | null;
  tokens_used: number | null;
  created_at: string;
  metadata?: {
    sources?: Array<{ name: string; url?: string; type: string }>;
    [key: string]: unknown;
  };
}

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  mime_type: string | null;
  file_size: number;
  chunk_count: number | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message: string | null;
  tags: string[];
  created_at: string;
  processed_at: string | null;
}

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  type: 'stdio' | 'http';
  enabled: boolean;
  built_in: boolean;
}

export interface QueryHistory {
  id: number;
  conversation_id: number | null;
  natural_language: string;
  generated_sql: string;
  result_row_count: number | null;
  execution_time_ms: number | null;
  is_favorite: boolean;
  created_at: string;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  services: {
    name: string;
    status: 'healthy' | 'unhealthy' | 'unknown';
    message: string | null;
    latency_ms: number | null;
  }[];
}

// Re-export dashboard types
export * from './dashboard';
