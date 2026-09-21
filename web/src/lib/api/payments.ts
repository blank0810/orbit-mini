import type { Plan } from "@/lib/types";
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
