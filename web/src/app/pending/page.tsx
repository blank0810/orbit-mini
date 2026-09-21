"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import { getMe } from "@/lib/api/subscribers";

// Stripe redirects here the instant payment succeeds, but the row only flips when the
// webhook lands. That gap is usually a second or two and occasionally much longer, so
// this screen polls rather than guessing. Doherty Threshold: the wait gets an explicit
// state, never a dead screen.
const POLL_MS = 2000;
const GIVE_UP_MS = 90_000;

function PendingView() {
  const router = useRouter();
  const [elapsed, setElapsed] = useState(0);
  const [gaveUp, setGaveUp] = useState(false);
  // Initialised inside the effect, not here: calling Date.now() during render is an
  // impure render-phase read, which React 19 lints against.
  const startedAt = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    startedAt.current ??= Date.now();

    async function poll() {
      if (cancelled) return;
      try {
        const me = await getMe();
        if (cancelled) return;
        if (me.status === "active" || me.status === "past_due") {
          router.replace("/dashboard");
          return;
        }
      } catch (error) {
        if (cancelled) return;
        // No session means the cookie never survived the round trip through Stripe.
        if (error instanceof ApiError && error.status === 401) {
          router.replace("/login");
          return;
        }
        // Any other failure is treated as transient and retried; the give-up timer
        // is what stops this running forever.
      }
      const waited = Date.now() - (startedAt.current ?? Date.now());
      setElapsed(waited);
      if (waited >= GIVE_UP_MS) {
        setGaveUp(true);
        return;
      }
      timer = setTimeout(poll, POLL_MS);
    }

    timer = setTimeout(poll, 600);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [router]);

  return (
    <div className="mx-auto flex w-full max-w-md flex-col px-6 py-16 sm:px-8">
      {gaveUp ? (
        <>
          <h1 className="text-3xl font-bold tracking-tight">
            Still confirming
          </h1>
          <p className="mt-3 text-text-2">
            Your payment went through. Stripe has not confirmed it to us yet,
            which occasionally takes a few minutes. Your dashboard will update
            on its own.
          </p>
          <Link href="/dashboard" className="mt-8">
            <Button className="w-full">Go to dashboard</Button>
          </Link>
        </>
      ) : (
        <>
          <div
            role="status"
            aria-live="polite"
            className="flex items-center gap-3"
          >
            <span className="size-2.5 animate-pulse rounded-full bg-accent" />
            <h1 className="text-3xl font-bold tracking-tight">
              Confirming your payment
            </h1>
          </div>
          <p className="mt-3 text-text-2">
            Stripe is telling us the payment cleared. This usually takes a
            couple of seconds.
          </p>
          {/* Skeleton of the dashboard that is about to appear, so the wait reads as
              progress toward something rather than an empty screen. */}
          <div className="mt-10 flex flex-col gap-4">
            <div className="h-24 animate-pulse rounded-2xl border border-border bg-surface" />
            <div className="h-36 animate-pulse rounded-2xl border border-border bg-surface" />
          </div>
          {elapsed > 12_000 ? (
            <p className="mt-6 text-sm text-text-3">
              Taking longer than usual. Still waiting.
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}

export default function PendingPage() {
  return (
    <Suspense fallback={null}>
      <PendingView />
    </Suspense>
  );
}
