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
  reasoning?: string;
  steps?: AgentStep[];
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

export type AgentSSEEvent =
  | { type: 'token';     content: string }
  | { type: 'reasoning'; content: string }
  | { type: 'step';      tool: string; args: Record<string, unknown>; result: unknown }
  | { type: 'done';      steps: AgentStep[]; model: string }
  | { type: 'error';     message: string };

// #### AUTH TYPES ####

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}
