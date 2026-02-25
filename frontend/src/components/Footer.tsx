"use client";

import Link from "next/link";
import { Zap, Mail, Twitter, Github } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-border/50 px-6 py-12">
      <div className="mx-auto max-w-5xl">
        <div className="mb-10 grid gap-8 md:grid-cols-4">
          <div>
            <div className="mb-4 flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-brand-cyan to-brand-blue">
                <Zap className="h-3.5 w-3.5 text-primary-foreground" />
              </div>
              <span className="font-bold text-foreground">
                Claw<span className="text-gradient">Bolt</span>
              </span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Deploy your AI agent in under 60 seconds. Dedicated VPS, no config, no complexity.
            </p>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-foreground">Product</h4>
            <ul className="space-y-2">
              {["Features", "Pricing"].map((item) => (
                <li key={item}>
                  <Link
                    href={`#${item.toLowerCase()}`}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {item}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/dashboard"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-foreground">Account</h4>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/login"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Log in
                </Link>
              </li>
              <li>
                <Link
                  href="/register"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Register
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-sm font-semibold text-foreground">Legal</h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Privacy
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                >
                  Terms
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between border-t border-border/40 pt-6 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © 2025 ClawBolt. All rights reserved.
          </p>
          <div className="mt-4 flex items-center gap-3 sm:mt-0">
            {[Mail, Twitter, Github].map((Icon, i) => (
              <a
                key={i}
                href="#"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-secondary text-muted-foreground transition-all duration-200 hover:bg-accent hover:text-foreground"
                aria-label="Social link"
              >
                <Icon className="h-3.5 w-3.5" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
