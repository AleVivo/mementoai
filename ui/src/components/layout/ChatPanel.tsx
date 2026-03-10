import { X } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { useChatStore } from "@/store/chat.store";
import { sendChat } from "@/api/chat";
import { useState, useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export function ChatPanel() {
  const { toggleChat, activeProject } = useUIStore();
  const { messages, isWaiting, addMessage, setWaiting } = useChatStore();
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const project = activeProject ?? "global";
  const projectMessages = messages[project] ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [projectMessages.length]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isWaiting) return;
    setInput("");
    addMessage(project, { role: "user", content: text });
    setWaiting(true);
    try {
      const res = await sendChat({ message: text, project: activeProject ?? undefined, history: projectMessages });
      addMessage(project, { role: "assistant", content: res.answer });
    } catch {
      addMessage(project, { role: "assistant", content: "Errore nella risposta. Verifica che il backend sia attivo." });
    } finally {
      setWaiting(false);
    }
  }

  return (
    <aside className="flex flex-col w-80 shrink-0 h-full border-l border-[#E5E5E5] bg-[#FAFAFA]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[#E5E5E5]">
        <span className="text-sm font-medium text-[#1A1A1A]">
          Chat {activeProject ? `· ${activeProject}` : ""}
        </span>
        <button onClick={toggleChat} className="p-1 rounded hover:bg-[#E5E5E5] text-[#6B7280]">
          <X size={14} />
        </button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-3">
        {projectMessages.length === 0 ? (
          <p className="text-xs text-[#6B7280] text-center mt-8">
            Fai una domanda sulla knowledge base
            {activeProject ? ` del progetto "${activeProject}"` : ""}.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {projectMessages.map((msg, i) => (
              <div key={i} className={`flex flex-col gap-0.5 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <span className="text-[10px] text-[#6B7280]">{msg.role === "user" ? "Tu" : "AI"}</span>
                <div
                  className={`text-sm px-3 py-2 rounded-lg max-w-[85%] whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-[#1A1A1A] text-white"
                      : "bg-[#F0F0F0] text-[#1A1A1A]"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isWaiting && (
              <div className="flex flex-col items-start gap-0.5">
                <span className="text-[10px] text-[#6B7280]">AI</span>
                <div className="text-sm px-3 py-2 rounded-lg bg-[#F0F0F0] text-[#6B7280]">...</div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      <Separator />

      {/* Input */}
      <div className="flex gap-2 px-3 py-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Fai una domanda..."
          disabled={isWaiting}
          className="flex-1 text-sm bg-transparent outline-none placeholder:text-[#9CA3AF] disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isWaiting}
          className="text-xs px-2 py-1 rounded bg-[#1A1A1A] text-white disabled:opacity-40 hover:bg-[#333] transition-colors"
        >
          Invia
        </button>
      </div>
    </aside>
  );
}
