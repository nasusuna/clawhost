"use client";

import { useId } from "react";

/**
 * ClawBolt logo — claw mark + wordmark, inspired by OpenClaw (openclaw.ai).
 * Minimal lobster/crab claw suggesting grip + speed.
 */
export const ClawBoltLogo = ({
  size = "md",
  showWordmark = true,
  className = "",
}: {
  size?: "sm" | "md" | "lg";
  showWordmark?: boolean;
  className?: string;
}) => {
  const id = useId();
  const sizes = {
    sm: { icon: 24, text: "text-lg", gap: "gap-1.5" },
    md: { icon: 32, text: "text-xl", gap: "gap-2" },
    lg: { icon: 48, text: "text-2xl", gap: "gap-3" },
  };
  const s = sizes[size];

  return (
    <span className={`inline-flex items-center ${s.gap} ${className}`}>
      {/* Claw mark: two pincers forming a C, inspired by crustacean claw */}
      <svg
        width={s.icon}
        height={s.icon}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <path
          d="M10 8c-2 2-4 8-4 12 0 4 2 8 6 10"
          stroke={`url(#claw-gradient-${id})`}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M22 8c2 2 4 8 4 12 0 4-2 8-6 10"
          stroke={`url(#claw-gradient-${id})`}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <defs>
          <linearGradient id={`claw-gradient-${id}`} x1="8" y1="8" x2="24" y2="24" gradientUnits="userSpaceOnUse">
            <stop stopColor="#34d399" />
            <stop offset="1" stopColor="#2dd4bf" />
          </linearGradient>
        </defs>
      </svg>
      {showWordmark && (
        <span className={`font-semibold tracking-tight ${s.text}`}>
          <span className="text-white">Claw</span>
          <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">
            Bolt
          </span>
        </span>
      )}
    </span>
  );
};
