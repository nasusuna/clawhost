"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Send, ArrowRight, ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type Plan = { id: string; name: string; vcpu: number; memory_gb: number };

type Sub = { id: string; status: string; plan_type: string; current_period_end: string | null } | null;

type TelegramStatus = { has_token: boolean };

const ONBOARDING_STEP_TELEGRAM = 1;
const ONBOARDING_STEP_PAYMENT = 2;

export default function SubscribePage() {
  const [step, setStep] = useState(ONBOARDING_STEP_TELEGRAM);
  const [telegramToken, setTelegramToken] = useState("");
  const [telegramSaving, setTelegramSaving] = useState(false);
  const [telegramError, setTelegramError] = useState<string | null>(null);
  const [telegramSuccess, setTelegramSuccess] = useState(false);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [sub, setSub] = useState<Sub>(undefined as unknown as Sub);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Plan[]>("/subscription/plans")
      .then((all) => setPlans(all.filter((p) => p.id === "starter")))
      .catch(() => setPlans([]));
  }, []);

  useEffect(() => {
    api<Sub>("/subscription/me").then(setSub).catch(() => setSub(null));
  }, []);

  const isActiveSub = sub && sub.status === "active";

  useEffect(() => {
    if (isActiveSub && step === ONBOARDING_STEP_TELEGRAM) {
      setStep(ONBOARDING_STEP_PAYMENT);
    }
  }, [isActiveSub, step]);

  const handleSaveTelegram = async () => {
    const raw = telegramToken.trim();
    if (!raw) return;
    setTelegramError(null);
    setTelegramSuccess(false);
    setTelegramSaving(true);
    try {
      await api<TelegramStatus>("/user/telegram-token", {
        method: "PUT",
        body: { bot_token: raw },
      });
      setTelegramSuccess(true);
      setTelegramToken("");
    } catch (e) {
      setTelegramError(e instanceof Error ? e.message : "Failed to save token");
    } finally {
      setTelegramSaving(false);
    }
  };

  const handleContinueToPayment = () => {
    setStep(ONBOARDING_STEP_PAYMENT);
  };

  const handleBackToTelegram = () => {
    setStep(ONBOARDING_STEP_TELEGRAM);
  };

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
          ? " Check that NEXT_PUBLIC_API_URL (Vercel) points to your Railway backend and CORS_ALLOWED_ORIGINS (Railway) includes this site's origin."
          : "";
      setError(message + hint);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Step {step} of 2</span>
        <span aria-hidden>·</span>
        <span>{step === ONBOARDING_STEP_TELEGRAM ? "Telegram (optional)" : "Payment"}</span>
      </div>

      {step === ONBOARDING_STEP_TELEGRAM && (
        <>
          <h1 className="text-2xl font-semibold">Connect Telegram (optional)</h1>
          <p className="text-muted-foreground">
            Add your Telegram bot token now and we&apos;ll connect OpenClaw to Telegram for you when your instance is ready.
            If you skip, you can set it up manually later from the{" "}
            <Link href="/dashboard/telegram-setup" className="text-primary hover:underline font-medium">
              Telegram Setup
            </Link>{" "}
            page in the dashboard.
          </p>
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Send className="h-5 w-5" />
                Telegram bot token
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Get a token from @BotFather in Telegram (<code className="rounded bg-muted px-1">/newbot</code>), then paste it below.
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              <input
                id="onboarding-telegram-token"
                type="text"
                value={telegramToken}
                onChange={(e) => setTelegramToken(e.target.value)}
                placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                className="w-full rounded-lg border border-border bg-background px-4 py-3 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:border-transparent focus:outline-none focus:ring-2 focus:ring-ring"
                aria-label="Telegram bot token"
              />
              {telegramError && (
                <p className="text-sm text-red-400">{telegramError}</p>
              )}
              {telegramSuccess && (
                <p className="text-sm text-emerald-500">Token saved. You can continue to payment.</p>
              )}
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleSaveTelegram}
                  disabled={!telegramToken.trim() || telegramSaving}
                  variant="secondary"
                >
                  {telegramSaving ? "Saving…" : "Save token"}
                </Button>
                <Button onClick={handleContinueToPayment} className="gap-2">
                  Continue to payment
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {step === ONBOARDING_STEP_PAYMENT && (
        <>
          <h1 className="text-2xl font-semibold">Choose a plan</h1>
          {error && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}
          <div className="flex gap-4">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleBackToTelegram}
              className="gap-2 text-muted-foreground"
              aria-label="Back to Telegram step"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          </div>
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
                  {isActiveSub ? (
                    <Button disabled variant="secondary">
                      Active
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={loading !== null}
                    >
                      {loading === plan.id ? "Redirecting…" : "Subscribe"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
