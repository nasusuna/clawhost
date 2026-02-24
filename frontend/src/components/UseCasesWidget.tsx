"use client";

import Link from "next/link";
import { Bot, HeadphonesIcon, ShoppingCart, GraduationCap, BarChart3, Users } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";

const useCases = [
  { icon: Bot, title: "AI Chat Assistant", desc: "24/7 smart support on Telegram & Discord", color: "hsl(186 100% 50%)" },
  { icon: HeadphonesIcon, title: "Customer Support", desc: "Automate FAQs & ticket resolution", color: "hsl(265 80% 65%)" },
  { icon: ShoppingCart, title: "E-Commerce Agent", desc: "Product recs, orders & tracking", color: "hsl(142 70% 50%)" },
  { icon: GraduationCap, title: "Education Tutor", desc: "Personalized learning assistant", color: "hsl(45 100% 55%)" },
  { icon: BarChart3, title: "Data Analyst", desc: "Query data & generate reports", color: "hsl(220 100% 65%)" },
  { icon: Users, title: "Community Manager", desc: "Moderate & engage your community", color: "hsl(340 80% 60%)" },
];

export default function UseCasesWidget() {
  const { user } = useAuth();

  return (
    <div className="card-glass w-full max-w-md rounded-2xl p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="dot-online h-2 w-2 rounded-full bg-green-400" />
        <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Popular Use Cases</span>
      </div>

      <div className="grid grid-cols-1 gap-2.5">
        {useCases.map((uc) => (
          <div
            key={uc.title}
            className="group flex cursor-default items-center gap-3 rounded-lg border border-border px-3 py-2.5 transition-all duration-200 hover:border-opacity-60"
          >
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors"
              style={{ background: `${uc.color.replace(")", " / 0.15)")}`, boxShadow: `0 0 12px ${uc.color.replace(")", " / 0.2)")}` }}
            >
              <uc.icon className="h-4 w-4" style={{ color: uc.color }} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-foreground">{uc.title}</div>
              <div className="text-xs text-muted-foreground">{uc.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <Link
        href={user ? "/dashboard/subscribe" : "/register"}
        className="mt-5 flex w-full items-center justify-center rounded-xl py-3.5 text-sm font-semibold text-primary-foreground transition-all duration-200 hover:scale-[1.02] hover:opacity-90 active:scale-[0.98]"
        style={{ background: "var(--gradient-primary)" }}
      >
        {user ? "Subscribe" : "Deploy Your Agent Now"}
      </Link>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        No code required · Deploy in under 60 seconds
      </p>
    </div>
  );
}
