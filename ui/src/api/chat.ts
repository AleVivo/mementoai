import { BASE_URL, tryRefresh } from "./client";
import { useAuthStore } from "../store/auth.store";
import type { ChatRequest, AgentRequest, AgentSSEEvent, SSEEvent } from "../types";

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function fetchSSE(url: string, body: unknown): Promise<Response> {
  const opts = { method: "POST", headers: authHeaders(), body: JSON.stringify(body) };
  let res = await fetch(url, opts);
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (!refreshed) throw new Error("Session expired. Please log in again.");
    res = await fetch(url, { ...opts, headers: authHeaders() });
  }
  return res;
}

export async function* streamAgent(request: AgentRequest): AsyncGenerator<AgentSSEEvent> {
  const response = await fetchSSE(`${BASE_URL}/agent`, request);

  if (!response.ok) throw new Error(`POST /agent → ${response.status}`);
  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.replace(/^data: /, "").trim();
      if (!line) continue;
      try {
        yield JSON.parse(line) as AgentSSEEvent;
      } catch {
        console.warn("Failed to parse agent SSE line:", line);
      }
    }
  }
}

export async function* streamChat(request: ChatRequest): AsyncGenerator<SSEEvent> {
  const response = await fetchSSE(`${BASE_URL}/chat`, request);

  if (!response.ok) throw new Error(`POST /chat → ${response.status}`);
  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.replace(/^data: /, '').trim();
      if (!line) continue;
      try{
        yield JSON.parse(line) as SSEEvent;
      } catch {
        console.warn("Failed to parse SSE line:", line);
      }
    }
  }
}
