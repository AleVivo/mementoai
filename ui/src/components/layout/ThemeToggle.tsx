import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(() => localStorage.getItem("theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
    localStorage.setItem("theme", isDark ? "dark" : "light");
  }, [isDark]);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={() => setIsDark((d) => !d)}
          className="p-1.5 rounded-md text-[var(--text-muted-ui)] hover:bg-[var(--bg-hover)] hover:text-foreground transition-colors"
          aria-label="Cambia tema"
        >
          {isDark ? <Sun size={14} /> : <Moon size={14} />}
        </button>
      </TooltipTrigger>
      <TooltipContent>{isDark ? "Tema chiaro" : "Tema scuro"}</TooltipContent>
    </Tooltip>
  );
}
