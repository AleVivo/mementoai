import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Placeholder from "@tiptap/extension-placeholder";
import Typography from "@tiptap/extension-typography";
import Link from "@tiptap/extension-link";
import TaskList from "@tiptap/extension-task-list";
import TaskItem from "@tiptap/extension-task-item";
import Highlight from "@tiptap/extension-highlight";
import CodeBlockLowlight from "@tiptap/extension-code-block-lowlight";
import { common, createLowlight } from "lowlight";

import { useEffect, useRef, useState } from "react";
import { useUIStore } from "@/store/ui.store";
import { useEntriesStore } from "@/store/entries.store";
import { updateEntry, indexEntry } from "@/api/entries";
import type { Entry, EntryType } from "@/types";

import { EntryMeta } from "./EntryMeta";
import { EditorToolbar } from "./EditorToolbar";

const lowlight = createLowlight(common);

interface LocalMeta {
  title: string;
  entry_type: EntryType;
  author: string;
  tags: string[];
  summary: string;
}

interface EntryEditorProps {
  entry: Entry;
}

export function EntryEditor({ entry }: EntryEditorProps) {
  const { setDirty, setSaving, setIndexing } = useUIStore();
  const { upsertEntry } = useEntriesStore();

  const [meta, setMeta] = useState<LocalMeta>({
    title: entry.title,
    entry_type: entry.entry_type,
    author: entry.author,
    tags: entry.tags,
    summary: entry.summary,
  });

  // Keep a ref to always have the latest meta in async callbacks
  const metaRef = useRef(meta);
  metaRef.current = meta;

  const autosaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const entryIdRef = useRef(entry.id);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ codeBlock: false }),
      Placeholder.configure({ placeholder: "Inizia a scrivere..." }),
      Typography,
      Link.configure({ openOnClick: false }),
      TaskList,
      TaskItem.configure({ nested: true }),
      Highlight,
      CodeBlockLowlight.configure({ lowlight }),
    ],
    content: entry.content,
    onUpdate() {
      setDirty(true);
      scheduleAutosave();
    },
  });

  // When the active entry changes, reset local state and editor content
  useEffect(() => {
    entryIdRef.current = entry.id;
    setMeta({
      title: entry.title,
      entry_type: entry.entry_type,
      author: entry.author,
      tags: entry.tags,
      summary: entry.summary,
    });
    if (editor) {
      editor.commands.setContent(entry.content ?? "", { emitUpdate: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entry.id]);

  // Clear pending timer on unmount
  useEffect(() => {
    return () => {
      if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    };
  }, []);

  // Ctrl+S — save immediato
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
        save();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editor]);

  function scheduleAutosave() {
    if (autosaveTimer.current) clearTimeout(autosaveTimer.current);
    autosaveTimer.current = setTimeout(() => save(), 1500);
  }

  async function save() {
    if (!editor) return;
    setSaving(true);
    try {
      const updated = await updateEntry(entryIdRef.current, {
        ...metaRef.current,
        content: editor.getHTML(),
      });
      upsertEntry(updated);
      setDirty(false);
    } catch {
      // Autosave is best-effort; silent failure
    } finally {
      setSaving(false);
    }
  }

  async function triggerIndex() {
    setIndexing(true);
    try {
      const updated = await indexEntry(entryIdRef.current);
      upsertEntry(updated);
    } catch {
      // silent
    } finally {
      setIndexing(false);
    }
  }

  function handleMetaChange(partial: Partial<LocalMeta>) {
    const next = { ...metaRef.current, ...partial };
    setMeta(next);
    setDirty(true);
    scheduleAutosave();
  }

  return (
    <div className="flex flex-col h-full">
      <EntryMeta
        entry={entry}
        title={meta.title}
        entryType={meta.entry_type}
        author={meta.author}
        tags={meta.tags}
        summary={meta.summary}
        onTitleChange={(v) => handleMetaChange({ title: v })}
        onTypeChange={(v) => handleMetaChange({ entry_type: v })}
        onAuthorChange={(v) => handleMetaChange({ author: v })}
        onTagsChange={(v) => handleMetaChange({ tags: v })}
        onSummaryChange={(v) => handleMetaChange({ summary: v })}
      />
      {editor && <EditorToolbar editor={editor} entry={entry} onIndex={triggerIndex} />}
      <EditorContent
        editor={editor}
        className="flex-1 overflow-y-auto [&_.tiptap]:outline-none [&_.tiptap]:min-h-[200px] [&_.tiptap_h1]:text-xl [&_.tiptap_h1]:font-semibold [&_.tiptap_h1]:mb-2 [&_.tiptap_h2]:text-lg [&_.tiptap_h2]:font-medium [&_.tiptap_h2]:mb-2 [&_.tiptap_p]:mb-2 [&_.tiptap_ul]:list-disc [&_.tiptap_ul]:pl-5 [&_.tiptap_ul]:mb-2 [&_.tiptap_ol]:list-decimal [&_.tiptap_ol]:pl-5 [&_.tiptap_ol]:mb-2 [&_.tiptap_blockquote]:border-l-2 [&_.tiptap_blockquote]:border-[#E5E5E5] [&_.tiptap_blockquote]:pl-3 [&_.tiptap_blockquote]:text-[#6B7280] [&_.tiptap_code]:bg-[#F0F0F0] [&_.tiptap_code]:px-1 [&_.tiptap_code]:rounded [&_.tiptap_code]:text-xs [&_.tiptap_pre]:bg-[#F0F0F0] [&_.tiptap_pre]:p-3 [&_.tiptap_pre]:rounded [&_.tiptap_pre]:text-xs [&_.tiptap_pre]:mb-2 [&_.tiptap_mark]:bg-yellow-100"
      />
    </div>
  );
}
