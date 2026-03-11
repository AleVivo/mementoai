import { X } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { Separator } from "@/components/ui/separator";
import { Drawer, DrawerContent } from "@/components/ui/drawer";
import { useChat } from "@/hooks/useChat";
import { ChatHistory } from "./ChatHistory";
import { ChatInput } from "./ChatInput";

export function ChatDrawer() {
  const { isChatOpen, toggleChat, activeProject } = useUIStore();
  const { projectMessages, isWaiting, send } = useChat();

  return (
    <Drawer
      open={isChatOpen}
      onOpenChange={(open) => { if (!open) toggleChat(); }}
      direction="right"
    >
      <DrawerContent className="flex flex-col w-80 h-full rounded-none border-l border-[#E5E5E5] bg-[#FAFAFA]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#E5E5E5] shrink-0">
          <span className="text-sm font-medium text-[#1A1A1A]">
            Chat{activeProject ? ` · ${activeProject}` : ""}
          </span>
          <button onClick={toggleChat} className="p-1 rounded hover:bg-[#E5E5E5] text-[#6B7280]">
            <X size={14} />
          </button>
        </div>

        <ChatHistory
          messages={projectMessages}
          isWaiting={isWaiting}
          activeProject={activeProject}
        />
        <Separator />
        <ChatInput onSend={send} disabled={isWaiting} />
      </DrawerContent>
    </Drawer>
  );
}
