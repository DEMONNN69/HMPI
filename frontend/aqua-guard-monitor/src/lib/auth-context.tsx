import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, refreshToken, logout as apiLogout, Tokens } from "./auth";

type AuthContextValue = {
  tokens: Tokens | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const STORAGE_KEY = "auth_tokens";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<Tokens | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) setTokens(JSON.parse(raw));
  }, []);

  useEffect(() => {
    if (tokens) localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
    else localStorage.removeItem(STORAGE_KEY);
  }, [tokens]);

  useEffect(() => {
    if (!tokens?.refresh) return;
    const id = setInterval(async () => {
      try {
        const res = await refreshToken(tokens.refresh);
        setTokens((prev) => (prev ? { ...prev, access: res.access } : prev));
      } catch (_) {
        setTokens(null);
      }
    }, 1000 * 60 * 30);
    return () => clearInterval(id);
  }, [tokens?.refresh]);

  const value = useMemo<AuthContextValue>(() => ({
    tokens,
    isAuthenticated: Boolean(tokens?.access),
    async login(username: string, password: string) {
      const t = await apiLogin(username, password);
      setTokens(t);
    },
    async logout() {
      if (tokens?.refresh) {
        try { await apiLogout(tokens.refresh); } catch {}
      }
      setTokens(null);
    },
  }), [tokens]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}


