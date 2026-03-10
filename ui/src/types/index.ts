export type EntryType = "adr" | "postmortem" | "update" | "other";

export type VectorStatus = "pending" | "indexed" | "outdated";

export interface Entry {
  id: string;
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;
  project: string;
  tags: string[];
  summary: string;
  vector_status: VectorStatus;
  created_at: string;
  updated_at: string;
}

export interface EntryCreate {
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;
  project: string;
  tags?: string[];
  summary?: string;
}

export interface EntryUpdate {
  title?: string;
  content?: string;
  entry_type?: EntryType;
  author?: string;
  project?: string;
  tags?: string[];
  summary?: string;
}

export interface SearchRequest {
  query: string;
  project?: string;
  entry_type?: EntryType;
  top_k?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  raw_text: string;
  author: string;
  project: string;
  entry_type: EntryType;
  tags: string[];
  score: number;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  message: string;
  project?: string;
  history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  sources: SearchResult[];
}
