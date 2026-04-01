import { useState } from "react";
import type { Editor } from "@tiptap/react";
import {
  Bold,
  Italic,
  Strikethrough,
  Code,
  Heading1,
  Heading2,
  List,
  ListOrdered,
  ListTodo,
  Quote,
  Code2,
  Highlighter,
  Trash2,
  BrainCircuit,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
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
import { deleteEntry } from "@/api/entries";
import { useEntriesStore } from "@/store/entries.store";
import { useUIStore } from "@/store/ui.store";
import type { Entry } from "@/types";

interface ToolBtnProps {
  onClick: () => void;
  active?: boolean;
  title: string;
  children: React.ReactNode;
}

function ToolBtn({ onClick, active, title, children }: ToolBtnProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`p-1 rounded-md transition-colors ${
        active
          ? "bg-[var(--bg-hover)] text-foreground"
          : "text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function Divider() {
  return <div className="w-px h-4 bg-[var(--border-ui)] mx-0.5 self-center" />
}

interface EditorToolbarProps {
  editor: Editor;
  entry: Entry;
  onIndex: () => void;
}

export function EditorToolbar({ editor, entry, onIndex }: EditorToolbarProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const { removeEntry } = useEntriesStore();
  const { setActiveEntryId, isIndexing } = useUIStore();

  async function handleDelete() {
    setIsDeleting(true);
    try {
      await deleteEntry(entry.id);
      removeEntry(entry.id);
      setActiveEntryId(null);
      toast.success(`"${entry.title}" eliminata`);
    } catch {
      toast.error("Errore durante l'eliminazione");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="flex items-center gap-0.5 flex-wrap px-2 py-1.5 rounded-lg bg-[var(--bg-subtle)] border border-[var(--border-ui)] mb-6">
      <ToolBtn
        onClick={() => editor.chain().focus().toggleBold().run()}
        active={editor.isActive("bold")}
        title="Grassetto"
      >
        <Bold size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleItalic().run()}
        active={editor.isActive("italic")}
        title="Corsivo"
      >
        <Italic size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleStrike().run()}
        active={editor.isActive("strike")}
        title="Barrato"
      >
        <Strikethrough size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleCode().run()}
        active={editor.isActive("code")}
        title="Codice inline"
      >
        <Code size={14} />
      </ToolBtn>

      <Divider />

      <ToolBtn
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        active={editor.isActive("heading", { level: 1 })}
        title="Titolo 1"
      >
        <Heading1 size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        active={editor.isActive("heading", { level: 2 })}
        title="Titolo 2"
      >
        <Heading2 size={14} />
      </ToolBtn>

      <Divider />

      <ToolBtn
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        active={editor.isActive("bulletList")}
        title="Lista puntata"
      >
        <List size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        active={editor.isActive("orderedList")}
        title="Lista numerata"
      >
        <ListOrdered size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleTaskList().run()}
        active={editor.isActive("taskList")}
        title="Lista attività"
      >
        <ListTodo size={14} />
      </ToolBtn>

      <Divider />

      <ToolBtn
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        active={editor.isActive("blockquote")}
        title="Citazione"
      >
        <Quote size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleCodeBlock().run()}
        active={editor.isActive("codeBlock")}
        title="Blocco codice"
      >
        <Code2 size={14} />
      </ToolBtn>
      <ToolBtn
        onClick={() => editor.chain().focus().toggleHighlight().run()}
        active={editor.isActive("highlight")}
        title="Evidenzia"
      >
        <Highlighter size={14} />
      </ToolBtn>

      <div className="flex-1" />
      <Divider />

      <button
        type="button"
        title="Indicizza (embedding)"
        disabled={isIndexing}
        onClick={onIndex}
        className="flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground disabled:opacity-50 transition-colors"
      >
        {isIndexing ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          <BrainCircuit size={14} />
        )}
        <span>{isIndexing ? "Indicizzazione..." : "Indicizza"}</span>
      </button>

      <Divider />

      <AlertDialog>
        <AlertDialogTrigger asChild>
          <button
            type="button"
            title="Elimina entry"
            disabled={isDeleting}
            className="p-1 rounded-md text-[var(--text-muted-ui)] hover:bg-[var(--color-destructive-hover-bg)] hover:text-[var(--color-error)] transition-colors disabled:opacity-50"
          >
            <Trash2 size={14} />
          </button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminare questa entry?</AlertDialogTitle>
            <AlertDialogDescription>
              Stai per eliminare <strong>"{entry.title}"</strong>. Questa azione non può essere annullata.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annulla</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              Elimina
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
