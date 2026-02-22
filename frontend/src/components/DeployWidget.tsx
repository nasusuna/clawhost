"use client";

import { useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";

const models = [
  { id: "claude", name: "Claude Opus 4.5", emoji: "🔥", desc: "Best reasoning" },
  { id: "gpt", name: "GPT-5.2", emoji: "⚡", desc: "Fast & powerful" },
  { id: "gemini", name: "Gemini 2.5 Pro", emoji: "💎", desc: "Multimodal" },
];

const channels = [
  { id: "telegram", name: "Telegram", emoji: "✈️", available: true },
  { id: "discord", name: "Discord", emoji: "🎮", available: true },
  { id: "whatsapp", name: "WhatsApp", emoji: "💬", available: false },
];

export default function DeployWidget() {
  const [selectedModel, setSelectedModel] = useState("claude");
  const [selectedChannel, setSelectedChannel] = useState("telegram");

  return (
    <div className="card-glass w-full max-w-md rounded-2xl p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="dot-online h-2 w-2 rounded-full bg-green-400" />
        <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
          Deploy Now
        </span>
      </div>

      <div className="mb-5">
        <p className="mb-3 text-xs font-mono uppercase tracking-wider text-muted-foreground">
          1. Intelligence Model
          <span className="ml-2 rounded border border-brand-cyan/30 px-1.5 py-0.5 text-[10px] text-brand-cyan">
            Required
          </span>
        </p>
        <div className="grid grid-cols-1 gap-2">
          {models.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setSelectedModel(m.id)}
              className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-all duration-200 ${
                selectedModel === m.id
                  ? "border-brand-cyan/60 bg-brand-cyan/10 text-foreground"
                  : "border-border text-muted-foreground hover:border-border/80 hover:bg-accent"
              }`}
            >
              <span className="text-lg">{m.emoji}</span>
              <div className="flex-1">
                <div className="text-sm font-medium">{m.name}</div>
                <div className="text-xs text-muted-foreground">{m.desc}</div>
              </div>
              {selectedModel === m.id && <Check className="h-4 w-4 text-brand-cyan" />}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <p className="mb-3 text-xs font-mono uppercase tracking-wider text-muted-foreground">
          2. Messaging Channel
          <span className="ml-2 rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
            Optional
          </span>
        </p>
        <div className="flex gap-2">
          {channels.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => c.available && setSelectedChannel(c.id)}
              className={`relative flex flex-1 flex-col items-center gap-1 rounded-lg border px-4 py-3 text-center transition-all duration-200 ${
                !c.available
                  ? "cursor-not-allowed border-border/40 opacity-40"
                  : selectedChannel === c.id
                    ? "border-brand-cyan/60 bg-brand-cyan/10"
                    : "border-border hover:border-border/80 hover:bg-accent"
              }`}
            >
              <span className="text-xl">{c.emoji}</span>
              <span className="text-xs font-medium text-foreground">{c.name}</span>
              {!c.available && <span className="text-[9px] text-muted-foreground">Soon</span>}
            </button>
          ))}
        </div>
      </div>

      <Link
        href="/register"
        className="flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98]"
        style={{ background: "var(--gradient-primary)" }}
      >
        🚀 Deploy with Google
      </Link>

      <p className="mt-3 text-center text-xs text-muted-foreground">
        Secure payment · Deploy in under 60 seconds
      </p>
    </div>
  );
}
