"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/components/AuthProvider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

const CONFIRM_PLACEHOLDER = "Type your email to confirm";

export default function AccountPage() {
  const { user, logout } = useAuth();
  const [confirmValue, setConfirmValue] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  const email = user?.email ?? "";
  const confirmMatches = confirmValue.trim().toLowerCase() === email.toLowerCase();
  const canDelete = confirmMatches && !isDeleting;

  const handleDeleteClick = () => {
    setShowConfirm(true);
    setError(null);
    setConfirmValue("");
  };

  const handleCancelConfirm = () => {
    setShowConfirm(false);
    setConfirmValue("");
    setError(null);
  };

  const handleDeleteAccount = async () => {
    if (!canDelete) return;
    setError(null);
    setIsDeleting(true);
    try {
      await api<{ ok: boolean }>("/auth/account", { method: "DELETE" });
      logout();
      if (typeof window !== "undefined") {
        window.location.href = "/";
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete account");
      setIsDeleting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") handleCancelConfirm();
  };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Account</h1>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-neutral-400">
            <span className="text-[var(--foreground)]">Email:</span> {email}
          </p>
          <p className="text-sm text-neutral-500">
            To change your email or password, log out and register again with the new credentials.
          </p>
        </CardContent>
      </Card>

      <Card className="border-red-500/30">
        <CardHeader>
          <CardTitle className="text-red-400">Danger zone</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-neutral-400">
            Permanently delete your account and all associated data (subscriptions, instances, usage).
            Your Stripe subscription will be canceled and any provisioned VPS will be canceled. This cannot be undone.
          </p>
          {!showConfirm ? (
            <Button
              type="button"
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300"
              onClick={handleDeleteClick}
              aria-label="Open delete account confirmation"
            >
              Delete account
            </Button>
          ) : (
            <div className="space-y-3 rounded-lg border border-red-500/30 bg-red-500/5 p-4" onKeyDown={handleKeyDown}>
              <label htmlFor="delete-confirm" className="block text-sm font-medium text-[var(--foreground)]">
                To confirm, type your email: <span className="font-semibold">{email}</span>
              </label>
              <input
                id="delete-confirm"
                type="text"
                autoComplete="off"
                placeholder={CONFIRM_PLACEHOLDER}
                value={confirmValue}
                onChange={(e) => setConfirmValue(e.target.value)}
                className="w-full max-w-md rounded-md border border-[var(--muted)] bg-[var(--background)] px-3 py-2 text-sm text-[var(--foreground)] placeholder:text-neutral-500 focus:border-red-500/50 focus:outline-none focus:ring-1 focus:ring-red-500/50"
                aria-label="Confirm account deletion by typing your email"
                disabled={isDeleting}
              />
              {error && <p className="text-sm text-red-400" role="alert">{error}</p>}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCancelConfirm}
                  disabled={isDeleting}
                  aria-label="Cancel account deletion"
                >
                  Cancel
                </Button>
                <Button
                  type="button"
                  variant="default"
                  className="bg-red-600 hover:bg-red-700"
                  onClick={handleDeleteAccount}
                  disabled={!canDelete}
                  aria-label="Permanently delete my account"
                >
                  {isDeleting ? "Deleting…" : "Permanently delete my account"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-sm text-neutral-500">
        <Link href="/dashboard" className="text-emerald-500 hover:underline">
          Back to dashboard
        </Link>
      </p>
    </div>
  );
}
