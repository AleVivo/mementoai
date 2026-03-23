import { useEffect, useState } from "react";
import { Settings2 } from "lucide-react";
import { ConfigSection } from "@/types";
import { getAllConfig } from "@/api/admin";
import { AdminSection } from "./AdminSection";
import { ThemeToggle } from "../layout/ThemeToggle";

export function AdminConsole() {
  const [sections, setSections] = useState<ConfigSection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAllConfig()
      .then(setSections)
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }, []);

  const handleUpdated = (updated: ConfigSection) => {
    setSections((prev) =>
      prev.map((s) => (s.id === updated.id ? updated : s))
    );
  };

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 h-12 border-b border-[var(--border-ui)] bg-background shrink-0">
        <Settings2 size={16} className="text-[var(--text-muted-ui)]" />
        <h1 className="text-sm font-semibold text-foreground">Admin Console</h1>
        <div className="ml-auto shrink-0">
            <ThemeToggle />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-[var(--text-muted-ui)]">Caricamento configurazione...</p>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-32">
            <p className="text-sm text-red-500">{error}</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4 max-w-2xl mx-auto w-full">
            {sections.map((section) => (
              <AdminSection
                key={section.id}
                section={section}
                onUpdated={handleUpdated}
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}