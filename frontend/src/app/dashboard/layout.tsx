"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Button } from "@/components/ui/Button";
import { ClawHostLogo } from "@/components/Logo";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, token, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (token === null && typeof window !== "undefined") router.push("/login");
  }, [token, router]);

  if (token === null) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-neutral-400">Loading…</p>
      </main>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--muted)] px-6 py-4 flex items-center justify-between">
        <nav className="flex items-center gap-6">
          <Link href="/">
            <ClawHostLogo size="sm" />
          </Link>
          <Link href="/dashboard" className={pathname === "/dashboard" ? "text-emerald-500" : "text-neutral-400 hover:text-[var(--foreground)]"}>Dashboard</Link>
          <Link href="/dashboard/instances" className={pathname === "/dashboard/instances" ? "text-emerald-500" : "text-neutral-400 hover:text-[var(--foreground)]"}>Intance</Link>
          <Link href="/dashboard/subscribe" className={pathname === "/dashboard/subscribe" ? "text-emerald-500" : "text-neutral-400 hover:text-[var(--foreground)]"}>Subscribe</Link>
          <Link href="/dashboard/account" className={pathname === "/dashboard/account" ? "text-emerald-500" : "text-neutral-400 hover:text-[var(--foreground)]"}>Account</Link>
        </nav>
        <div className="flex items-center gap-4">
          <span className="text-sm text-neutral-400">{user?.email}</span>
          <Button
            variant="outline"
            size="sm"
            className="border-red-500/60 text-red-400 hover:bg-red-500/15 hover:text-red-300"
            asChild
          >
            <Link href="/dashboard/account" aria-label="Delete account">
              Delete account
            </Link>
          </Button>
          <Button variant="ghost" size="sm" onClick={() => { logout(); router.push("/"); }}>Log out</Button>
        </div>
      </header>
      <div className="flex-1 p-6">{children}</div>
    </div>
  );
}
