import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => twMerge(clsx(inputs));

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
