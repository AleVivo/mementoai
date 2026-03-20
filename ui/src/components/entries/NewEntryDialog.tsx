import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus } from "lucide-react";
import { createEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useUIStore } from "@/store/ui.store";
import { useProjectsStore } from "@/store/projects.store";
import type { EntryType } from "@/types";

interface NewEntryDialogProps {
  /** The project_id to create the entry in */
  projectId: string;
}

export function NewEntryDialog({ projectId }: NewEntryDialogProps) {
  const [title, setTitle] = useState("");
  const [entryType, setEntryType] = useState<EntryType>("adr");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { upsertEntry } = useEntriesStore();
  const { setActiveEntryId, isNewEntryOpen, setNewEntryOpen } = useUIStore();
  const projects = useProjectsStore((s) => s.projects);
  const projectName = projects.find((p) => p.id === projectId)?.name ?? projectId;

  function reset() {
    setTitle("");
    setEntryType("adr");
    setError(null);
  }

  function handleOpenChange(value: boolean) {
    setNewEntryOpen(value);
    if (!value) reset();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Il titolo è obbligatorio.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await createEntry({
        title: title.trim(),
        content: "",
        entry_type: entryType,
        project_id: projectId,
      });
      upsertEntry(created);
      setActiveEntryId(created.id);
      setNewEntryOpen(false);
      reset();
    } catch {
      setError("Errore nella creazione. Verifica che il backend sia attivo.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={isNewEntryOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <button className="flex items-center gap-1.5 text-xs text-[var(--text-muted-ui)] hover:text-foreground px-2 py-1 rounded-md hover:bg-[var(--bg-hover)] transition-colors">
          <Plus size={13} />
          Nuova entry
        </button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nuova entry</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5 mt-2">
          {/* Title */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-[var(--text-muted-ui)]">Titolo *</label>
            <Input
              autoFocus
              placeholder="es. ADR-001 Scelta database"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Type */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-[var(--text-muted-ui)]">Tipo *</label>
            <Select value={entryType} onValueChange={(v) => setEntryType(v as EntryType)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="adr">ADR</SelectItem>
                <SelectItem value="postmortem">Postmortem</SelectItem>
                <SelectItem value="update">Update</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Project (read-only) */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-[var(--text-muted-ui)]">Progetto</label>
            <p className="text-sm text-foreground px-3 py-2 rounded-md bg-[var(--bg-subtle)] border border-[var(--border-ui)]">
              {projectName}
            </p>
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}

          <div className="flex justify-end gap-2 mt-1">
            <Button type="button" variant="outline" onClick={() => setNewEntryOpen(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creazione..." : "Crea entry"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
