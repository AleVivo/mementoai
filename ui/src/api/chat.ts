import { BASE_URL } from "./client";
import { useAuthStore } from "../store/auth.store";
import type { ChatRequest, AgentRequest, AgentSSEEvent, SSEEvent } from "../types";

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function* streamAgent(request: AgentRequest): AsyncGenerator<AgentSSEEvent> {
  const response = await fetch(`${BASE_URL}/agent`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(request),
  });

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
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);
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
