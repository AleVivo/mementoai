import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { registerUser, loginUser } from "@/api/auth";
import { useAuthStore } from "@/store/auth.store";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { AuthBrandingPanel } from "./AuthBrandingPanel";
import { BookMarked } from "lucide-react";

interface Props {
  onSwitchToLogin: () => void;
}

export function RegisterPage({ onSwitchToLogin }: Props) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const profile = await registerUser({ email, password, first_name: firstName, last_name: lastName, company });
      const { access_token, refresh_token } = await loginUser(email, password);
      setAuth(access_token, refresh_token, profile);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
              <h2 className="text-xl font-semibold tracking-tight">Create an account</h2>
              <p className="text-sm text-[var(--text-muted-ui)]">Join your team's knowledge base</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  type="text"
                  placeholder="First name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  autoFocus
                />
                <Input
                  type="text"
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                />
              </div>
              <Input
                type="text"
                placeholder="Company (optional)"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
              <Input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <Input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <Input
                type="password"
                placeholder="Confirm password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              {error && (
                <p className="text-xs text-destructive rounded-md px-3 py-2 bg-destructive/10">
                  {error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Creating account..." : "Create account"}
              </Button>
            </form>

            <p className="text-center text-sm text-[var(--text-muted-ui)]">
              Already have an account?{" "}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="font-medium text-foreground underline underline-offset-4 hover:text-[var(--accent-ui)] transition-colors"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
