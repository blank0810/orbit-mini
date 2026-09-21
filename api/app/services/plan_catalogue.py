from dataclasses import dataclass

from app.core.config import get_settings


class UnknownPlan(Exception):
    pass


@dataclass(frozen=True)
class Plan:
    key: str
    display_name: str
    product_id: str
    recommended: bool


# The client sends a plan KEY, never a price or product id. The server owns this mapping,
# so no caller can check out against an arbitrary price in the Stripe account.
PLAN_KEYS = ("starter", "pro")


def get_plans() -> dict[str, Plan]:
    settings = get_settings()
    # Pro is recommended so the UI ranks the options rather than showing two equal cards.
    return {
        "starter": Plan("starter", "ScaleSage Starter", settings.stripe_product_id_starter, False),
        "pro": Plan("pro", "ScaleSage Pro", settings.stripe_product_id_pro, True),
    }


def get_plan(key: str) -> Plan:
    if key not in PLAN_KEYS:
        raise UnknownPlan
    return get_plans()[key]
