"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { ApiError } from "@/lib/api/client";
import { generateDemoAccount, login } from "@/lib/api/subscribers";

const DEMO_EMAIL = "demo@orbit.ehnand.com";
const DEMO_PASSWORD = "orbit-demo-2026";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(undefined);
    setBusy(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (error) {
      setBusy(false);
      // The API returns the same message for an unknown email and a wrong password.
      // Nothing here narrows it down, or the endpoint stops being non-enumerable.
      setFormError(
        error instanceof ApiError
          ? error.message
          : "Something went wrong. Please try again.",
      );
    }
  }

  return (
    <div className="mx-auto w-full max-w-md px-6 pb-24 sm:px-8">
      <section className="py-10">
        <h1 className="text-3xl font-bold tracking-tight">Sign in</h1>
        <p className="mt-2 text-text-2">
          Your plan and billing status, in one place.
        </p>
      </section>

      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
        <Field
          id="email"
          label="Email"
          type="email"
          inputMode="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />
        <Field
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        {formError ? (
          <p
            role="alert"
            className="rounded-xl border border-danger/40 bg-surface p-3 text-sm text-danger"
          >
            {formError}
          </p>
        ) : null}

        <Button type="submit" loading={busy} loadingLabel="Signing in…" className="w-full">
          Sign in
        </Button>
      </form>

      <div className="mt-8 rounded-2xl border border-border bg-surface p-5">
        <p className="text-sm font-semibold">Just looking?</p>

        {/* The primary of the two: it creates a private account and lands you on a
            populated dashboard in one click, with nothing to type and nothing shared. */}
        <Button
          type="button"
          className="mt-4 w-full"
          loading={generating}
          loadingLabel="Creating…"
          onClick={async () => {
            setGenerating(true);
            setFormError(undefined);
            try {
              await generateDemoAccount();
              // The API set the session cookie on that response, so we are already signed in.
              router.push("/dashboard");
            } catch (error) {
              setGenerating(false);
              setFormError(
                error instanceof ApiError
                  ? error.message
                  : "Could not create a demo account. Please try again.",
              );
            }
          }}
        >
          Generate a demo account
        </Button>
        <p className="mt-2 text-xs text-text-3">
          A fresh subscriber, yours alone. Only five exist at a time, so the oldest is
          retired when a new one is made.
        </p>

        {/* Secondary: the shared account whose credentials are printed, for anyone who
            wants to sign in by hand or come back to the same data later. */}
        <Button
          type="button"
          variant="secondary"
          className="mt-5 w-full"
          onClick={() => {
            setEmail(DEMO_EMAIL);
            setPassword(DEMO_PASSWORD);
            setFormError(undefined);
          }}
        >
          Or use the shared demo account
        </Button>
        <p className="mt-3 font-mono text-xs text-text-3">
          {DEMO_EMAIL}
          <br />
          {DEMO_PASSWORD}
        </p>
      </div>

      <p className="mt-8 text-sm text-text-3">
        No account?{" "}
        <Link href="/" className="text-accent underline underline-offset-4">
          See pricing.
        </Link>
      </p>
    </div>
  );
}
