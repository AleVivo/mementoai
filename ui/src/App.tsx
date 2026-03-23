import "./App.css";
import { useState } from "react";
import { Sidebar } from "./components/layout/Sidebar";
import { MainPanel } from "./components/layout/MainPanel";
import { ChatDrawer } from "./components/chat/ChatDrawer";
import { useUIStore } from "./store/ui.store";
import { useAuthStore } from "./store/auth.store";
import { LoginPage } from "./components/auth/LoginPage";
import { RegisterPage } from "./components/auth/RegisterPage";
import { AdminConsole } from "./components/admin/AdminConsole";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "sonner";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

function App() {
  const isSidebarOpen = useUIStore((s) => s.isSidebarOpen);
  const isAdminConsoleOpen = useUIStore((s) => s.isAdminConsoleOpen);
  const token = useAuthStore((s) => s.token);
  const [showRegister, setShowRegister] = useState(false);
  useKeyboardShortcuts();

  if (!token) {
    return (
      <TooltipProvider>
        {showRegister ? (
          <RegisterPage onSwitchToLogin={() => setShowRegister(false)} />
        ) : (
          <LoginPage onSwitchToRegister={() => setShowRegister(true)} />
        )}
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex h-screen overflow-hidden bg-background">
        {isSidebarOpen && <Sidebar />}
        {isAdminConsoleOpen ? <AdminConsole /> : <MainPanel />}        
        <ChatDrawer />
      </div>
      <Toaster position="bottom-right" richColors />
    </TooltipProvider>
  );
}

export default App;

