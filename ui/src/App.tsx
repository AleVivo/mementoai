import "./App.css";
import { Sidebar } from "./components/layout/Sidebar";
import { MainPanel } from "./components/layout/MainPanel";
import { ChatDrawer } from "./components/chat/ChatDrawer";
import { useUIStore } from "./store/ui.store";
import { TooltipProvider } from "@/components/ui/tooltip";

function App() {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-[#FAFAFA]">
        {isSidebarOpen && <Sidebar />}
        <MainPanel />
        <ChatDrawer />
      </div>
    </TooltipProvider>
  );
}

export default App;
