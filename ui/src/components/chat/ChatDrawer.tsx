import { X } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { Separator } from "@/components/ui/separator";
import { Drawer, DrawerContent } from "@/components/ui/drawer";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useChat } from "@/hooks/useChat";
import { ChatHistory } from "./ChatHistory";
import { ChatInput } from "./ChatInput";

export function ChatDrawer() {
  const { isChatOpen, toggleChat, activeProject, chatMode, setChatMode } = useUIStore();
  const { projectMessages, isWaiting, send } = useChat();

  return (
    <Drawer
      open={isChatOpen}
      onOpenChange={(open) => { if (!open) toggleChat(); }}
      direction="right"
    >
      <DrawerContent className="flex flex-col w-96 h-full rounded-l-2xl border-l border-[var(--border-ui)] bg-background" style={{ boxShadow: "var(--shadow-lg)" }}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-ui)] shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">
              {activeProject ? `Chat · ${activeProject}` : "Chat · Tutto"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Select value={chatMode} onValueChange={(v) => setChatMode(v as "rag" | "agent")}>
              <SelectTrigger size="sm" className="h-7 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rag">RAG</SelectItem>
                <SelectItem value="agent">Agent</SelectItem>
              </SelectContent>
            </Select>
            <button onClick={toggleChat} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
              <X size={14} />
            </button>
          </div>
        </div>

        <div className="flex-1 min-h-0 overflow-hidden">
          <ChatHistory
            messages={projectMessages}
            isWaiting={isWaiting}
            activeProject={activeProject}
          />
        </div>
        <Separator />
        <ChatInput onSend={send} disabled={isWaiting} />
      </DrawerContent>
    </Drawer>
  );
}
