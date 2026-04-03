import { useState } from "react";
import { PanelLeftClose, MessageSquare, LogOut, Settings2, Plus, ShieldCheck, AlertCircle, RefreshCw, FolderPlus, ArrowUpLeft } from "lucide-react";
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from "@dnd-kit/core";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import { toast } from "sonner";
import { useUIStore } from "@/store/ui.store";
import { useAuthStore } from "@/store/auth.store";
import { useEntriesStore } from "@/store/entries.store";
import { useProjectsStore } from "@/store/projects.store";
import { useEntries } from "@/hooks/useEntries";
import { useProjects } from "@/hooks/useProjects";
import { useFolders } from "@/hooks/useFolders";
import { updateEntry } from "@/api/entries";
import { EntryList } from "@/components/entries/EntryList";
import { NewEntryDialog } from "@/components/entries/NewEntryDialog";
import { NewProjectDialog } from "@/components/projects/NewProjectDialog";
import { ProjectSettingsDialog } from "@/components/projects/ProjectSettingsDialog";
import { FolderTree } from "@/components/folders/FolderTree";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Project } from "@/types";

export function Sidebar() {
  const { activeProjectId, setActiveProjectId, toggleSidebar, toggleChat, setActiveEntryId, setActiveFolderId } = useUIStore();
  const { entries, isLoading, error: entriesError, upsertEntry } = useEntriesStore();
  const { projects, isLoading: isLoadingProjects, error: projectsError } = useProjectsStore();
  const { user, logout } = useAuthStore();
  const [settingsProject, setSettingsProject] = useState<Project | null>(null);
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [activeDrag, setActiveDrag] = useState<{ label: string } | null>(null);
  const { toggleAdminConsole } = useUIStore();

  const { refetch: refetchProjects } = useProjects();
  const { refetch: refetchEntries } = useEntries();
  const { moveFolder } = useFolders();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  function handleDragStart(event: DragStartEvent) {
    const data = event.active.data.current as { title: string } | undefined;
    setActiveDrag({ label: data?.title ?? "..." });
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveDrag(null);
    const { active, over } = event;
    if (!over) return;
    const activeId = String(active.id);
    const overId = String(over.id);
    if (activeId === overId) return;

    const isEntryDrag = activeId.startsWith("entry:");
    const isFolderDrag = activeId.startsWith("folder:");
    const activeItemId = isEntryDrag
      ? activeId.slice("entry:".length)
      : activeId.slice("folder:".length);
    const isRootTarget = overId === "root";
    const targetFolderId = isRootTarget ? null : overId.slice("folder:".length);

    if (isEntryDrag) {
      try {
        const updated = await updateEntry(activeItemId, { folder_id: targetFolderId });
        upsertEntry(updated);
      } catch {
        toast.error("Impossibile spostare la entry");
      }
    } else if (isFolderDrag) {
      if (targetFolderId === activeItemId) return;
      // Block drop onto a descendant of the dragged folder
      const activeData = active.data.current as { path: string } | undefined;
      const overData = over.data.current as { path: string } | undefined;
      if (activeData && overData && overData.path.startsWith(activeData.path + "/")) return;
      try {
        await moveFolder(activeItemId, { new_parent_id: targetFolderId });
      } catch {
        toast.error("Impossibile spostare la cartella");
      }
    }
  }

  const activeProject = projects.find((p) => p.id === activeProjectId) ?? null;

  // Always show only root-level entries (no folder assigned).
  // Folder contents are rendered inline inside the FolderTree when expanded.
  const rootEntries = entries.filter((e) => e.folder_id === null);

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
    <aside className="flex flex-col w-64 shrink-0 h-full border-r border-[var(--border-ui)] bg-[var(--bg-subtle)]">
      {/* Header */}
      <div className="flex items-center justify-between px-4 h-12 border-b border-[var(--border-ui)]">
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

      {/* Project list */}
      <div className="px-4 py-4 border-b border-[var(--border-ui)]">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[11px] font-medium text-[var(--text-muted-ui)] uppercase tracking-wide">Progetti</p>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => setIsNewProjectOpen(true)}
                className="p-1 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] hover:text-foreground transition-colors"
              >
                <Plus size={13} />
              </button>
            </TooltipTrigger>
            <TooltipContent>Nuovo progetto</TooltipContent>
          </Tooltip>
        </div>

        {isLoadingProjects && projects.length === 0 ? (
          <p className="text-xs text-[var(--text-muted-ui)] px-3 py-2">Caricamento...</p>
        ) : projectsError ? (
          <div className="flex flex-col gap-2 px-1 py-1">
            <div className="flex items-start gap-1.5 text-xs text-destructive">
              <AlertCircle size={12} className="mt-0.5 shrink-0" />
              <span className="leading-tight">{projectsError}</span>
            </div>
            <button
              onClick={refetchProjects}
              className="flex items-center justify-center gap-1.5 w-full text-xs font-medium px-2 py-1.5 rounded-md border border-[var(--border-ui)] text-[var(--text-muted-ui)] hover:text-foreground hover:bg-[var(--bg-hover)] transition-colors"
            >
              <RefreshCw size={11} />
              Riprova
            </button>
          </div>
        ) : projects.length === 0 ? (
          <p className="text-xs text-[var(--text-muted-ui)] px-3 py-2 italic">
            Nessun progetto. Creane uno!
          </p>
        ) : (
          <div className="flex flex-col gap-1">
            {projects.map((p) => (
              <div
                key={p.id}
                className={cn(
                  "group flex items-center gap-1 rounded-lg transition-colors",
                  activeProjectId === p.id
                    ? "bg-[var(--bg-hover)]"
                    : "hover:bg-[var(--bg-hover)]"
                )}
              >
                <button
                  onClick={() => { setActiveProjectId(p.id); setActiveEntryId(null); setActiveFolderId(null); }}
                  className={cn(
                    "flex-1 text-left text-sm px-3 py-2 truncate transition-colors",
                    activeProjectId === p.id
                      ? "font-medium text-foreground"
                      : "text-[var(--text-muted-ui)] hover:text-foreground"
                  )}
                >
                  {p.name}
                </button>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      onClick={(e) => { e.stopPropagation(); setSettingsProject(p); }}
                      className="shrink-0 p-1.5 mr-1 rounded-md opacity-0 group-hover:opacity-100 text-[var(--text-muted-ui)] hover:text-foreground hover:bg-[var(--bg-subtle)] transition-all"
                    >
                      <Settings2 size={12} />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Impostazioni progetto</TooltipContent>
                </Tooltip>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Folder tree + Entry list */}
      <div className="flex-1 overflow-y-auto">
        {activeProjectId ? (
          <>
            <FolderTree onSelectEntry={setActiveEntryId} />
            <EntryList
              entries={rootEntries}
              onSelect={setActiveEntryId}
              isLoading={isLoading}
              error={entriesError}
              onRetry={refetchEntries}
            />
          </>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 px-6 text-center">
            <FolderPlus size={20} className="text-[var(--text-muted-ui)] opacity-50" />
            <div className="flex flex-col gap-1">
              <p className="text-xs font-medium text-[var(--text-muted-ui)]">Nessun progetto ancora</p>
              <p className="text-[11px] text-[var(--text-muted-ui)] opacity-60 leading-relaxed">
                Crea un progetto per iniziare ad aggiungere entry
              </p>
            </div>
            <button
              onClick={() => setIsNewProjectOpen(true)}
              className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md border border-[var(--border-ui)] text-[var(--text-muted-ui)] hover:text-foreground hover:bg-[var(--bg-hover)] transition-colors"
            >
              <Plus size={11} />
              Nuovo progetto
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-start justify-start pt-6 gap-2 px-5 text-left">
            <ArrowUpLeft size={14} className="text-[var(--text-muted-ui)] opacity-40" />
            <div className="flex flex-col gap-0.5">
              <p className="text-xs font-medium text-[var(--text-muted-ui)]">Seleziona un progetto</p>
              <p className="text-[11px] text-[var(--text-muted-ui)] opacity-60 leading-relaxed">
                Le entry del progetto appariranno qui
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer actions */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border-ui)]">
        {activeProject ? (
          <NewEntryDialog projectId={activeProject.id} />
        ) : (
          <span />
        )}
        <Tooltip>
          <TooltipTrigger asChild>
            <button onClick={toggleChat} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
              <MessageSquare size={14} />
            </button>
          </TooltipTrigger>
          <TooltipContent>Apri chat</TooltipContent>
        </Tooltip>
      </div>

      {/* User / logout */}
      <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--border-ui)]">
        <div className="flex flex-col min-w-0">
          {(user?.first_name || user?.last_name) && (
            <span className="text-xs font-medium text-foreground truncate">
              {[user.first_name, user.last_name].filter(Boolean).join(" ")}
            </span>
          )}
          <span className="text-xs text-[var(--text-muted-ui)] truncate" title={user?.email}>{user?.email}</span>
        </div>
        <div>
        {user?.role === "admin" && (
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={toggleAdminConsole}
                className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors"
              >
                <ShieldCheck size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent>Admin console</TooltipContent>
          </Tooltip>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <button onClick={logout} className="p-1.5 rounded-md hover:bg-[var(--bg-hover)] text-[var(--text-muted-ui)] transition-colors">
                <LogOut size={14} />
              </button>
            </TooltipTrigger>
            <TooltipContent>Logout</TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Project settings dialog */}
      {settingsProject && (
        <ProjectSettingsDialog
          project={settingsProject}
          open={settingsProject !== null}
          onOpenChange={(v) => { if (!v) setSettingsProject(null); }}
        />
      )}

      {/* New project dialog */}
      <NewProjectDialog open={isNewProjectOpen} onOpenChange={setIsNewProjectOpen} />
    </aside>

    <DragOverlay dropAnimation={null}>
      {activeDrag ? (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[var(--border-ui)] bg-[var(--bg-subtle)] text-xs font-medium shadow-lg opacity-90 pointer-events-none">
          {activeDrag.label}
        </div>
      ) : null}
    </DragOverlay>
    </DndContext>
  );
}
