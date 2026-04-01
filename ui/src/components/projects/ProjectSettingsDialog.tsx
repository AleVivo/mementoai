import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2, UserMinus, UserPlus, Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { Project, ProjectMember } from "@/types";
import {
  updateProject,
  deleteProject,
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
} from "@/api/projects";
import { lookupUserByEmail } from "@/api/users";
import { useProjectsStore } from "@/store/projects.store";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { useAuthStore } from "@/store/auth.store";

interface ProjectSettingsDialogProps {
  project: Project;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProjectSettingsDialog({ project, open, onOpenChange }: ProjectSettingsDialogProps) {
  const isOwner = project.currentUserRole === "owner";
  const { upsertProject, removeProject } = useProjectsStore();
  const { activeProjectId, setActiveProjectId, setActiveEntryId } = useUIStore();
  const { setEntries } = useEntriesStore();
  const currentUser = useAuthStore((s) => s.user);

  // Edit project info
  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description ?? "");
  const [isSavingInfo, setIsSavingInfo] = useState(false);

  // Members
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);

  // Delete project
  const [isDeleting, setIsDeleting] = useState(false);

  // Sync edit fields when project prop changes
  useEffect(() => {
    setEditName(project.name);
    setEditDescription(project.description ?? "");
  }, [project.id, project.name, project.description]);

  // Load members when dialog opens
  useEffect(() => {
    if (!open) return;
    setIsLoadingMembers(true);
    getProjectMembers(project.id)
      .then(setMembers)
      .catch(() => toast.error("Impossibile caricare i membri."))
      .finally(() => setIsLoadingMembers(false));
  }, [open, project.id]);

  async function handleSaveInfo(e: React.FormEvent) {
    e.preventDefault();
    if (!editName.trim()) return;
    setIsSavingInfo(true);
    try {
      const updated = await updateProject(project.id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });
      upsertProject(updated);
      toast.success("Progetto aggiornato.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("409")) {
        toast.error("Esiste già un progetto con questo nome.");
      } else {
        toast.error("Errore durante il salvataggio.");
      }
    } finally {
      setIsSavingInfo(false);
    }
  }

  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault();
    const email = memberEmail.trim();
    if (!email) return;
    setIsAddingMember(true);
    setMemberError(null);
    try {
      const user = await lookupUserByEmail(email);
      await addProjectMember(project.id, user.id);
      const refreshed = await getProjectMembers(project.id);
      setMembers(refreshed);
      setMemberEmail("");
      toast.success(`${user.email} aggiunto al progetto.`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("404")) {
        setMemberError("Nessun utente trovato con questa email.");
      } else if (msg.includes("409")) {
        setMemberError("L'utente è già membro di questo progetto.");
      } else {
        setMemberError("Errore durante l'aggiunta del membro.");
      }
    } finally {
      setIsAddingMember(false);
    }
  }

  async function handleRemoveMember(userId: string, displayName: string) {
    setRemovingUserId(userId);
    try {
      await removeProjectMember(project.id, userId);
      setMembers((prev) => prev.filter((m) => m.userId !== userId));
      toast.success(`${displayName} rimosso dal progetto.`);
    } catch {
      toast.error("Errore durante la rimozione del membro.");
    } finally {
      setRemovingUserId(null);
    }
  }

  async function handleDeleteProject() {
    setIsDeleting(true);
    try {
      await deleteProject(project.id);
      removeProject(project.id);
      if (activeProjectId === project.id) {
        setActiveProjectId(null);
        setActiveEntryId(null);
        setEntries([]);
      }
      onOpenChange(false);
      toast.success(`Progetto "${project.name}" eliminato.`);
    } catch {
      toast.error("Errore durante l'eliminazione del progetto.");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] flex flex-col gap-0 p-0 overflow-hidden">
        <DialogHeader className="px-6 py-4 border-b border-[var(--border-ui)]">
          <DialogTitle>Impostazioni progetto</DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 overflow-y-auto">
          <div className="flex flex-col gap-6 px-6 py-5">

            {/* ── Info section ── */}
            <section className="flex flex-col gap-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted-ui)]">
                Informazioni
              </h3>
              <form onSubmit={handleSaveInfo} className="flex flex-col gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-[var(--text-muted-ui)]">Nome</label>
                  <Input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    disabled={!isOwner}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-[var(--text-muted-ui)]">Descrizione</label>
                  <Input
                    placeholder="Breve descrizione"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    disabled={!isOwner}
                  />
                </div>
                {isOwner && (
                  <div className="flex justify-end">
                    <Button type="submit" size="sm" disabled={isSavingInfo || !editName.trim()}>
                      {isSavingInfo ? "Salvataggio..." : "Salva"}
                    </Button>
                  </div>
                )}
              </form>
            </section>

            <Separator />

            {/* ── Members section ── */}
            <section className="flex flex-col gap-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted-ui)]">
                Membri
              </h3>

              {/* Add member (owner only) */}
              {isOwner && (
                <form onSubmit={handleAddMember} className="flex flex-col gap-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Email utente..."
                      value={memberEmail}
                      onChange={(e) => { setMemberEmail(e.target.value); setMemberError(null); }}
                      className="flex-1"
                    />
                    <Button type="submit" size="sm" disabled={isAddingMember || !memberEmail.trim()}>
                      {isAddingMember ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <UserPlus size={14} />
                      )}
                    </Button>
                  </div>
                  {memberError && (
                    <p className="text-xs text-[var(--color-error)]">{memberError}</p>
                  )}
                </form>
              )}

              {/* Member list */}
              {isLoadingMembers ? (
                <div className="flex items-center gap-2 text-xs text-[var(--text-muted-ui)] py-2">
                  <Loader2 size={12} className="animate-spin" /> Caricamento...
                </div>
              ) : members.length === 0 ? (
                <p className="text-xs text-[var(--text-muted-ui)]">Nessun membro.</p>
              ) : (
                <div className="flex flex-col gap-1">
                  {members.map((m) => {
                    const displayName = [m.firstName, m.lastName].filter(Boolean).join(" ") || m.email;
                    const isSelf = m.userId === currentUser?.id;
                    return (
                      <div
                        key={m.userId}
                        className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-ui)]"
                      >
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
                          <p className="text-xs text-[var(--text-muted-ui)] truncate">{m.email}</p>
                        </div>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-hover)] text-[var(--text-muted-ui)] shrink-0 capitalize">
                          {m.role}
                        </span>
                        {isOwner && !isSelf && m.role !== "owner" && (
                          <button
                            onClick={() => handleRemoveMember(m.userId, displayName)}
                            disabled={removingUserId === m.userId}
                            title="Rimuovi membro"
                            className="shrink-0 p-1 rounded-md text-[var(--text-muted-ui)] hover:text-[var(--color-error)] hover:bg-[var(--color-destructive-hover-bg)] transition-colors disabled:opacity-50"
                          >
                            {removingUserId === m.userId ? (
                              <Loader2 size={12} className="animate-spin" />
                            ) : (
                              <UserMinus size={12} />
                            )}
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            {/* ── Danger zone (owner only) ── */}
            {isOwner && (
              <>
                <Separator />
                <section className="flex flex-col gap-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-error)]">
                    Zona pericolosa
                  </h3>
                  <p className="text-xs text-[var(--text-muted-ui)]">
                    L'eliminazione del progetto rimuove permanentemente tutte le entry, i chunk e i
                    membri associati. Questa operazione non è reversibile.
                  </p>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-fit border-[var(--color-error)] text-[var(--color-error)] hover:bg-[var(--color-destructive-hover-bg)]"
                        disabled={isDeleting}
                      >
                        {isDeleting ? (
                          <Loader2 size={13} className="animate-spin mr-1.5" />
                        ) : (
                          <Trash2 size={13} className="mr-1.5" />
                        )}
                        Elimina progetto
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Eliminare il progetto?</AlertDialogTitle>
                        <AlertDialogDescription>
                          Stai per eliminare <strong>"{project.name}"</strong>. Tutte le entry e i
                          chunk associati verranno eliminati definitivamente.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Annulla</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={handleDeleteProject}
                          className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                        >
                          Elimina
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </section>
              </>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
