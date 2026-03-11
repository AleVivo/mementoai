import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import type { ChatMessage as ChatMessageType } from "@/types";

interface Props {
  messages: ChatMessageType[];
  isWaiting: boolean;
  activeProject: string | null;
}

export function ChatHistory({ messages, isWaiting, activeProject }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isWaiting]);

  return (
    <ScrollArea className="flex-1 px-4 py-3">
      {messages.length === 0 ? (
        <p className="text-xs text-[var(--text-muted-ui)] text-center mt-8">
          Fai una domanda sulla knowledge base
          {activeProject ? ` del progetto "${activeProject}"` : ""}.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
          {isWaiting && (
            <div className="flex flex-col items-start gap-0.5">
              <span className="text-[10px] text-[var(--text-muted-ui)]">AI</span>
              <div className="text-sm px-4 py-2.5 rounded-2xl rounded-bl-sm bg-[var(--bg-hover)] text-[var(--text-muted-ui)]">...</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </ScrollArea>
  );
}
