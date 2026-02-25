"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Send, X, Check, Copy } from "lucide-react";
import PhoneMockup from "@/components/PhoneMockup";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

type TelegramStatus = { has_token: boolean };
type SnippetResponse = { config_fragment: Record<string, unknown> } | null;
type FullConfigInstance = { instance_id: string; domain: string | null; full_config: Record<string, unknown> };
type FullConfigResponse = { instances: FullConfigInstance[] } | null;
type Instance = { id: string; status: string };

export default function TelegramSetupPage() {
  const [token, setToken] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [hasToken, setHasToken] = useState<boolean | null>(null);
  const [snippet, setSnippet] = useState<SnippetResponse | null>(null);
  const [fullConfig, setFullConfig] = useState<FullConfigResponse | null>(null);
  const [instances, setInstances] = useState<Instance[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchStatus = useCallback(() => {
    api<TelegramStatus>("/user/telegram-token")
      .then((s) => setHasToken(s.has_token))
      .catch(() => setHasToken(false));
  }, []);

  useEffect(() => {
    fetchStatus();
    api<Instance[]>("/instances").then(setInstances).catch(() => setInstances([]));
  }, [fetchStatus]);

  useEffect(() => {
    if (hasToken) {
      api<SnippetResponse>("/user/telegram-config-snippet")
        .then((s) => setSnippet(s))
        .catch(() => setSnippet(null));
      api<FullConfigResponse>("/user/telegram-full-config")
        .then((r) => setFullConfig(r ?? null))
        .catch(() => setFullConfig(null));
    } else {
      setSnippet(null);
      setFullConfig(null);
    }
  }, [hasToken]);

  const handleSave = async () => {
    const raw = token.trim();
    if (!raw) return;
    setError(null);
    setSuccess(false);
    setSaving(true);
    try {
      await api<TelegramStatus>("/user/telegram-token", {
        method: "PUT",
        body: { bot_token: raw },
      });
      setSuccess(true);
      setHasToken(true);
      setToken("");
      const [sn, fc] = await Promise.all([
        api<SnippetResponse>("/user/telegram-config-snippet").catch(() => null),
        api<FullConfigResponse>("/user/telegram-full-config").catch(() => null),
      ]);
      setSnippet(sn ?? null);
      setFullConfig(fc ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save token");
    } finally {
      setSaving(false);
    }
  };

  const handleCopyFullConfig = (inst: FullConfigInstance) => {
    const text = JSON.stringify(inst.full_config, null, 2);
    navigator.clipboard.writeText(text);
    setCopiedId(inst.instance_id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const showFullConfig = (hasToken ?? false) && fullConfig?.instances?.length;
  const existingInstances = instances.filter((i) => i.status === "running");

  return (
    <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center p-4 md:p-8">
      <div className="glow-border relative w-full max-w-6xl overflow-hidden rounded-2xl bg-card">
        <Button
          variant="ghost"
          size="sm"
          className="absolute right-4 top-4 z-10 text-muted-foreground hover:text-foreground md:right-6 md:top-6"
          asChild
        >
          <Link href="/dashboard" aria-label="Back to dashboard">
            <X className="h-6 w-6" />
          </Link>
        </Button>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:gap-0">
          <div className="flex flex-col justify-center p-8 md:p-12 lg:p-16">
            <div className="mb-10 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary">
                <Send className="h-6 w-6 text-primary-foreground" />
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
                Connect Telegram
              </h1>
            </div>

            <div className="mb-6 rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-foreground">
              <p className="font-semibold mb-2">How it works</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li><strong className="text-foreground">Optional.</strong> You can skip this and use OpenClaw without Telegram.</li>
                <li><strong className="text-foreground">Save & Connect:</strong> we add Telegram to OpenClaw for you—for new instances (at provisioning) and for existing running instances (we update the config and restart the gateway automatically). You only need to open OpenClaw, then in Telegram DM your bot and approve the pairing code when prompted.</li>
                <li>If an existing instance did not update automatically, copy the <strong className="text-foreground">full config</strong> below for your instance and replace the entire OpenClaw config with it, then restart the gateway.</li>
              </ul>
            </div>

            <div className="space-y-8">
              <h2 className="text-lg font-semibold text-foreground">
                How to get your bot token?
              </h2>

              <ol className="space-y-5 text-secondary-foreground">
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">1.</span>
                  <span>
                    Open Telegram and go to{" "}
                    <a
                      href="https://t.me/BotFather"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-primary hover:underline"
                    >
                      @BotFather
                    </a>
                    .
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">2.</span>
                  <span>
                    Start a chat and type{" "}
                    <code className="rounded bg-muted px-2 py-0.5 text-sm text-foreground">
                      /newbot
                    </code>
                    .
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">3.</span>
                  <span>Follow the prompts to name your bot and choose a username.</span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">4.</span>
                  <span>
                    BotFather will send you a message with your bot token. Copy the entire token
                    (it looks like a long string of numbers and letters).
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="mt-0.5 font-mono text-sm text-muted-foreground">5.</span>
                  <span>Paste the token in the field below and click Save & Connect.</span>
                </li>
              </ol>

              <div className="space-y-3 pt-4">
                <label
                  htmlFor="telegram-token"
                  className="text-sm font-semibold text-foreground"
                >
                  Enter bot token
                </label>
                <input
                  id="telegram-token"
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="w-full rounded-lg border border-border bg-background px-4 py-3 font-mono text-sm text-foreground placeholder:text-muted-foreground transition-all focus:border-transparent focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              {error && (
                <p className="text-sm text-red-400">{error}</p>
              )}
              {success && (
                <p className="flex items-center gap-2 text-sm text-emerald-500">
                  <Check className="h-4 w-4" />
                  {existingInstances.length > 0
                    ? "Token saved. We're updating your existing instance(s) with Telegram; when done, open OpenClaw and approve pairing in Telegram."
                    : "Token saved. New instances will get Telegram pre-configured."}
                </p>
              )}

              <Button
                className="w-full gap-2"
                disabled={!token.trim() || saving}
                onClick={handleSave}
              >
                {saving ? "Saving…" : "Save & Connect ✓"}
              </Button>

              {showFullConfig && (
                <div className="space-y-3 rounded-lg border border-border bg-muted/30 p-4">
                  <p className="text-sm font-medium text-foreground">
                    Full config: copy and replace entire OpenClaw config
                  </p>
                  <p className="text-xs text-muted-foreground">
                    If an instance was not updated automatically, copy the full config for your instance below. In OpenClaw (Control UI or <code className="rounded bg-muted px-1">openclaw.json</code> on the server), replace the entire config with this JSON, then restart the gateway. See{" "}
                    <a
                      href="https://docs.openclaw.ai/channels/telegram"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      OpenClaw Telegram docs
                    </a>
                    .
                  </p>
                  {(fullConfig?.instances ?? []).map((inst) => (
                    <div key={inst.instance_id} className="space-y-2 rounded-lg border border-border bg-background p-3">
                      <p className="text-xs font-medium text-foreground">
                        Instance {inst.domain ? `(${inst.domain})` : ""}
                      </p>
                      <pre className="max-h-48 overflow-auto rounded bg-muted/50 p-3 text-xs font-mono text-foreground">
                        {JSON.stringify(inst.full_config, null, 2)}
                      </pre>
                      <Button
                        type="button"
                        variant="secondary"
                        size="sm"
                        className="gap-2"
                        onClick={() => handleCopyFullConfig(inst)}
                        aria-label={`Copy full config for ${inst.domain ?? inst.instance_id}`}
                      >
                        <Copy className="h-3.5 w-3.5" />
                        {copiedId === inst.instance_id ? "Copied" : "Copy full config"}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center bg-secondary/30 p-8 lg:p-12">
            <PhoneMockup />
          </div>
        </div>
      </div>
    </div>
  );
}
