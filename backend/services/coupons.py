"""Coupon validation — shared by the /api/coupons/validate endpoint and the
order route so the discount is always computed the same way, server-side."""
from datetime import datetime

from backend.models import Coupon


def validate_coupon(db, code: str, subtotal: float) -> dict:
    """Validate a coupon against a subtotal.

    Returns a dict: {valid, code, discount, kind, value, message}. `discount`
    is 0.0 when invalid. Never raises — callers can trust the shape.
    """
    result = {"valid": False, "code": "", "discount": 0.0,
              "kind": None, "value": None, "message": "Enter a coupon code"}
    if not code:
        return result

    norm = code.strip().upper()
    coupon = db.query(Coupon).filter(Coupon.code == norm).first()

    if not coupon or not coupon.active:
        result["message"] = "That code isn't valid."
        return result
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        result["message"] = "That code has expired."
        return result
    if subtotal < (coupon.min_subtotal or 0):
        result["message"] = f"Requires a subtotal of at least ${coupon.min_subtotal:,.0f}."
        return result

    if coupon.kind == "fixed":
        discount = min(float(coupon.value), subtotal)
    else:  # percent
        discount = round(subtotal * float(coupon.value) / 100.0, 2)
    discount = max(0.0, min(discount, subtotal))

    label = (f"{coupon.value:g}% off" if coupon.kind == "percent"
             else f"${coupon.value:g} off")
    return {
        "valid": True, "code": norm, "discount": discount,
        "kind": coupon.kind, "value": coupon.value,
        "message": f"{norm} applied — {label}.",
    }
