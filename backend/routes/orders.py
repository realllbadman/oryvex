"""Order routes — admin-contact flow (NO online payment).

POST /api/orders/  (TRAILING SLASH):
  - reject if age_confirmed is not true (400)
  - compute subtotal, shipping (free >= threshold, else flat; + freight region
    surcharge for international), and total
  - persist the order and fire both order emails via BackgroundTasks
"""
import json
import os

from backend.config import env_num

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Order
from backend.schemas import OrderCreate, OrderOut
from backend.services import email
from backend.services.coupons import validate_coupon

router = APIRouter()

MIN_ORDER = env_num("MIN_ORDER", "150")
FREE_SHIP_THRESHOLD = env_num("FREE_SHIP_THRESHOLD", "300")
INSURANCE_FEE = env_num("INSURANCE_FEE", "15")

# Selectable shipping methods: key -> (label, price). Prices are env-overridable.
SHIPPING_METHODS = {
    "free": ("Free Standard Shipping (business days)", 0.0),
    "priority": ("Priority Shipping — 2-3 business days",
                 env_num("SHIP_PRIORITY", "20")),
    "overnight": ("Overnight Shipping — next business day",
                  env_num("SHIP_OVERNIGHT", "60")),
}


# Flat international freight surcharge by region (added on top of shipping).
FREIGHT_REGIONS = {
    "domestic": 0.0, "us": 0.0, "canada": 100.0, "latam": 150.0,
    "europe": 175.0, "uk": 175.0, "asia": 200.0, "oceania": 250.0, "other": 250.0,
}


def resolve_shipping(method: str | None, subtotal: float):
    """Return (label, cost) for the chosen method, validated server-side.

    'free' is only honoured when the order qualifies (>= FREE_SHIP_THRESHOLD);
    otherwise it falls back to priority so free shipping can't be gamed.
    """
    key = (method or "priority").lower()
    if key not in SHIPPING_METHODS:
        key = "priority"
    if key == "free" and subtotal < FREE_SHIP_THRESHOLD:
        key = "priority"
    return SHIPPING_METHODS[key]


@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    payload: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if not payload.age_confirmed:
        raise HTTPException(
            status_code=400, detail="Age/research-use confirmation required"
        )
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order contains no items")

    subtotal = sum(i.unit_price * i.quantity for i in payload.items)

    if MIN_ORDER and subtotal < MIN_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum order is ${MIN_ORDER:,.0f}. Your subtotal is ${subtotal:,.2f}.",
        )

    # Re-validate any coupon server-side (never trust the client's discount).
    coupon = validate_coupon(db, payload.coupon_code or "", subtotal)
    discount = coupon["discount"] if coupon["valid"] else 0.0
    applied_code = coupon["code"] if coupon["valid"] else None

    insurance = INSURANCE_FEE if payload.insurance else 0.0
    freight = FREIGHT_REGIONS.get((payload.freight_region or "domestic").lower(), 0.0)
    if freight > 0:
        # International: freight IS the shipping — no domestic method fee on top.
        ship_label, shipping = "International shipping", 0.0
    else:
        ship_label, shipping = resolve_shipping(payload.shipping_method, subtotal)
    total = round(subtotal - discount + shipping + insurance + freight, 2)

    items = [i.model_dump() for i in payload.items]
    data = payload.model_dump()
    data["items"] = json.dumps(items)
    data["age_confirmed"] = 1 if payload.age_confirmed else 0
    data["coupon_code"] = applied_code
    data["discount"] = discount
    data["shipping_method"] = ship_label
    data["insurance"] = insurance
    data["total"] = total

    order = Order(**data)
    db.add(order)
    db.commit()
    db.refresh(order)

    customer = payload.model_dump()
    background_tasks.add_task(
        email.send_order_customer_confirmation, customer, items, total, shipping,
        discount, applied_code, insurance, ship_label, freight,
    )
    background_tasks.add_task(
        email.send_order_owner_notification, customer, items, total, shipping,
        discount, applied_code, insurance, ship_label, freight,
    )
    return order
