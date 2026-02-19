"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type User = { id: string; email: string } | null;

type AuthContextValue = {
  user: User;
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  setUser: (u: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User>(null);
  const [token, setToken] = useState<string | null>(null);

  const login = useCallback((t: string) => {
    setToken(t);
    if (typeof window !== "undefined") localStorage.setItem("clawhost_token", t);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    if (typeof window !== "undefined") localStorage.removeItem("clawhost_token");
  }, []);

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("clawhost_token") : null;
    if (t) setToken(t);
  }, []);

  useEffect(() => {
    if (!token) {
      setUser(null);
      return;
    }
    const fetchUser = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setUser({ id: data.id, email: data.email });
        } else {
          logout();
        }
      } catch {
        logout();
      }
    };
    fetchUser();
  }, [token, logout]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};
