import { create } from "zustand";
import type { User } from "../types";

function decodeEmail(token: string): string {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.email ?? "";
  } catch {
    return "";
  }
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (token: string, refreshToken: string, profile?: Partial<User>) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>(() => {
  const token = localStorage.getItem("auth_token");
  const refreshToken = localStorage.getItem("auth_refresh_token");
  const storedProfile = localStorage.getItem("auth_user");
  const user: User | null = token
    ? (storedProfile ? JSON.parse(storedProfile) : { id: "", email: decodeEmail(token), first_name: "", last_name: "", company: "", created_at: "" })
    : null;

  return {
    token,
    refreshToken,
    user,

    setAuth: (token, refreshToken, profile) => {
      const user: User = {
        id: profile?.id ?? "",
        email: profile?.email ?? decodeEmail(token),
        first_name: profile?.first_name ?? "",
        last_name: profile?.last_name ?? "",
        company: profile?.company ?? "",
        created_at: profile?.created_at ?? "",
      };
      localStorage.setItem("auth_token", token);
      localStorage.setItem("auth_refresh_token", refreshToken);
      localStorage.setItem("auth_user", JSON.stringify(user));
      useAuthStore.setState({ token, refreshToken, user });
    },

    logout: () => {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_refresh_token");
      localStorage.removeItem("auth_user");
      useAuthStore.setState({ token: null, refreshToken: null, user: null });
    },
  };
});
