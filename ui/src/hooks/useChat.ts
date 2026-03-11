import { useChatStore } from "@/store/chat.store";
import { useUIStore } from "@/store/ui.store";
import { sendChat } from "@/api/chat";

export function useChat() {
  const { activeProject } = useUIStore();
  const { messages, isWaiting, addMessage, setWaiting } = useChatStore();

  const project = activeProject ?? "global";
  const projectMessages = messages[project] ?? [];

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isWaiting || !activeProject) return;
    addMessage(project, { role: "user", content: trimmed });
    setWaiting(true);
    try {
      const res = await sendChat({
        question: trimmed,
        project: activeProject,
      });
      addMessage(project, { role: "assistant", content: res.answer });
    } catch {
      addMessage(project, {
        role: "assistant",
        content: "Errore nella risposta. Verifica che il backend sia attivo.",
      });
    } finally {
      setWaiting(false);
    }
  }

  return { projectMessages, isWaiting, send };
}
