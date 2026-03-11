import "./App.css";
import { Sidebar } from "./components/layout/Sidebar";
import { MainPanel } from "./components/layout/MainPanel";
import { ChatDrawer } from "./components/chat/ChatDrawer";
import { useUIStore } from "./store/ui.store";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

function App() {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  useKeyboardShortcuts();

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-background">
        {isSidebarOpen && <Sidebar />}
        <MainPanel />
        <ChatDrawer />
      </div>
      <Toaster position="bottom-right" richColors />
    </TooltipProvider>
  );
}

export default App;
