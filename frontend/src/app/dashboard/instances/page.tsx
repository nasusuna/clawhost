"use client";

import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type Instance = {
  id: string;
  status: string;
  domain: string | null;
  ip_address: string | null;
  gateway_token: string | null;
  created_at: string;
  last_heartbeat: string | null;
};

export default function InstancesPage() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyToken = useCallback((instanceId: string, token: string) => {
    navigator.clipboard.writeText(token);
    setCopiedId(instanceId);
    setTimeout(() => setCopiedId(null), 2000);
  }, []);

  const fetchInstances = useCallback(() => {
    api<Instance[]>("/instances")
      .then(setInstances)
      .catch(() => setInstances([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const handleRetryProvisioning = async (instanceId: string) => {
    setMessage(null);
    setRetryingId(instanceId);
    try {
      await api<{ ok: boolean; message: string }>(`/instances/${instanceId}/retry-provisioning`, {
        method: "POST",
      });
      setMessage("Job enqueued. Worker will process it shortly—refresh in a few minutes.");
      fetchInstances();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Instances</h1>
      {message && (
        <p className={message.startsWith("Job") ? "text-emerald-500 text-sm" : "text-red-500 text-sm"}>
          {message}
        </p>
      )}
      {loading && <p className="text-neutral-400">Loading…</p>}
      {!loading && instances.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-neutral-400">No instances yet. Subscribe to get your first OpenClaw instance.</p>
          </CardContent>
        </Card>
      )}
      {!loading && instances.length > 0 && (
        <div className="grid gap-4">
          {instances.map((inst) => (
            <Card key={inst.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base font-medium">{inst.domain ?? inst.id}</CardTitle>
                <span
                  className={
                    inst.status === "running"
                      ? "text-emerald-500"
                      : inst.status === "provisioning"
                      ? "text-amber-500"
                      : "text-neutral-400"
                  }
                >
                  {inst.status}
                </span>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-1 text-sm">
                  {inst.ip_address && (
                    <>
                      <dt className="text-neutral-400">IP</dt>
                      <dd>{inst.ip_address}</dd>
                    </>
                  )}
                  {inst.last_heartbeat && (
                    <>
                      <dt className="text-neutral-400">Last heartbeat</dt>
                      <dd>{new Date(inst.last_heartbeat).toLocaleString()}</dd>
                    </>
                  )}
                </dl>
                {inst.gateway_token && inst.status === "running" && (
                  <div className="mt-4 space-y-2">
                    <p className="text-sm text-neutral-400">
                      Paste this token in OpenClaw: Overview → Gateway Token, then click Connect.
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 truncate rounded bg-neutral-800 px-2 py-1.5 text-sm font-mono">
                        {inst.gateway_token}
                      </code>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleCopyToken(inst.id, inst.gateway_token!)}
                        aria-label="Copy gateway token"
                      >
                        {copiedId === inst.id ? "Copied" : "Copy"}
                      </Button>
                    </div>
                  </div>
                )}
                {(inst.domain || inst.ip_address) && inst.status === "running" && (
                  <div className="mt-4 flex flex-wrap gap-4">
                    {inst.gateway_token && (
                      <a
                        href={`${inst.domain ? `https://${inst.domain}` : `http://${inst.ip_address}`}/?token=${encodeURIComponent(inst.gateway_token)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block text-sm font-medium text-emerald-500 hover:underline"
                      >
                        Start OpenClaw →
                      </a>
                    )}
                    <a
                      href={inst.domain ? `https://${inst.domain}` : `http://${inst.ip_address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block text-sm text-neutral-400 hover:text-[var(--foreground)] hover:underline"
                    >
                      Open instance
                    </a>
                  </div>
                )}
                {(["provisioning", "stopped"].includes(inst.status?.toLowerCase() ?? "") && (
                  <Button
                    variant="secondary"
                    size="sm"
                    className="mt-4"
                    onClick={() => handleRetryProvisioning(inst.id)}
                    disabled={retryingId === inst.id}
                  >
                    {retryingId === inst.id ? "Retrying…" : "Retry provisioning"}
                  </Button>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
