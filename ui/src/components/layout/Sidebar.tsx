import { useEffect } from "react";
import { PanelLeftClose, Plus, MessageSquare } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { getEntries } from "@/api/entries";
import { EntryList } from "@/components/entries/EntryList";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function Sidebar() {
  const { activeProject, setActiveProject, toggleSidebar, toggleChat, setActiveEntryId } = useUIStore();
  const { entries, isLoading, setEntries, setLoading } = useEntriesStore();

  useEffect(() => {
    setLoading(true);
    getEntries(activeProject ?? undefined)
      .then(setEntries)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeProject]);

  const projects = Array.from(new Set(entries.map((e) => e.project))).sort();

  return (
    <aside className="flex flex-col w-56 shrink-0 h-full border-r border-[#E5E5E5] bg-[#F5F5F5]">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-[#E5E5E5]">
        <span className="text-xs font-semibold tracking-wide text-[#6B7280] uppercase">MementoAI</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleSidebar} className="p-1 rounded hover:bg-[#E5E5E5] text-[#6B7280]">
              <PanelLeftClose size={14} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Chiudi sidebar</TooltipContent>
        </Tooltip>
      </div>

      {/* Project filter */}
      <div className="px-3 py-2 border-b border-[#E5E5E5]">
        <p className="text-[11px] font-medium text-[#6B7280] uppercase tracking-wide mb-1">Progetto</p>
        <div className="flex flex-col gap-0.5">
          <button
            onClick={() => setActiveProject(null)}
            className={cn(
              "text-left text-sm px-2 py-1 rounded truncate",
              activeProject === null ? "bg-[#E5E5E5] font-medium text-[#1A1A1A]" : "text-[#6B7280] hover:bg-[#EBEBEB]"
            )}
          >
            Tutti
          </button>
          {projects.map((p) => (
            <button
              key={p}
              onClick={() => setActiveProject(p)}
              className={cn(
                "text-left text-sm px-2 py-1 rounded truncate",
                activeProject === p ? "bg-[#E5E5E5] font-medium text-[#1A1A1A]" : "text-[#6B7280] hover:bg-[#EBEBEB]"
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Entry list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <p className="text-xs text-[#6B7280] px-3 py-4">Caricamento...</p>
        ) : (
          <EntryList
            entries={entries.filter((e) => !activeProject || e.project === activeProject)}
            onSelect={setActiveEntryId}
          />
        )}
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-between px-3 py-2 border-t border-[#E5E5E5]">
        <button
          onClick={() => setActiveEntryId(null)}
          className="flex items-center gap-1.5 text-xs text-[#6B7280] hover:text-[#1A1A1A] px-2 py-1 rounded hover:bg-[#E5E5E5]"
        >
          <Plus size={13} />
          Nuova entry
        </button>
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleChat} className="p-1 rounded hover:bg-[#E5E5E5] text-[#6B7280]">
              <MessageSquare size={14} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Apri chat</TooltipContent>
        </Tooltip>
      </div>
    </aside>
  );
}
