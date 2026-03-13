import { useChatStore } from "@/store/chat.store";
import { useUIStore } from "@/store/ui.store";
import { sendChat, sendAgent } from "@/api/chat";

export function useChat() {
  const { activeProject, chatMode } = useUIStore();
  const { messages, isWaiting, addMessage, setWaiting } = useChatStore();

  // Key is the active project name, or "__all__" when no project is selected
  const messageKey = activeProject ?? "__all__";
  const projectMessages = messages[messageKey] ?? [];

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isWaiting) return;
    addMessage(messageKey, { role: "user", content: trimmed });
    setWaiting(true);
    try {
      // Pass project only when one is active — backend searches everything when omitted
      const scopedProject = activeProject ?? undefined;
      let answer: string;
      if (chatMode === "agent") {
        const res = await sendAgent({ question: trimmed, project: scopedProject });
        answer = res.answer;
      } else {
        const res = await sendChat({ question: trimmed, project: scopedProject });
        answer = res.answer;
      }
      addMessage(messageKey, { role: "assistant", content: answer });
    } catch {
      addMessage(messageKey, {
        role: "assistant",
        content: "Errore nella risposta. Verifica che il backend sia attivo.",
      });
    } finally {
      setWaiting(false);
    }
  }

  return { projectMessages, isWaiting, send };
}
