"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X, Zap } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-cyan to-brand-blue">
          <Zap className="h-4 w-4 text-primary-foreground" />
        </div>
        <span className="text-lg font-bold tracking-tight">
          <span className="text-foreground">Claw</span>
          <span className="text-gradient">Bolt</span>
        </span>
      </div>

      <div className="hidden md:flex items-center gap-8">
        {["Features", "Pricing", "FAQ"].map((item) => (
          <a
            key={item}
            href={`#${item.toLowerCase()}`}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
          >
            {item}
          </a>
        ))}
      </div>

      <div className="hidden md:flex items-center gap-3">
        {user ? (
          <Link
            href="/dashboard"
            className="text-sm font-semibold px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-all duration-200 glow-cyan"
          >
            Dashboard
          </Link>
        ) : (
          <>
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2"
            >
              Sign in
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-all duration-200 glow-cyan"
            >
              Get Started
            </Link>
          </>
        )}
      </div>

      <button
        type="button"
        className="md:hidden text-foreground"
        onClick={() => setOpen(!open)}
        aria-label="Toggle menu"
      >
        {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {open && (
        <div className="absolute top-full left-0 right-0 bg-card border-b border-border p-6 flex flex-col gap-4 md:hidden">
          {["Features", "Pricing", "FAQ"].map((item) => (
            <a
              key={item}
              href={`#${item.toLowerCase()}`}
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setOpen(false)}
            >
              {item}
            </a>
          ))}
          <Link
            href="/register"
            className="w-full py-2 rounded-lg bg-primary text-primary-foreground font-semibold text-center"
            onClick={() => setOpen(false)}
          >
            Get Started
          </Link>
        </div>
      )}
    </nav>
  );
}
