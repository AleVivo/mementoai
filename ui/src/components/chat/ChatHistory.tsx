import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "./ChatMessage";
import type { ChatMessage as ChatMessageType } from "@/types";
import { MementoLoader } from "@/components/loader";

interface Props {
  messages: ChatMessageType[];
  activeProjectId: string | null;
}

export function ChatHistory({ messages, activeProjectId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const lastMessage = messages[messages.length - 1];
  const lastContent = lastMessage?.content ?? "";
  const isStreaming = lastMessage?.isStreaming && lastMessage.role === "assistant";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, lastContent]);

  return (
    <ScrollArea className="h-full px-4 py-3">
      {messages.length === 0 ? (
        <p className="text-xs text-[var(--text-muted-ui)] text-center mt-8">
          Fai una domanda sulla knowledge base
          {activeProjectId ? " del progetto selezionato" : ""}.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
          {isStreaming && (
            <div className="flex items-start px-1">
              <MementoLoader />
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}
    </ScrollArea>
  );
}
