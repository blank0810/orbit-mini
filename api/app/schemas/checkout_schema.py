from typing import Literal

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    # A Literal makes an unknown plan a 422 from FastAPI before any Stripe call.
    plan: Literal["starter", "pro"]


class CheckoutResponse(BaseModel):
    checkout_url: str


class PlanRead(BaseModel):
    key: str
    display_name: str
    recommended: bool


class ChangePlanRequest(BaseModel):
    # Same closed set as checkout: the client names a plan, never a price.
    plan: Literal["starter", "pro"]


class ChangePlanResponse(BaseModel):
    plan_name: str
