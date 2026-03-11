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
    <div className="flex gap-2 px-3 py-2 shrink-0">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Fai una domanda... (Enter per inviare)"
        disabled={disabled}
        rows={2}
        className="flex-1 text-sm bg-transparent outline-none placeholder:text-[#9CA3AF] disabled:opacity-50 resize-none"
      />
      <button
        onClick={submit}
        disabled={!value.trim() || disabled}
        className="self-end text-xs px-2 py-1 rounded bg-[#1A1A1A] text-white disabled:opacity-40 hover:bg-[#333] transition-colors"
      >
        Invia
      </button>
    </div>
  );
}
