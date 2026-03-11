import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/types";

interface Props {
  message: ChatMessageType;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  return (
    <div className={`flex flex-col gap-0.5 ${isUser ? "items-end" : "items-start"}`}>
      <span className="text-[10px] text-[#6B7280]">{isUser ? "Tu" : "AI"}</span>
      <div
        className={`text-sm px-3 py-2 rounded-lg max-w-[85%] ${
          isUser
            ? "bg-[#1A1A1A] text-white whitespace-pre-wrap"
            : "bg-[#F0F0F0] text-[#1A1A1A]"
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
                <code className="bg-white/60 rounded px-1 text-xs font-mono">{children}</code>
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
