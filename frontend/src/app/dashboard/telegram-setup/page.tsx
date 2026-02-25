"use client";

import { useState } from "react";
import Link from "next/link";
import { Send, X } from "lucide-react";
import PhoneMockup from "@/components/PhoneMockup";
import { Button } from "@/components/ui/Button";

export default function TelegramSetupPage() {
  const [token, setToken] = useState("");

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center p-4 md:p-8">
      <div className="glow-border relative w-full max-w-6xl overflow-hidden rounded-2xl bg-card">
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-4 top-4 z-10 text-muted-foreground hover:text-foreground md:right-6 md:top-6"
          asChild
        >
          <Link href="/dashboard" aria-label="Back to dashboard">
            <X className="h-6 w-6" />
          </Link>
        </Button>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:gap-0">
          <div className="flex flex-col justify-center p-8 md:p-12 lg:p-16">
            <div className="mb-10 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary">
                <Send className="h-6 w-6 text-primary-foreground" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                Connect Telegram
              </h1>
            </div>

            <div className="space-y-8">
              <h2 className="text-lg font-semibold text-foreground">
                How to get your bot token?
              </h2>

              <ol className="space-y-5 text-secondary-foreground">
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">1.</span>
                  <span>
                    Open Telegram and go to{" "}
                    <a
                      href="https://t.me/BotFather"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-primary hover:underline"
                    >
                      @BotFather
                    </a>
                    .
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">2.</span>
                  <span>
                    Start a chat and type{" "}
                    <code className="rounded bg-muted px-2 py-0.5 text-sm text-foreground">
                      /newbot
                    </code>
                    .
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">3.</span>
                  <span>Follow the prompts to name your bot and choose a username.</span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">4.</span>
                  <span>
                    BotFather will send you a message with your bot token. Copy the entire token
                    (it looks like a long string of numbers and letters).
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">5.</span>
                  <span>Paste the token in the field below and click Save & Connect.</span>
                </li>
              </ol>

              <div className="space-y-3 pt-4">
                <label
                  htmlFor="telegram-token"
                  className="text-sm font-semibold text-foreground"
                >
                  Enter bot token
                </label>
                <input
                  id="telegram-token"
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="w-full rounded-lg border border-border bg-background px-4 py-3 font-mono text-sm text-foreground placeholder:text-muted-foreground transition-all focus:border-transparent focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <Button
                className="w-full gap-2"
                disabled={!token.trim()}
              >
                Save & Connect ✓
              </Button>
            </div>
          </div>

          <div className="flex items-center justify-center bg-secondary/30 p-8 lg:p-12">
            <PhoneMockup />
          </div>
        </div>
      </div>
    </div>
  );
}
