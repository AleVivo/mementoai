import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/types";

interface Props {
  message: ChatMessageType;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`flex flex-col gap-0.5 ${isUser ? "items-end" : "items-start"}`}>
      <span className="text-[10px] text-[var(--text-muted-ui)]">{isUser ? "Tu" : "AI"}</span>
      <div
        className={`text-sm px-4 py-2.5 max-w-[85%] ${
          isUser
            ? "bg-[var(--accent-ui)] text-white rounded-2xl rounded-br-sm whitespace-pre-wrap"
            : "bg-[var(--bg-hover)] text-foreground rounded-2xl rounded-bl-sm"
        }`}
      >
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-1">{children}</ol>,
              code: ({ children }) => (
                <code className="bg-background/60 rounded px-1 text-xs font-mono">{children}</code>
              ),
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}
