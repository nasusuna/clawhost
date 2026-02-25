import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => twMerge(clsx(inputs));

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const API_BASE = rawApiUrl;

/** Call once from client to warn if production build uses localhost API. */
export const assertProductionApiUrl = (): void => {
  if (typeof window === "undefined") return;
  if (process.env.NODE_ENV !== "production") return;
  const u = rawApiUrl.toLowerCase();
  if (u.includes("localhost") || u.startsWith("http://127.0.0.1")) {
    console.warn(
      "[ClawBolt] NEXT_PUBLIC_API_URL looks like localhost. Set it to your production API URL (e.g. https://api.clawbolt.online) for production."
    );
  }
};
