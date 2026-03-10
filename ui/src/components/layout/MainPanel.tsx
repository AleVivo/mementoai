import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { PanelLeft } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { EntryEditor } from "@/components/editor/EntryEditor";

export function MainPanel() {
  const { activeEntryId, isSidebarOpen, toggleSidebar } = useUIStore();
  const entries = useEntriesStore((s) => s.entries);
  const activeEntry = entries.find((e) => e.id === activeEntryId) ?? null;

  return (
    <main className="flex flex-col flex-1 min-w-0 h-full">
      {/* Top bar */}
      <div className="flex items-center gap-2 px-4 h-10 border-b border-[#E5E5E5] shrink-0">
        {!isSidebarOpen && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button onClick={toggleSidebar} className="p-1 rounded hover:bg-[#E5E5E5] text-[#6B7280]">
                <PanelLeft size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent>Apri sidebar</TooltipContent>
          </Tooltip>
        )}
        <span className="text-sm text-[#6B7280] truncate">
          {activeEntry ? activeEntry.title : "Seleziona o crea una entry"}
        </span>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        {activeEntry ? (
          <div className="max-w-3xl mx-auto px-8 py-8 h-full overflow-y-auto">
            <EntryEditor key={activeEntry.id} entry={activeEntry} />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-[#6B7280]">
            <p className="text-sm">Seleziona una entry dalla sidebar</p>
            <p className="text-xs">oppure crea una nuova entry</p>
          </div>
        )}
      </div>
    </main>
  );
}
