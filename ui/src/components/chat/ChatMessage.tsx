import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/types";
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
interface Props {
  message: ChatMessageType;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [reasoningOpen, setReasoningOpen] = useState(false);

  // Balloon vuoto durante il caricamento iniziale — mostra solo il loader (in ChatHistory)
  const hasVisibleContent =
    message.content ||
    message.reasoning ||
    (message.steps && message.steps.length > 0) ||
    (message.sources && message.sources.length > 0);

  if (!isUser && message.isStreaming && !hasVisibleContent) return null;

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
          <>
          {/* Sources — appaiono appena arriva l'evento sources, prima del done */}
          {message.sources && message.sources.length > 0 && (
              <div className="mb-2 pb-2 border-b border-[var(--border-ui)]">
                <button
                  onClick={() => setSourcesOpen((v) => !v)}
                  className="flex items-center gap-1 text-[11px] text-[var(--text-muted-ui)] hover:text-foreground transition-colors"
                >
                  {sourcesOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  {message.sources.length} {message.sources.length === 1 ? "fonte consultata" : "fonti consultate"}
                </button>

                {sourcesOpen && (
                  <div className="mt-1.5 flex flex-col gap-1">
                    {message.sources.map((source, i) => (
                      <span
                        key={`${source.entry_id}-${i}`}
                        className="text-[11px] text-[var(--text-muted-ui)]"
                      >
                        {source.title}
                        {source.section && (
                          <span className="opacity-60"> — {source.section}</span>
                        )}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 2 — Reasoning (Agent) */}
            {message.reasoning && (
              <div className="mb-2 pb-2 border-b border-[var(--border-ui)]">
                <button
                  onClick={() => setReasoningOpen((v) => !v)}
                  className="flex items-center gap-1 text-[11px] text-[var(--text-muted-ui)] hover:text-foreground transition-colors italic"
                >
                  {reasoningOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                  Ragionamento
                </button>
                {reasoningOpen && (
                  <p className="mt-1.5 text-[11px] text-[var(--text-muted-ui)] italic leading-relaxed whitespace-pre-wrap">
                    {message.reasoning}
                  </p>
                )}
              </div>
            )}

            {/* 3 — Steps (Agent) */}
            {message.steps && message.steps.length > 0 && (
              <div className="mb-2 pb-2 border-b border-[var(--border-ui)] flex flex-col gap-1">
                {message.steps.map((step, i) => (
                  <span key={i} className="text-[11px] text-[var(--text-muted-ui)] flex items-center gap-1.5">
                    {step.pending ? (
                      <span className="inline-block w-2.5 h-2.5 rounded-full border border-current border-t-transparent animate-spin flex-shrink-0" />
                    ) : (
                      <span className="inline-block w-2 h-2 rounded-full bg-current opacity-50 flex-shrink-0" />
                    )}
                    <span className={`font-mono bg-background/60 rounded px-1 ${step.pending ? "opacity-60" : ""}`}>{step.tool}</span>
                  </span>
                ))}
              </div>
            )}

            {/* Contenuto del messaggio */}
            {message.content && (
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


          </>
        )}
      </div>
    </div>
  );
}
