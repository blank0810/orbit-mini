"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { StatusBadge } from "@/components/dashboard/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ApiError } from "@/lib/api/client";
import { getMe, logout } from "@/lib/api/subscribers";
import type { Subscriber } from "@/lib/types";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(d);
}

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<Subscriber | null>(null);
  const [failed, setFailed] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((result) => {
        if (!cancelled) setMe(result);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 401) {
          router.replace("/login");
          return;
        }
        setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [router]);

  const signOut = useCallback(async () => {
    setSigningOut(true);
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  }, [router]);

  if (failed) {
    return (
      <div className="mx-auto w-full max-w-2xl px-6 py-16 sm:px-8">
        <p role="alert" className="text-text-2">
          Your dashboard could not be loaded.
        </p>
      </div>
    );
  }

  if (!me) {
    return (
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-6 py-16 sm:px-8">
        <div className="h-24 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-40 animate-pulse rounded-2xl border border-border bg-surface" />
        <div className="h-28 animate-pulse rounded-2xl border border-border bg-surface" />
      </div>
    );
  }

  const subscribed = me.status !== "incomplete";

  return (
    <div className="mx-auto w-full max-w-2xl px-6 pb-24 sm:px-8">
      {/* Three regions, chunked by purpose: who you are, what you have, what happens
          next. Grouping comes from spacing and fill rather than dividers. */}
      <section className="py-10">
        <h1 className="text-3xl font-bold tracking-tight">
          {me.first_name}&rsquo;s subscription
        </h1>
        <p className="mt-2 text-text-2">{me.email}</p>
      </section>

      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs tracking-widest text-text-3 uppercase">
              Plan
            </p>
            <p className="mt-2 text-2xl font-semibold">
              {subscribed ? me.plan_name : "No plan yet"}
            </p>
          </div>
          <StatusBadge status={me.status} />
        </div>

        <div className="mt-8 border-t border-border pt-6">
          <p className="font-mono text-xs tracking-widest text-text-3 uppercase">
            {me.status === "canceled" ? "Access until" : "Renews"}
          </p>
          <p className="mt-2 text-lg">{formatDate(me.current_period_end)}</p>
        </div>
      </Card>

      {/* One primary action per view. When there is no plan, the primary action is to
          choose one; otherwise the page is purely informational and sign-out is the
          only control, deliberately secondary. */}
      {!subscribed ? (
        <div className="mt-6">
          <Link href="/">
            <Button className="w-full sm:w-auto">Choose a plan</Button>
          </Link>
          <p className="mt-3 text-sm text-text-3">
            Your account exists but no payment has been recorded yet.
          </p>
        </div>
      ) : null}

      {me.status === "past_due" ? (
        <p
          role="alert"
          className="mt-6 rounded-2xl border border-warn/40 bg-surface p-5 text-sm text-warn"
        >
          A payment did not go through. Stripe will retry automatically.
        </p>
      ) : null}

      <div className="mt-10">
        <Button
          variant="secondary"
          onClick={signOut}
          loading={signingOut}
          loadingLabel="Signing out…"
        >
          Sign out
        </Button>
      </div>
    </div>
  );
}
