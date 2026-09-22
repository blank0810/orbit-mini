"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { PlanCard } from "@/components/pricing/PlanCard";
import { WalkthroughVideo } from "@/components/pricing/WalkthroughVideo";
import { Button } from "@/components/ui/Button";
import { getPlans } from "@/lib/api/payments";
import type { Plan } from "@/lib/types";

// Copy lives here rather than in the API: the API owns what a plan IS, the marketing
// page owns how it is sold. Amounts shown must match the Stripe prices.
const CONTENT: Record<
  Plan["key"],
  { price: string; cadence: string; blurb: string; features: string[] }
> = {
  starter: {
    price: "£597",
    cadence: "/mo",
    blurb: "For sole traders getting more leads without hiring.",
    features: [
      "Missed-call text-back",
      "Quote follow-up, automated",
      "Review system",
      "Your Orbit dashboard",
    ],
  },
  pro: {
    price: "£1,497",
    cadence: "/mo",
    blurb: "For established operators ready to scale without hiring.",
    features: [
      "Everything in Starter",
      "Voice AI answering 24/7",
      "LinkedIn and email outreach",
      "Monthly score review",
    ],
  },
};

export default function PricingPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<Plan[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [selecting, setSelecting] = useState<Plan["key"] | null>(null);

  useEffect(() => {
    let cancelled = false;
    // Resetting state lives in retry(), not here: setting state in an effect body is a
    // render-phase side effect, and React 19 lints against it.
    getPlans()
      .then((result) => {
        if (!cancelled) setPlans(result);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  const retry = useCallback(() => {
    setPlans(null);
    setFailed(false);
    setAttempt((n) => n + 1);
  }, []);

  const select = useCallback(
    (key: Plan["key"]) => {
      setSelecting(key);
      router.push(`/register?plan=${key}`);
    },
    [router],
  );

  // Recommended first in the DOM so mobile and screen readers meet the ranked choice
  // first; CSS order puts Starter back on the left from md, as on scalesage.ai.
  const ordered = plans
    ? [...plans].sort((a, b) => Number(b.recommended) - Number(a.recommended))
    : null;

  return (
    <div className="mx-auto w-full max-w-5xl px-6 pb-24 sm:px-8">
      <section className="py-10 sm:py-14">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Plug the <em className="italic text-accent">leak</em>.
        </h1>
        <p className="mt-4 max-w-xl text-lg text-text-2">
          ScaleSage finds where money, leads and hours are slipping out, then
          builds the systems that close them.
        </p>
      </section>

      {failed ? (
        <div className="flex flex-col items-start gap-4 rounded-2xl border border-border bg-surface p-6">
          <p role="alert" className="text-text-2">
            Plans could not be loaded.
          </p>
          <Button variant="secondary" onClick={retry}>
            Try again
          </Button>
        </div>
      ) : null}

      {!failed && !ordered ? (
        // Skeletons, never a blank screen: the wait is masked (Doherty Threshold).
        <div className="flex flex-col gap-6 md:flex-row md:items-stretch">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : null}

      {ordered ? (
        <div className="flex flex-col gap-6 md:flex-row md:items-stretch">
          {ordered.map((plan) => (
            <div
              key={plan.key}
              className={`flex-1 ${plan.recommended ? "md:order-2" : "md:order-1"}`}
            >
              <PlanCard
                plan={plan}
                {...CONTENT[plan.key]}
                selecting={selecting === plan.key}
                onSelect={() => select(plan.key)}
              />
            </div>
          ))}
        </div>
      ) : null}

      <WalkthroughVideo />

      <p className="mt-10 text-sm text-text-3">
        Already subscribed?{" "}
        <Link
          href="/login"
          className="text-accent underline underline-offset-4"
        >
          Sign in.
        </Link>
      </p>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="h-96 flex-1 animate-pulse rounded-2xl border border-border bg-surface" />
  );
}
