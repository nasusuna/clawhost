import { API_BASE } from "./utils";

type Method = "GET" | "POST" | "PUT" | "DELETE";

const getToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem("clawhost_token") : null;

const handleUnauthorized = (): void => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("clawhost_token");
  window.location.href = "/login";
};

export const api = async <T>(
  path: string,
  options: { method?: Method; body?: unknown } = {}
): Promise<T> => {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers,
    ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
  });
  if (res.status === 401) {
    handleUnauthorized();
    throw new Error("Session expired");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
};
