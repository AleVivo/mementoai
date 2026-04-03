import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";

export interface ContextMenuItem {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  tooltip?: string;
  danger?: boolean;
}

interface ContextMenuProps {
  x: number;
  y: number;
  items: ContextMenuItem[];
  onClose: () => void;
}

/** Floating context menu rendered at (x, y) screen coordinates via a portal. */
export function ContextMenu({ x, y, items, onClose }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handlePointerDown(e: PointerEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return createPortal(
    <div
      ref={menuRef}
      style={{ position: "fixed", top: y, left: x, zIndex: 9999 }}
      className="min-w-[160px] rounded-md border border-[var(--border-ui)] bg-[var(--bg-subtle)] shadow-md py-1"
    >
      {items.map((item, i) => (
        <div key={i} title={item.tooltip}>
          <button
            disabled={item.disabled}
            onClick={() => {
              if (!item.disabled && item.onClick) {
                item.onClick();
                onClose();
              }
            }}
            className={cn(
              "w-full text-left text-xs px-3 py-1.5 transition-colors",
              item.disabled
                ? "text-[var(--text-muted-ui)] opacity-50 cursor-not-allowed"
                : item.danger
                  ? "text-destructive hover:bg-destructive/10"
                  : "text-foreground hover:bg-[var(--bg-hover)]",
            )}
          >
            {item.label}
          </button>
        </div>
      ))}
    </div>,
    document.body,
  );
}

/** Returns props and state for attaching a context menu to any element. */
export function useContextMenu() {
  const menuState = useRef<{ x: number; y: number; open: boolean } | null>(null);

  return menuState;
}
