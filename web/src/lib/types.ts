export type SubscriberStatus = "incomplete" | "active" | "past_due" | "canceled";

export interface Subscriber {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  plan_name: string;
  status: SubscriberStatus;
  current_period_end: string | null;
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
