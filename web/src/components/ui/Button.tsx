"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
  loadingLabel?: string;
  children: ReactNode;
}

// min-h-11 is 44px: primary actions are thumb-sized on mobile (Fitts's Law), and well
// clear of the 24x24 minimum WCAG 2.2 AA sets for any target.
const BASE =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-6 " +
  "text-base font-semibold transition-colors disabled:cursor-not-allowed";

const VARIANTS: Record<Variant, string> = {
  // Disabled dims rather than fades to invisible: a disabled control still has to be
  // legible enough to explain why nothing happened.
  primary: "bg-accent text-on-accent hover:bg-accent/90 disabled:bg-accent/60",
  secondary:
    "border border-border bg-transparent text-text hover:bg-surface-2 disabled:text-text-3",
};

export function Button({
  variant = "primary",
  loading = false,
  loadingLabel,
  children,
  className = "",
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled === true || loading}
      aria-busy={loading || undefined}
      className={`${BASE} ${VARIANTS[variant]} ${className}`}
    >
      {loading ? <Spinner /> : null}
      {/* The label stays put while busy so the button keeps its width and the layout
          does not jump. The wait is masked, not hidden (Doherty Threshold). */}
      <span>{loading && loadingLabel ? loadingLabel : children}</span>
    </button>
  );
}

function Spinner() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" className="size-4 animate-spin">
      <circle
        cx="8"
        cy="8"
        r="6.5"
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.3"
        strokeWidth="2.5"
      />
      <path
        d="M8 1.5A6.5 6.5 0 0 1 14.5 8"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
