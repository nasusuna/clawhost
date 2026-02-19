"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type Sub = { id: string; status: string; plan_type: string; current_period_end: string | null } | null;

export default function DashboardPage() {
  const [sub, setSub] = useState<Sub>(undefined as unknown as Sub);

  useEffect(() => {
    api<Sub>("/subscription/me").then(setSub).catch(() => setSub(null));
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
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
            <CardTitle>Instances</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-neutral-400 mb-4">View and manage your OpenClaw instances.</p>
            <Button asChild>
              <Link href="/dashboard/instances">View instances</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
