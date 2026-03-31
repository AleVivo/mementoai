import { create } from "zustand";
import type { AgentStep, ChatMessage, ChatSource } from "../types";

interface ChatState {
  messages: Record<string, ChatMessage[]>;
  conversationIds: Record<string, string | null>;

  setConversationId: (project: string, id: string) => void;
  addMessage:       (project: string, message: ChatMessage) => void;
  appendToken:      (project: string, token: string) => void;
  appendReasoning:  (project: string, content: string) => void;
  addStep:          (project: string, step: AgentStep) => void;
  setSources:       (project: string, sources: ChatSource[]) => void;
  setStreamingDone: (project: string) => void;
  clearMessages:    (project: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: {},
  conversationIds: {},

  setConversationId: (project, id) =>
    set((s) => ({
      conversationIds: { ...s.conversationIds, [project]: id },
    })),

  addMessage: (project, message) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [project]: [...(s.messages[project] ?? []), message],
      },
    })),

  appendToken: (project, token) =>
    set((s) => {
      const msgs = [...(s.messages[project] ?? [])];
      const last = msgs[msgs.length - 1];
      if (!last || last.role !== "assistant") return s;
      msgs[msgs.length - 1] = { ...last, content: last.content + token };
      return { messages: { ...s.messages, [project]: msgs } };
    }),

  appendReasoning: (project, content) =>
    set((s) => {
      const msgs = [...(s.messages[project] ?? [])];
      const last = msgs[msgs.length - 1];
      if (!last || last.role !== "assistant") return s;
      msgs[msgs.length - 1] = {
        ...last,
        reasoning: last.reasoning
          ? last.reasoning + "\n\n" + content
          : content,
      };
      return { messages: { ...s.messages, [project]: msgs } };
    }),

  addStep: (project, step) =>
    set((s) => {
      const msgs = [...(s.messages[project] ?? [])];
      const last = msgs[msgs.length - 1];
      if (!last || last.role !== "assistant") return s;
      msgs[msgs.length - 1] = {
        ...last,
        steps: [...(last.steps ?? []), step],
      };
      return { messages: { ...s.messages, [project]: msgs } };
    }),

  setSources: (project, sources) =>
    set((s) => {
      const msgs = [...(s.messages[project] ?? [])];
      const last = msgs[msgs.length - 1];
      if (!last || last.role !== "assistant") return s;
      msgs[msgs.length - 1] = { ...last, sources };
      return { messages: { ...s.messages, [project]: msgs } };
    }),

  setStreamingDone: (project) =>
    set((s) => {
      const msgs = [...(s.messages[project] ?? [])];
      const last = msgs[msgs.length - 1];
      if (!last) return s;
      msgs[msgs.length - 1] = { ...last, isStreaming: false };
      return { messages: { ...s.messages, [project]: msgs } };
    }),

  clearMessages: (project) =>
    set((s) => {
      const messages = { ...s.messages };
      const conversationIds = { ...s.conversationIds };
      delete messages[project];
      delete conversationIds[project];
      return { messages, conversationIds };
    }),
}));
