export type SubscriberStatus = "incomplete" | "active" | "past_due" | "canceled";

export interface Subscriber {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  plan_name: string;
  status: SubscriberStatus;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  full_name: string;
}

export interface Plan {
  key: "starter" | "pro";
  display_name: string;
  recommended: boolean;
}

export interface ApiError {
  detail: string;
}

export interface DemoAccount {
  email: string;
  password: string;
  full_name: string;
}
