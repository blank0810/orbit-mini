"use client";

import { Button } from "@/components/ui/Button";
import type { Plan } from "@/lib/types";

interface PlanCardProps {
  plan: Plan;
  price: string;
  cadence: string;
  blurb: string;
  features: string[];
  onSelect: () => void;
  selecting: boolean;
}

export function PlanCard({
  plan,
  price,
  cadence,
  blurb,
  features,
  onSelect,
  selecting,
}: PlanCardProps) {
  return (
    <div
      // The two plans are RANKED, not presented flat. Hick's Law is about the cost of an
      // unranked choice rather than the count: a recommended marker collapses a
      // comparison back into a yes/no.
      className={`relative flex h-full flex-col rounded-2xl border p-6 ${
        plan.recommended
          ? "border-accent bg-surface-2"
          : "border-border bg-surface"
      }`}
    >
      {plan.recommended ? (
        <span className="absolute -top-3 left-6 rounded-full bg-accent px-3 py-1 text-xs font-semibold tracking-wide text-on-accent">
          MOST POPULAR
        </span>
      ) : null}

      <h2 className="text-xl font-semibold">{plan.display_name}</h2>
      <p className="mt-1 text-sm text-text-2">{blurb}</p>

      <p className="mt-5 flex items-baseline gap-1">
        <span className="text-4xl font-bold tracking-tight">{price}</span>
        <span className="text-base text-text-3">{cadence}</span>
      </p>

      <ul className="mt-6 flex flex-1 flex-col gap-3 text-sm">
        {features.map((feature) => (
          <li key={feature} className="flex items-start gap-3">
            <CheckIcon />
            <span className="text-text-2">{feature}</span>
          </li>
        ))}
      </ul>

      <Button
        onClick={onSelect}
        loading={selecting}
        loadingLabel="Opening…"
        variant={plan.recommended ? "primary" : "secondary"}
        className="mt-7 w-full"
      >
        Choose {plan.display_name}
      </Button>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 16 16"
      className="mt-0.5 size-4 shrink-0 text-accent"
    >
      <path
        d="M3 8.5 6.2 11.7 13 5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
