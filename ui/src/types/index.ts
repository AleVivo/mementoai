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
  week: string;
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

// #### SEARCH TYPES ####

export interface SearchRequest {
  query: string;
  project?: string;
  entry_type?: EntryType;
  top_k?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  summary: string;
  author: string;
  project: string;
  entry_type: EntryType;
  tags: string[];
  score: number;
}

// #### CHAT TYPES ####

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  isStreaming: boolean;
}

export interface ChatRequest {
  question: string;
  project?: string;
}

export interface ChatSource {
  entry_id: string;
  title: string;
  entry_type: EntryType;
  section: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export type SSEEvent = 
  | { type: 'sources'; sources: ChatSource[] }
  | { type: 'token';   content: string }
  | { type: 'done' }
  | { type: 'error';   message: string };


// #### AGENT TYPES ####
export interface AgentRequest {
  question: string; 
  project?: string; 
}

export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

export interface AgentResponse {
  answer: string;
  steps: AgentStep[];
  model: string;
}