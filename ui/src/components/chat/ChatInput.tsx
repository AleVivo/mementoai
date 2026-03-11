import { useState } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  }

  return (
    <div className="flex gap-2 px-4 py-3 shrink-0">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Fai una domanda... (Enter per inviare)"
        disabled={disabled}
        rows={2}
        className="flex-1 text-sm bg-[var(--bg-subtle)] border border-[var(--border-ui)] rounded-xl px-3 py-2 outline-none placeholder:text-[var(--text-muted-ui)] disabled:opacity-50 resize-none focus:border-[var(--accent-ui)] transition-colors"
      />
      <button
        onClick={submit}
        disabled={!value.trim() || disabled}
        className="self-end text-xs px-3 py-2 rounded-lg bg-[var(--accent-ui)] text-white disabled:opacity-40 hover:bg-[var(--accent-hover-ui)] transition-colors"
      >
        Invia
      </button>
    </div>
  );
}
