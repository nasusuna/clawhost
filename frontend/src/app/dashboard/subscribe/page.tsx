"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type Plan = { id: string; name: string; vcpu: number; memory_gb: number };

export default function SubscribePage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Plan[]>("/subscription/plans")
      .then(setPlans)
      .catch(() => setPlans([]));
  }, []);

  const handleSubscribe = async (planType: string) => {
    setError("");
    setLoading(planType);
    try {
      const base = typeof window !== "undefined" ? window.location.origin : "";
      const res = await api<{ checkout_url: string }>("/subscription/checkout", {
        method: "POST",
        body: {
          plan_type: planType,
          success_url: `${base}/dashboard?success=1`,
          cancel_url: `${base}/dashboard/subscribe?canceled=1`,
        },
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
        return;
      }
      setError("No checkout URL returned");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Checkout failed";
      const hint =
        message === "Failed to fetch"
          ? " Check that NEXT_PUBLIC_API_URL (Vercel) points to your Railway backend and CORS_ALLOWED_ORIGINS (Railway) includes this site’s origin."
          : "";
      setError(message + hint);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Choose a plan</h1>
      {error && (
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}
      <div className="grid gap-6 md:grid-cols-2">
        {plans.map((plan) => (
          <Card key={plan.id}>
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <p className="text-sm text-neutral-400">
                {plan.vcpu} vCPU, {plan.memory_gb} GB RAM
              </p>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => handleSubscribe(plan.id)}
                disabled={loading !== null}
              >
                {loading === plan.id ? "Redirecting…" : "Subscribe"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
