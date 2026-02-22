"use client";

import { Shield, Zap, Activity, Globe, Lock, RefreshCw } from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Deploy in 60 Seconds",
    desc: "No servers, no SSH, no config files. One-click deployment gets your AI agent live instantly.",
    accent: "brand-cyan",
  },
  {
    icon: Activity,
    title: "Autonomous Heartbeat",
    desc: "Your agent runs 24/7 with built-in health monitoring. Auto-restart on failure. Zero intervention.",
    accent: "brand-blue",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    desc: "End-to-end encrypted, isolated per-user containers. Your data never touches shared infrastructure.",
    accent: "brand-purple",
  },
  {
    icon: Globe,
    title: "Multi-Channel Ready",
    desc: "Connect to Telegram, Discord, WhatsApp and more. One agent, every platform.",
    accent: "brand-cyan",
  },
  {
    icon: Lock,
    title: "Your Keys, Your Control",
    desc: "Bring your own API keys or use ours. Full transparency, no lock-in.",
    accent: "brand-blue",
  },
  {
    icon: RefreshCw,
    title: "Auto-Updates",
    desc: "Always on the latest OpenClaw version. Security patches applied automatically.",
    accent: "brand-purple",
  },
];

const accentMap: Record<string, { color: string; bg: string; border: string }> = {
  "brand-cyan": {
    color: "hsl(186 100% 50%)",
    bg: "hsl(186 100% 50% / 0.1)",
    border: "hsl(186 100% 50% / 0.2)",
  },
  "brand-blue": {
    color: "hsl(220 100% 65%)",
    bg: "hsl(220 100% 65% / 0.1)",
    border: "hsl(220 100% 65% / 0.2)",
  },
  "brand-purple": {
    color: "hsl(265 80% 65%)",
    bg: "hsl(265 80% 65% / 0.1)",
    border: "hsl(265 80% 65% / 0.2)",
  },
};

export default function FeaturesSection() {
  return (
    <section id="features" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <span className="badge-pill mb-4 inline-block">Capability Matrix</span>
          <h2 className="mb-4 text-4xl font-bold text-foreground md:text-5xl">
            Built for <span className="text-gradient">autonomy</span>
          </h2>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            Your personal AI workforce, distilled into a single deployment.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => {
            const Icon = f.icon;
            const { color, bg, border } = accentMap[f.accent];
            return (
              <div
                key={i}
                className="card-glass group rounded-2xl p-6 transition-all duration-300 hover:border-brand-cyan/30"
              >
                <div
                  className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl transition-all duration-300 group-hover:scale-110"
                  style={{ background: bg, border: `1px solid ${border}` }}
                >
                  <Icon className="h-5 w-5" style={{ color }} />
                </div>
                <h3 className="mb-2 text-base font-semibold text-foreground">{f.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
