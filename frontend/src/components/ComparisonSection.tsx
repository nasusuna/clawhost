"use client";

import { Clock, X, Check } from "lucide-react";

const traditionalSteps = [
  { step: "Purchasing local virtual machine", time: "15 min" },
  { step: "Creating SSH keys and storing securely", time: "10 min" },
  { step: "Connecting to the server via SSH", time: "5 min" },
  { step: "Installing Node.js and NPM", time: "5 min" },
  { step: "Installing OpenClaw", time: "7 min" },
  { step: "Setting up OpenClaw", time: "10 min" },
  { step: "Connecting to AI provider", time: "4 min" },
  { step: "Pairing with messaging platform", time: "4 min" },
];

const clawHostSteps = [
  { step: "Sign in & subscribe", sub: "Stripe checkout" },
  { step: "Provisioning runs", sub: "Dedicated VPS auto-provisioned" },
  { step: "Paste token & connect", sub: "Zero configuration required" },
];

export default function ComparisonSection() {
  return (
    <section id="comparison" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <span className="badge-pill mb-4 inline-block">Complexity Diff</span>
          <h2 className="mb-4 text-4xl font-bold text-foreground md:text-5xl">
            Skip the complexity
          </h2>
          <p className="text-lg text-muted-foreground">Traditional deployment vs ClawHost</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Traditional */}
          <div className="card-glass rounded-2xl border-border/50 p-6">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <div className="mb-1 text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  Traditional Deployment
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-red-400" />
                  <span className="text-2xl font-bold font-mono text-red-400">~60 min</span>
                </div>
              </div>
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-400/10">
                <X className="h-5 w-5 text-red-400" />
              </div>
            </div>
            <div className="space-y-3">
              {traditionalSteps.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between border-b border-border/30 py-2 last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-1.5 rounded-full bg-red-400/60" />
                    <span className="text-sm text-muted-foreground">{s.step}</span>
                  </div>
                  <span className="ml-2 shrink-0 text-xs font-mono text-red-400/80">{s.time}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ClawHost */}
          <div
            className="relative overflow-hidden rounded-2xl border p-6"
            style={{
              background: "linear-gradient(135deg, hsl(186 100% 10% / 0.4), hsl(220 100% 10% / 0.3))",
              borderColor: "hsl(186 100% 50% / 0.3)",
            }}
          >
            <div className="absolute inset-0 animate-shimmer" />
            <div className="relative">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <div className="mb-1 text-xs font-mono uppercase tracking-wider text-brand-cyan/80">
                    ClawHost Deployment
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-brand-cyan" />
                    <span className="text-2xl font-bold font-mono text-brand-cyan">&lt;1 min</span>
                  </div>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-brand-cyan/20 bg-brand-cyan/10">
                  <Check className="h-5 w-5 text-brand-cyan" />
                </div>
              </div>
              <div className="mb-6 space-y-4">
                {clawHostSteps.map((s, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-brand-cyan/40 bg-brand-cyan/20">
                      <span className="text-xs font-mono text-brand-cyan">{i + 1}</span>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-foreground">{s.step}</div>
                      <div className="text-xs text-muted-foreground">{s.sub}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-between border-t border-brand-cyan/20 py-3">
                <span className="text-sm font-mono text-muted-foreground">Time saved</span>
                <span className="text-sm font-bold font-mono text-brand-cyan">98% faster</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
