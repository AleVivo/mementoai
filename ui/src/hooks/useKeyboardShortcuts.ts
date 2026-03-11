import { useEffect } from "react";
import { useUIStore } from "@/store/ui.store";

export function useKeyboardShortcuts() {
  const { isDirty, setNewEntryOpen, toggleChat } = useUIStore();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ignore shortcuts when typing in inputs / textareas / contenteditable
      const target = e.target as HTMLElement;
      const isEditable =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      if (e.ctrlKey || e.metaKey) {
        switch (e.key.toLowerCase()) {
          case "n":
            if (!isEditable) {
              e.preventDefault();
              setNewEntryOpen(true);
            }
            break;
          case "j":
            e.preventDefault();
            toggleChat();
            break;
          case "k":
            if (!isEditable) {
              e.preventDefault();
              // Focus the search bar if present
              const searchInput = document.querySelector<HTMLInputElement>(
                '[data-search-input="true"]'
              );
              searchInput?.focus();
            }
            break;
          default:
            break;
        }
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDirty]);
}
