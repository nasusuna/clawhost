"use client";

import Link from "next/link";
import { Check, Info } from "lucide-react";

const GEMINI_FLASH_LITE_TOOLTIP =
  "Our most cost-efficient multimodal model, offering the fastest performance for high-frequency, lightweight tasks. Gemini 2.5 Flash-Lite is best for high-volume classification, simple data extraction, and extremely low-latency applications where budget and speed are the primary constraints.";

type PlanFeature = string | { text: string; tooltip: string };

const plans: Array<{
  name: string;
  price: number;
  desc: string;
  features: PlanFeature[];
  cta: string;
  highlight: boolean;
}> = [
  {
    name: "Starter",
    price: 39.99,
    desc: "Perfect for personal use",
    features: [
      "1 AI agent",
      "1 messaging channel",
      "Telegram Bot ready",
      {
        text: "Pre configured 'Gemini 2.5 Flash-Lite'",
        tooltip: GEMINI_FLASH_LITE_TOOLTIP,
      },
      "99.9% uptime SLA",
      "Auto-updates",
      "Email support",
    ],
    cta: "Get Started",
    highlight: true,
  },
];

export default function PricingSection() {
  return (
    <section id="pricing" className="px-6 py-24">
      <div className="mx-auto max-w-5xl">
        <div className="mb-14 text-center">
          <span className="badge-pill mb-4 inline-block">Pricing</span>
          <h2 className="mb-4 text-4xl font-bold text-foreground md:text-5xl">
            Simple, transparent pricing
          </h2>
          <p className="mb-8 text-lg text-muted-foreground">Start free. Scale as you grow.</p>
        </div>

        <div className="mx-auto grid max-w-md grid-cols-1 gap-6">
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
                    ${plan.price.toFixed(2)}
                  </span>
                  <span className="mb-1 text-sm text-muted-foreground">/mo</span>
                </div>
              </div>

              <ul className="mb-6 space-y-2.5">
                {plan.features.map((feat, j) => {
                  const isWithTooltip = typeof feat === "object" && "text" in feat && "tooltip" in feat;
                  return (
                    <li key={j} className="flex items-center gap-2.5 text-sm text-muted-foreground">
                      <Check className="h-4 w-4 shrink-0 text-brand-cyan" />
                      {isWithTooltip ? (
                        <>
                          <span>{(feat as { text: string; tooltip: string }).text}</span>
                          <span
                            className="inline-flex shrink-0 cursor-help text-muted-foreground/80 hover:text-foreground"
                            title={(feat as { text: string; tooltip: string }).tooltip}
                            aria-label="More information"
                          >
                            <Info className="h-3.5 w-3.5" />
                          </span>
                        </>
                      ) : (
                        feat as string
                      )}
                    </li>
                  );
                })}
              </ul>

              <Link
                href={plan.cta === "Contact Sales" ? "mailto:sales@clawbolt.online" : "/dashboard/subscribe"}
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
