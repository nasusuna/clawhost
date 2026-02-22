"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { useState } from "react";

const plans = [
  {
    name: "Starter",
    price: { monthly: 9, yearly: 7 },
    desc: "Perfect for personal use",
    features: ["1 AI agent", "1 messaging channel", "99.9% uptime SLA", "Auto-updates", "Email support"],
    cta: "Get Started",
    highlight: false,
  },
  {
    name: "Pro",
    price: { monthly: 19, yearly: 15 },
    desc: "For power users",
    features: [
      "5 AI agents",
      "All messaging channels",
      "99.99% uptime SLA",
      "Auto-updates",
      "Priority support",
      "Custom commands",
      "Analytics dashboard",
    ],
    cta: "Start Free Trial",
    highlight: true,
  },
  {
    name: "Team",
    price: { monthly: 49, yearly: 39 },
    desc: "For teams & businesses",
    features: [
      "Unlimited AI agents",
      "All messaging channels",
      "99.99% uptime SLA",
      "Auto-updates",
      "Dedicated support",
      "Custom integrations",
      "Team management",
      "SSO & audit logs",
    ],
    cta: "Contact Sales",
    highlight: false,
  },
];

export default function PricingSection() {
  const [yearly, setYearly] = useState(false);

  return (
    <section id="pricing" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <span className="badge-pill mb-4 inline-block">Pricing</span>
          <h2 className="mb-4 text-4xl font-bold text-foreground md:text-5xl">
            Simple, transparent pricing
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">Start free. Scale as you grow.</p>

          <div className="inline-flex items-center gap-3 rounded-xl border border-border bg-secondary p-1">
            <button
              type="button"
              onClick={() => setYearly(false)}
              className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all ${
                !yearly ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setYearly(true)}
              className={`rounded-lg px-4 py-1.5 text-sm font-medium transition-all ${
                yearly ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"
              }`}
            >
              Yearly
              <span className="ml-1.5 text-xs text-brand-cyan">-20%</span>
            </button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan, i) => (
            <div
              key={i}
              className={`relative rounded-2xl p-6 transition-all duration-300 ${
                plan.highlight ? "border-2" : "card-glass"
              }`}
              style={
                plan.highlight
                  ? {
                      background: "linear-gradient(135deg, hsl(186 100% 10% / 0.5), hsl(220 100% 10% / 0.3))",
                      borderColor: "hsl(186 100% 50% / 0.5)",
                      boxShadow: "0 0 30px hsl(186 100% 50% / 0.1)",
                    }
                  : {}
              }
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="badge-pill px-3 py-1 text-xs font-semibold">Most Popular</span>
                </div>
              )}

              <div className="mb-6">
                <h3 className="mb-1 text-lg font-bold text-foreground">{plan.name}</h3>
                <p className="mb-4 text-sm text-muted-foreground">{plan.desc}</p>
                <div className="flex items-end gap-1">
                  <span className="text-4xl font-bold font-mono text-foreground">
                    ${yearly ? plan.price.yearly : plan.price.monthly}
                  </span>
                  <span className="mb-1 text-sm text-muted-foreground">/mo</span>
                </div>
              </div>

              <ul className="mb-6 space-y-2.5">
                {plan.features.map((feat, j) => (
                  <li key={j} className="flex items-center gap-2.5 text-sm text-muted-foreground">
                    <Check className="h-4 w-4 shrink-0 text-brand-cyan" />
                    {feat}
                  </li>
                ))}
              </ul>

              <Link
                href={plan.cta === "Contact Sales" ? "mailto:sales@clawhost.com" : "/dashboard/subscribe"}
                className={`flex w-full items-center justify-center rounded-xl py-3 text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98] ${
                  plan.highlight
                    ? "text-primary-foreground"
                    : "bg-secondary text-foreground hover:bg-accent"
                }`}
                style={plan.highlight ? { background: "var(--gradient-primary)" } : {}}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
