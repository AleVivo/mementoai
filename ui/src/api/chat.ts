import { apiPost } from "./client";
import type { ChatRequest, ChatResponse, AgentRequest, AgentResponse } from "../types";

export const sendChat = (data: ChatRequest) =>
  apiPost<ChatResponse>("/chat", data);

export const sendAgent = (data: AgentRequest) =>
  apiPost<AgentResponse>("/agent", data);
