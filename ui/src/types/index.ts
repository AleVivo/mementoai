export type EntryType = "adr" | "postmortem" | "update" | "other";

export type VectorStatus = "pending" | "indexed" | "outdated";

export interface Entry {
  id: string;
  title: string;
  content: string;
  entry_type: EntryType;
  author: string;      // display name — read-only, derived from authorId
  authorId: string;
  projectId: string;
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
  project_id: string;
  tags?: string[];
  summary?: string;
}

export interface EntryUpdate {
  title?: string;
  content?: string;
  entry_type?: EntryType;
  tags?: string[];
  summary?: string;
}

// #### SEARCH TYPES ####

export interface SearchRequest {
  query: string;
  project_id?: string;
  top_k?: number;
}

export interface SearchResult {
  entry_id: string;
  entry_type: EntryType;
  entry_title: string;
  project_id: string;
  heading: string | null;
  text: string;
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
  project_id?: string;
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
  project_id?: string;
  conversation_id?: string;
}

export interface AgentStep {
  tool: string;
  args: Record<string, unknown>;
  result: unknown;
}

export type AgentSSEEvent =
  | { type: 'session';   conversation_id: string }   // ← nuovo
  | { type: 'token';     content: string }
  | { type: 'reasoning'; content: string }
  | { type: 'step';      tool: string; args: Record<string, unknown>; result: unknown }
  | { type: 'done';      steps: AgentStep[]; model: string }
  | { type: 'error';     message: string };

// #### PROJECT TYPES ####

export interface Project {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  createdAt: string;
  currentUserRole: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

export interface ProjectMember {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  addedAt: string;
}

// #### AUTH TYPES ####

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  role: "user" | "admin";
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// #### ADMIN TYPES ####

export type FieldType = "text" | "secret" | "select" | "toggle";
export type SectionType = "integration" | "settings";
export type ConfigStatus = "unknown" | "active" | "error";

export interface SelectOption {
  value: string;
  label: string;
}

export interface DependsOn {
  field: string;
  options: Record<string, SelectOption[]>;
}

export interface RequiredIf {
  field: string;
  in?: string[];
  not_in?: string[];
}

export interface SchemaField {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  required_if?: RequiredIf;
  placeholder?: string;
  options?: SelectOption[];
  depends_on?: DependsOn;
  value: string | boolean | null;
}

export interface ConfigSection {
  id: string;
  type: SectionType;
  label: string;
  description?: string;
  fields: SchemaField[];
  status?: ConfigStatus;
  status_message?: string;
  last_tested_at?: string;
  updated_at?: string;
  updated_by?: string;
}

export interface ConfigUpdateRequest {
  values: Record<string, string | boolean | null>;
}