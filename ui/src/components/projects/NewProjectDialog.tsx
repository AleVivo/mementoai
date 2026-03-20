import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createProject } from "@/api/projects";
import { useProjectsStore } from "@/store/projects.store";
import { useUIStore } from "@/store/ui.store";

interface NewProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function NewProjectDialog({ open, onOpenChange }: NewProjectDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { upsertProject } = useProjectsStore();
  const { setActiveProjectId } = useUIStore();

  function reset() {
    setName("");
    setDescription("");
    setError(null);
  }

  function handleOpenChange(value: boolean) {
    onOpenChange(value);
    if (!value) reset();
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Il nome del progetto è obbligatorio.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const created = await createProject({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      upsertProject(created);
      setActiveProjectId(created.id);
      onOpenChange(false);
      reset();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "";
      if (msg.includes("409")) {
        setError("Esiste già un progetto con questo nome.");
      } else {
        setError("Errore nella creazione. Verifica che il backend sia attivo.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Nuovo progetto</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-2">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-[var(--text-muted-ui)]">Nome *</label>
            <Input
              autoFocus
              placeholder="es. Backend API"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium text-[var(--text-muted-ui)]">Descrizione</label>
            <Input
              placeholder="Breve descrizione del progetto"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}

          <div className="flex justify-end gap-2 mt-1">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annulla
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creazione..." : "Crea progetto"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
