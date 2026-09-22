import type { Plan, Subscriber } from "@/lib/types";
import { api } from "./client";

export async function getPlans(): Promise<Plan[]> {
  return api<Plan[]>("/plans");
}

export async function startCheckout(
  plan: "starter" | "pro",
): Promise<{ checkout_url: string }> {
  return api<{ checkout_url: string }>("/checkout", {
    method: "POST",
    body: JSON.stringify({ plan }),
  });
}

// Moves a LIVE subscription between plans, prorated. Not the same as checking out again,
// which would open a second subscription and bill twice.
export async function changePlan(plan: "starter" | "pro"): Promise<{ plan_name: string }> {
  return api<{ plan_name: string }>("/subscription/change", {
    method: "POST",
    body: JSON.stringify({ plan }),
  });
}

// Ends at the end of the paid period, not immediately: the customer already bought the
// rest of this month.
export async function cancelSubscription(): Promise<Subscriber> {
  return api<Subscriber>("/subscription/cancel", { method: "POST" });
}

export async function resumeSubscription(): Promise<Subscriber> {
  return api<Subscriber>("/subscription/resume", { method: "POST" });
}
