import { useChatStore } from "@/store/chat.store";
import { useUIStore } from "@/store/ui.store";
import { streamChat, streamAgent } from "@/api/chat";

export function useChat() {
  const { activeProjectId, chatMode } = useUIStore();
  const { messages, conversationIds, addMessage, setConversationId, appendToken, appendReasoning, addStep, setSources, setStreamingDone } = useChatStore();

  // Key is the active project id, or "__all__" when no project is selected
  const messageKey = activeProjectId ?? "__all__";
  const projectMessages = messages[messageKey] ?? [];
  const conversationId = conversationIds[messageKey] ?? null;

  const lastMessage = projectMessages[projectMessages.length - 1];
  const isWaiting = lastMessage?.role === "assistant" && lastMessage.isStreaming === true;

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || isWaiting) return;

    const scopedProjectId = activeProjectId ?? undefined;

    addMessage(messageKey, { role: "user", content: trimmed, isStreaming: false });
    
    if (chatMode === "agent") {
      addMessage(messageKey, { role: "assistant", content: "", isStreaming: true });
      try {
        for await (const event of streamAgent({
           question: trimmed, 
           project_id: scopedProjectId,
           conversation_id: conversationId ?? undefined,
          })) {
          switch (event.type) {
            case "session":
              setConversationId(messageKey, event.conversation_id);
            break;
            case "token":
              appendToken(messageKey, event.content);
              break;
            case "reasoning":
              appendReasoning(messageKey, event.content);
              break;
            case "step":
              addStep(messageKey, { tool: event.tool, args: event.args ?? {}, result: event.result });
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
      return;
    }
    
    // RAG — streaming
    addMessage(messageKey, { role: "assistant", content: "", isStreaming: true });

    try{
      for await( const event of streamChat({ question: trimmed, project_id: scopedProjectId }) ){
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
