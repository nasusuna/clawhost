"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type Sub = { id: string; status: string; plan_type: string; current_period_end: string | null } | null;

type InstanceUsage = {
  instance_id: string;
  domain: string | null;
  tokens_used: number;
  tokens_cap: number;
  period_end: string;
  over_limit: boolean;
};

type UsageResponse = { instances: InstanceUsage[] };

const formatTokens = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
};

export default function DashboardPage() {
  const [sub, setSub] = useState<Sub>(undefined as unknown as Sub);
  const [usage, setUsage] = useState<UsageResponse | undefined>(undefined);

  useEffect(() => {
    api<Sub>("/subscription/me").then(setSub).catch(() => setSub(null));
  }, []);

  useEffect(() => {
    api<UsageResponse>("/usage").then(setUsage).catch(() => setUsage({ instances: [] }));
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <Button
          variant="outline"
          size="sm"
          className="border-red-500/60 text-red-400 hover:bg-red-500/15 hover:text-red-300"
          asChild
        >
          <Link href="/dashboard/account" aria-label="Delete account">
            Delete account
          </Link>
        </Button>
      </div>
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Subscription</CardTitle>
          </CardHeader>
          <CardContent>
            {sub === undefined && <p className="text-neutral-400">Loading…</p>}
            {sub === null && (
              <p className="text-neutral-400">
                No active subscription. <Link href="/dashboard/subscribe" className="text-emerald-500 hover:underline">Subscribe</Link>
              </p>
            )}
            {sub && (
              <div className="space-y-2">
                <p><span className="text-neutral-400">Plan:</span> {sub.plan_type}</p>
                <p><span className="text-neutral-400">Status:</span> {sub.status}</p>
                {sub.current_period_end && <p><span className="text-neutral-400">Renews:</span> {new Date(sub.current_period_end).toLocaleDateString()}</p>}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Intance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-neutral-400 mb-4">View and manage your OpenClaw instances.</p>
            <Button asChild>
              <Link href="/dashboard/instances">View intance</Link>
            </Button>
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Account</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-neutral-400 mb-4">Manage your profile or permanently delete your account and all data.</p>
            <Button
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
              asChild
            >
              <Link href="/dashboard/account">Manage account & delete account</Link>
            </Button>
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Gemini token usage</CardTitle>
          </CardHeader>
          <CardContent>
            {usage === undefined && <p className="text-neutral-400">Loading…</p>}
            {usage && usage.instances.length === 0 && (
              <p className="text-neutral-400">No instances yet. Usage is shown per instance after provisioning.</p>
            )}
            {usage && usage.instances.length > 0 && (
              <div className="space-y-4">
                {usage.instances.map((inst) => {
                  const pct = Math.min(100, (inst.tokens_used / inst.tokens_cap) * 100);
                  const label = inst.domain || `Instance ${inst.instance_id.slice(0, 8)}`;
                  return (
                    <div key={inst.instance_id} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium text-neutral-300">{label}</span>
                        <span className="text-neutral-400">
                          {formatTokens(inst.tokens_used)} / {formatTokens(inst.tokens_cap)} tokens
                        </span>
                      </div>
                      <div
                        className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden"
                        role="progressbar"
                        aria-valuenow={inst.tokens_used}
                        aria-valuemin={0}
                        aria-valuemax={inst.tokens_cap}
                        aria-label={`Token usage for ${label}`}
                      >
                        <div
                          className={inst.over_limit ? "h-full bg-red-500" : "h-full bg-emerald-500"}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      {inst.over_limit && (
                        <p className="text-sm text-red-400">
                          Usage limit reached — API disabled until next period (resets {new Date(inst.period_end).toLocaleDateString()}).
                        </p>
                      )}
                      {!inst.over_limit && (
                        <p className="text-xs text-neutral-500">Resets {new Date(inst.period_end).toLocaleDateString()}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
