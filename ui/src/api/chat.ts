import { apiPost, BASE_URL } from "./client";
import type { ChatRequest, AgentRequest, AgentResponse, SSEEvent } from "../types";

export const sendAgent = (data: AgentRequest) =>
  apiPost<AgentResponse>("/agent", data);

export async function* streamChat(request: ChatRequest): AsyncGenerator<SSEEvent>{
  const response = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) throw new Error(`API error: ${response.status}`);
  if (!response.body) throw new Error('No response body');

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? '';

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
