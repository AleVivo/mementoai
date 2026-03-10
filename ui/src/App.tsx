import "./App.css";
import { Sidebar } from "./components/layout/Sidebar";
import { MainPanel } from "./components/layout/MainPanel";
import { ChatPanel } from "./components/layout/ChatPanel";
import { useUIStore } from "./store/ui.store";
import { TooltipProvider } from "@/components/ui/tooltip";

function App() {
  const isChatOpen = useUIStore((s) => s.isChatOpen);
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-[#FAFAFA]">
        {isSidebarOpen && <Sidebar />}
        <MainPanel />
        {isChatOpen && <ChatPanel />}
      </div>
    </TooltipProvider>
  );
}

export default App;
