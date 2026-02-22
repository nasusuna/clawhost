"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";

const faqs = [
  {
    q: "What is ClawHost?",
    a: "ClawHost is a managed deployment platform for OpenClaw AI agents. Dedicated VPS per customer — no servers to manage, no SSH, no configuration. Your AI agent goes live in under 60 seconds.",
  },
  {
    q: "Which AI models are supported?",
    a: "We support Claude (Anthropic), GPT (OpenAI), and Gemini out of the box. You add your own API keys in the OpenClaw Control UI. Switch models anytime—no redeploy needed.",
  },
  {
    q: "Which messaging platforms can I connect?",
    a: "Currently Telegram and Discord are fully supported. WhatsApp integration is coming soon. Connect via the OpenClaw Control UI with your gateway token.",
  },
  {
    q: "Is my data secure?",
    a: "Absolutely. Each customer gets a dedicated VPS. Your API keys stay on your instance and are never shared. HTTPS, firewalls, and automatic security updates.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Yes — no lock-in, no cancellation fees. Cancel from your dashboard; your instance remains active until the end of the billing period.",
  },
  {
    q: "Do I need technical knowledge?",
    a: "Minimal. Sign up, subscribe, and paste your gateway token into OpenClaw. We handle provisioning, SSL, and updates.",
  },
];

export default function FAQSection() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section id="faq" className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <div className="mb-14 text-center">
          <span className="badge-pill mb-4 inline-block">FAQ</span>
          <h2 className="mb-4 text-4xl font-bold text-foreground md:text-5xl">
            Common questions
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <div
              key={i}
              className="card-glass overflow-hidden rounded-xl transition-all duration-300"
            >
              <button
                type="button"
                className="flex w-full items-center justify-between p-5 text-left transition-colors hover:bg-accent/30"
                onClick={() => setOpen(open === i ? null : i)}
              >
                <span className="pr-4 font-medium text-foreground">{faq.q}</span>
                <ChevronDown
                  className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-300 ${
                    open === i ? "rotate-180 text-brand-cyan" : ""
                  }`}
                />
              </button>
              {open === i && (
                <div className="border-t border-border/40 px-5 pb-5 pt-4 text-sm leading-relaxed text-muted-foreground">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
