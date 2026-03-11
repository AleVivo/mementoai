import { apiPost } from "./client";
import type { ChatRequest, ChatResponse } from "../types";

export const sendChat = (data: ChatRequest) =>
  apiPost<ChatResponse>("/chat", data);
