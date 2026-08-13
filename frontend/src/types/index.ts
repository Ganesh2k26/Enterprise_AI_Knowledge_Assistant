export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  status: "pending" | "processing" | "ready" | "failed";
  error_message: string | null;
  page_count: number | null;
  is_favorite: boolean;
  is_scanned: boolean;
  embedding_count: number;
  folder_id: string | null;
  created_at: string;
}

export interface Folder {
  id: string;
  name: string;
  parent_folder_id: string | null;
  created_at: string;
}

export interface Citation {
  document_id: string;
  chunk_id: string;
  filename: string;
  page_number: number | null;
  section_title: string | null;
  chunk_text: string;
  similarity_score: number;
  confidence_score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  citations: Citation[];
  confidence_score: number | null;
  token_usage?: { suggested_questions?: string[] };
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  document_ids: string[];
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminOverview {
  registered_users: number;
  uploaded_documents: number;
  failed_documents: number;
  storage_used_bytes: number;
  embedding_count: number;
  usage_last_30_days: { action: string; count: number; avg_latency_ms: number }[];
  recent_documents: { id: string; filename: string; status: string; file_size_bytes: number; created_at: string }[];
}

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}
