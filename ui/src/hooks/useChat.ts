import { useChatStore } from "@/store/chat.store";
import { useUIStore } from "@/store/ui.store";
import { streamChat, sendAgent } from "@/api/chat";

export function useChat() {
  const { activeProject, chatMode } = useUIStore();
  const { messages, addMessage, appendToken, setSources, setStreamingDone } = useChatStore();

  // Key is the active project name, or "__all__" when no project is selected
  const messageKey = activeProject ?? "__all__";
  const projectMessages = messages[messageKey] ?? [];

  const lastMessage = projectMessages[projectMessages.length - 1];
  const isWaiting = lastMessage?.role === "assistant" && lastMessage.isStreaming === true;

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isWaiting) return;

    const scopedProject = activeProject ?? undefined;

    addMessage(messageKey, { role: "user", content: trimmed, isStreaming: false });
    
    if(chatMode === "agent"){
      addMessage(messageKey, { role: "assistant", content: "", isStreaming: true });
      try {
        const res = await sendAgent({ question: trimmed, project: scopedProject });
        appendToken(messageKey, res.answer);
      }catch{
        appendToken(messageKey, "Errore nella risposta. Verifica che il backend sia attivo.");
      } finally{
        setStreamingDone(messageKey);
      }
      return;
    }
    
    // RAG — streaming
    addMessage(messageKey, { role: "assistant", content: "", isStreaming: true });

    try{
      for await( const event of streamChat({ question: trimmed, project: scopedProject }) ){
        switch(event.type){
          case "sources":
            setSources(messageKey, event.sources);
            break;
          case "token":
            appendToken(messageKey, event.content);
            break;
          case "done":
            setStreamingDone(messageKey);
            break;
          case "error":
            appendToken(messageKey, `\n\n_Errore: ${event.message}_`);
            setStreamingDone(messageKey);
            break;
        }
      }
    } catch {
      appendToken(messageKey, "\n\n_Errore di connessione. Verifica che il backend sia attivo._");
      setStreamingDone(messageKey);
    }
  }

  return { projectMessages, isWaiting, send };
}
