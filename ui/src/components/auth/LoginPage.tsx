import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { loginUser } from "@/api/auth";
import { useAuthStore } from "@/store/auth.store";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { AuthBrandingPanel } from "./AuthBrandingPanel";
import { BookMarked } from "lucide-react";

interface Props {
  onSwitchToRegister: () => void;
}

export function LoginPage({ onSwitchToRegister }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const { access_token, refresh_token, user } = await loginUser(email, password);
      setAuth(access_token, refresh_token, user);
    } catch (err) {
      console.error("Login error:", err);
      setError("Credenziali non valide. Controlla email e password e riprova.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <AuthBrandingPanel />

      {/* Right form panel */}
      <div className="relative flex flex-1 items-center justify-center px-6 bg-[var(--bg-subtle)]">
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <BookMarked size={18} />
            <span className="font-semibold tracking-tight">MementoAI</span>
          </div>

          <div
            className="rounded-xl p-8 space-y-6 bg-card"
            style={{
              border: "1px solid var(--border-ui)",
              boxShadow: "var(--shadow-md)",
            }}
          >
            <div className="space-y-1">
              <h2 className="text-xl font-semibold tracking-tight">Sign in</h2>
              <p className="text-sm text-[var(--text-muted-ui)]">Enter your credentials to continue</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {error && (
                <p className="text-xs text-destructive rounded-md px-3 py-2 bg-destructive/10">
                  {error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign in"}
              </Button>
            </form>

            <p className="text-center text-sm text-[var(--text-muted-ui)]">
              No account?{" "}
              <button
                type="button"
                onClick={onSwitchToRegister}
                className="font-medium text-foreground underline underline-offset-4 hover:text-[var(--accent-ui)] transition-colors"
              >
                Create one
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
