import { PanelLeftClose, MessageSquare } from "lucide-react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { useEntries } from "@/hooks/useEntries";
import { EntryList } from "@/components/entries/EntryList";
import { NewEntryDialog } from "@/components/entries/NewEntryDialog";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function Sidebar() {
  const { activeProject, setActiveProject, toggleSidebar, toggleChat, setActiveEntryId } = useUIStore();
  const { entries, isLoading } = useEntriesStore();
  useEntries();

  const projects = Array.from(new Set(entries.map((e) => e.project))).sort();

  return (
    <aside className="flex flex-col w-64 shrink-0 h-full border-r border-[var(--border-ui)] bg-[var(--bg-subtle)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-ui)]">
        <span className="text-sm font-semibold tracking-tight text-foreground">MementoAI</span>
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleSidebar} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
              <PanelLeftClose size={14} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Chiudi sidebar</TooltipContent>
        </Tooltip>
      </div>

      {/* Project filter */}
      <div className="px-4 py-4 border-b border-[var(--border-ui)]">
        <p className="text-[11px] font-medium text-[var(--text-muted-ui)] uppercase tracking-wide mb-3">Progetto</p>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => setActiveProject(null)}
            className={cn(
              "text-left text-sm px-3 py-2 rounded-lg truncate transition-colors",
              activeProject === null ? "bg-[var(--bg-hover)] font-medium text-foreground" : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground"
            )}
          >
            Tutti
          </button>
          {projects.map((p) => (
            <button
              key={p}
              onClick={() => setActiveProject(p)}
              className={cn(
                "text-left text-sm px-3 py-2 rounded-lg truncate transition-colors",
                activeProject === p ? "bg-[var(--bg-hover)] font-medium text-foreground" : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground"
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Entry list */}
      <div className="flex-1 overflow-y-auto">
        <EntryList
          entries={entries.filter((e) => !activeProject || e.project === activeProject)}
          onSelect={setActiveEntryId}
          isLoading={isLoading}
        />
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border-ui)]">
        <NewEntryDialog defaultProject={activeProject ?? ""} />
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleChat} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
              <MessageSquare size={14} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Apri chat</TooltipContent>
        </Tooltip>
      </div>
    </aside>
  );
}
