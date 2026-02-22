"use client";

import Link from "next/link";
import Navbar from "@/components/Navbar";
import DeployWidget from "@/components/DeployWidget";
import ComparisonSection from "@/components/ComparisonSection";
import FeaturesSection from "@/components/FeaturesSection";
import PricingSection from "@/components/PricingSection";
import FAQSection from "@/components/FAQSection";
import Footer from "@/components/Footer";
import { useAuth } from "@/components/AuthProvider";

const stats = [
  { label: "Deploy", value: "<60s" },
  { label: "Uptime", value: "99.9%" },
  { label: "Config", value: "0 lines" },
  { label: "Models", value: "8+" },
];

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />

      {/* Hero Section */}
      <section className="relative flex min-h-screen items-center pt-20">
        {/* Background */}
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20"
          style={{ backgroundImage: "url(/hero-bg.png)" }}
        />
        <div className="absolute inset-0 hero-gradient" />
        <div
          className="absolute inset-0"
          style={{
            background: "radial-gradient(ellipse at center top, hsl(186 100% 20% / 0.12) 0%, transparent 70%)",
          }}
        />

        <div className="relative mx-auto grid w-full max-w-6xl grid-cols-1 items-center gap-12 px-6 py-20 md:grid-cols-2">
          {/* Left: Text */}
          <div className="animate-fade-in">
            <div className="badge-pill mb-6 inline-flex items-center gap-2">
              <div className="dot-online h-1.5 w-1.5 rounded-full bg-green-400" />
              OpenClaw — AI Deployment Tool
            </div>

            <h1 className="mb-6 text-5xl font-black leading-[1.05] tracking-tight md:text-6xl lg:text-7xl">
              Deploy OpenClaw <span className="block text-gradient">Under 1 Minute.</span>
            </h1>

            <p className="mb-8 max-w-md text-lg leading-relaxed text-muted-foreground">
              Your 24/7 OpenClaw AI agent & assistant, live on Telegram in under 60 seconds. Deploy
              ClawdBot & MoltBot — no Docker, no VPS, no config.
            </p>

            {/* Stats row */}
            <div className="mb-8 flex flex-wrap gap-3">
              {stats.map((s, i) => (
                <div key={i} className="stat-card">
                  <div className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                    {s.label}
                  </div>
                  <div className="text-lg font-bold font-mono text-brand-cyan">{s.value}</div>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              {user ? (
                <Link
                  href="/dashboard"
                  className="rounded-xl px-6 py-3 font-semibold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98] glow-cyan"
                  style={{ background: "var(--gradient-primary)" }}
                >
                  Open Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/register"
                    className="rounded-xl px-6 py-3 font-semibold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98] glow-cyan"
                    style={{ background: "var(--gradient-primary)" }}
                  >
                    🚀 Deploy OpenClaw Now
                  </Link>
                  <Link
                    href="#features"
                    className="rounded-xl border border-border bg-secondary px-6 py-3 font-semibold text-foreground transition-all duration-200 hover:bg-accent"
                  >
                    View Demo
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Right: Deploy Widget */}
          <div className="flex animate-fade-in animate-float justify-center md:justify-end">
            <DeployWidget />
          </div>
        </div>

        {/* Bottom gradient fade */}
        <div
          className="absolute bottom-0 left-0 right-0 h-32"
          style={{ background: "linear-gradient(to bottom, transparent, hsl(222 47% 5%))" }}
        />
      </section>

      {/* Social proof strip */}
      <div className="border-y border-border/30 bg-secondary/20 px-6 py-8">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-8 text-center">
          {[
            { label: "Active Agents", value: "12,400+" },
            { label: "Messages Processed", value: "2.1M+" },
            { label: "Avg Deploy Time", value: "47 sec" },
            { label: "Customer Rating", value: "4.9 / 5" },
          ].map((s, i) => (
            <div key={i}>
              <div className="text-2xl font-bold font-mono text-foreground">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      <ComparisonSection />
      <FeaturesSection />
      <PricingSection />
      <FAQSection />

      {/* CTA Section */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-3xl text-center">
          <div
            className="relative overflow-hidden rounded-3xl border p-12"
            style={{
              background: "linear-gradient(135deg, hsl(186 100% 10% / 0.3), hsl(220 100% 10% / 0.2))",
              borderColor: "hsl(186 100% 50% / 0.25)",
            }}
          >
            <div className="absolute inset-0 animate-shimmer" />
            <div className="relative">
              <h2 className="mb-4 text-4xl font-black text-foreground md:text-5xl">
                Ready to deploy?
              </h2>
              <p className="mb-8 text-lg text-muted-foreground">
                Join thousands of users running their AI agents 24/7 with ClawHost.
              </p>
              {user ? (
                <Link
                  href="/dashboard"
                  className="inline-block rounded-xl px-8 py-4 text-lg font-bold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98] glow-cyan"
                  style={{ background: "var(--gradient-primary)" }}
                >
                  Open Dashboard
                </Link>
              ) : (
                <Link
                  href="/register"
                  className="inline-block rounded-xl px-8 py-4 text-lg font-bold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98] glow-cyan"
                  style={{ background: "var(--gradient-primary)" }}
                >
                  Start Free — Deploy in 60s
                </Link>
              )}
              <p className="mt-4 text-sm text-muted-foreground">
                3-day free trial · No credit card required
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
