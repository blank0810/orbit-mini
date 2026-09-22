import type { DemoAccount, Subscriber } from "@/lib/types";
import { api } from "./client";

export async function getMe(): Promise<Subscriber> {
  return api<Subscriber>("/subscribers/me");
}

export async function register(data: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}): Promise<Subscriber> {
  return api<Subscriber>("/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function login(
  email: string,
  password: string,
): Promise<Subscriber> {
  return api<Subscriber>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function logout(): Promise<void> {
  return api<void>("/auth/logout", { method: "POST" });
}

// Creates a throwaway demo account and signs you into it. The API sets the session cookie
// on this response, so no follow-up login call is needed.
export async function generateDemoAccount(): Promise<DemoAccount> {
  return api<DemoAccount>("/demo/generate", { method: "POST" });
}
