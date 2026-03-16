import { BookMarked, FileText, Search, MessageSquare } from "lucide-react";

export function AuthBrandingPanel() {
  return (
    <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12" style={{ background: "#0F172A" }}>
      <div className="flex items-center gap-2.5">
        <BookMarked size={20} className="text-white" />
        <span className="text-white font-semibold tracking-tight">MementoAI</span>
      </div>
      <div className="space-y-6">
        <div className="space-y-3">
          <h1 className="text-3xl font-semibold text-white leading-snug">
            Your team's knowledge base,<br />always at hand.
          </h1>
          <p className="text-sm" style={{ color: "#94A3B8" }}>
            Write structured documents, search them semantically,<br />and query them with AI.
          </p>
        </div>
        <ul className="space-y-3">
          {[
            { icon: FileText, label: "Structured docs — ADRs, postmortems, updates" },
            { icon: Search,   label: "Semantic search across your knowledge base" },
            { icon: MessageSquare, label: "RAG chat and ReAct agent on your documents" },
          ].map(({ icon: Icon, label }) => (
            <li key={label} className="flex items-center gap-3">
              <div className="flex items-center justify-center w-7 h-7 rounded-md" style={{ background: "rgba(255,255,255,0.08)" }}>
                <Icon size={13} className="text-white" />
              </div>
              <span className="text-sm" style={{ color: "#CBD5E1" }}>{label}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-xs" style={{ color: "#475569" }}>Local-first. No cloud dependencies. Data stays on your device.</p>
    </div>
  );
}
