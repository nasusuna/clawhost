"use client";

import { Star } from "lucide-react";

const reviews = [
  {
    name: "Arjun Mehta",
    role: "Founder, ShopEasy",
    rating: 5,
    text: "OpenClaw replaced our entire support team overnight. Our Telegram bot handles 90% of queries automatically — and customers love it.",
    avatar: "AM",
  },
  {
    name: "Priya Sharma",
    role: "Community Lead, DevHub",
    rating: 5,
    text: "Deployed a Discord moderation bot in 47 seconds. No Docker, no config files. It just works. This is the future of AI deployment.",
    avatar: "PS",
  },
  {
    name: "Marcus Chen",
    role: "CTO, LearnFlow",
    rating: 5,
    text: "We built an AI tutor for our students using Claude Opus. The zero-config approach saved us weeks of DevOps work.",
    avatar: "MC",
  },
  {
    name: "Sofia Rodriguez",
    role: "E-Commerce Manager",
    rating: 5,
    text: "Our sales bot on Telegram increased conversions by 35%. OpenClaw made it ridiculously easy to set up and maintain.",
    avatar: "SR",
  },
];

export default function ReviewsSection() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <div className="mb-14 text-center">
          <div className="badge-pill mb-4 inline-flex items-center gap-2">
            ⭐ Customer Reviews
          </div>
          <h2 className="mb-4 text-4xl font-black text-foreground md:text-5xl">
            Loved by <span className="text-gradient">Thousands</span>
          </h2>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            See what our users say about deploying AI agents with OpenClaw.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {reviews.map((r) => (
            <div
              key={r.name}
              className="card-glass rounded-2xl p-6 transition-all duration-300 hover:border-brand-cyan/30"
            >
              <div className="mb-4 flex gap-1">
                {Array.from({ length: r.rating }).map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-brand-cyan text-brand-cyan" />
                ))}
              </div>
              <p className="mb-5 text-sm leading-relaxed text-foreground">
                &quot;{r.text}&quot;
              </p>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-cyan/15 text-sm font-bold text-brand-cyan">
                  {r.avatar}
                </div>
                <div>
                  <div className="text-sm font-semibold text-foreground">{r.name}</div>
                  <div className="text-xs text-muted-foreground">{r.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
