"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { ApiError } from "@/lib/api/client";
import { startCheckout } from "@/lib/api/payments";
import { register } from "@/lib/api/subscribers";
import type { Plan } from "@/lib/types";

const PLAN_LABEL: Record<Plan["key"], string> = {
  starter: "ScaleSage Starter, £597/mo",
  pro: "ScaleSage Pro, £1,497/mo",
};

function RegisterForm() {
  const params = useSearchParams();
  // The query string is user-controlled, so it is narrowed to the closed set rather
  // than trusted. The API validates again; this only keeps the label honest.
  const plan: Plan["key"] = params.get("plan") === "pro" ? "pro" : "starter";

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState<string | undefined>();
  const [passwordError, setPasswordError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEmailError(undefined);
    setPasswordError(undefined);
    setFormError(undefined);
    setBusy(true);

    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email,
        password,
      });
      const { checkout_url } = await startCheckout(plan);
      // Busy stays true through the redirect on purpose: clearing it would flash an
      // idle button for the moment before the browser leaves the page.
      window.location.href = checkout_url;
    } catch (error) {
      setBusy(false);
      if (error instanceof ApiError) {
        if (error.status === 409) {
          setEmailError("That email already has an account.");
          return;
        }
        if (error.status === 422) {
          setPasswordError("Check your details and try again.");
          return;
        }
        setFormError(error.message);
        return;
      }
      setFormError("Something went wrong. Please try again.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-md px-6 pb-24 sm:px-8">
      <section className="py-10">
        <h1 className="text-3xl font-bold tracking-tight">
          Create your account
        </h1>
        <p className="mt-2 text-text-2">
          You are subscribing to{" "}
          <span className="text-text">{PLAN_LABEL[plan]}</span>.
        </p>
      </section>

      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-5">
        <div className="flex flex-col gap-5 sm:flex-row">
          <div className="flex-1">
            <Field
              id="first_name"
              label="First name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              autoComplete="given-name"
              required
            />
          </div>
          <div className="flex-1">
            <Field
              id="last_name"
              label="Last name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              autoComplete="family-name"
              required
            />
          </div>
        </div>

        <Field
          id="email"
          label="Email"
          type="email"
          inputMode="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          error={emailError}
          required
        />

        <Field
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
          // Stated up front, never revealed only on failure. Nielsen error prevention.
          hint="At least 8 characters."
          error={passwordError}
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

        <Button
          type="submit"
          loading={busy}
          loadingLabel="Taking you to Stripe…"
          className="w-full"
        >
          Continue to payment
        </Button>
      </form>

      <p className="mt-8 text-sm text-text-3">
        Already have an account?{" "}
        <Link href="/login" className="text-accent underline underline-offset-4">
          Sign in.
        </Link>
      </p>
    </div>
  );
}

export default function RegisterPage() {
  // useSearchParams needs a Suspense boundary, or the production build fails while
  // prerendering this route.
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}
