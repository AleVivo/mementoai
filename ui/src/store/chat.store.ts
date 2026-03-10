import { create } from "zustand";
import type { ChatMessage } from "../types";

interface ChatState {
  messages: Record<string, ChatMessage[]>;
  isWaiting: boolean;

  addMessage: (project: string, message: ChatMessage) => void;
  setWaiting: (waiting: boolean) => void;
  clearMessages: (project: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: {},
  isWaiting: false,

  addMessage: (project, message) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [project]: [...(s.messages[project] ?? []), message],
      },
    })),
  setWaiting: (waiting) => set({ isWaiting: waiting }),
  clearMessages: (project) =>
    set((s) => {
      const messages = { ...s.messages };
      delete messages[project];
      return { messages };
    }),
}));
