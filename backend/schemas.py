"""Pydantic v2 schemas for orders and bookings."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ─── Orders ──────────────────────────────────────────────────────
class OrderItem(BaseModel):
    product_id: int
    name: str
    strength: Optional[str] = None
    unit_price: float
    quantity: int


class OrderCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str
    company: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    freight_region: Optional[str] = None

    contact_pref: Optional[str] = None
    best_time: Optional[str] = None
    notes: Optional[str] = None

    items: List[OrderItem]
    total: float
    coupon_code: Optional[str] = None
    payment_method: Optional[str] = None
    shipping_method: Optional[str] = None
    insurance: bool = False
    age_confirmed: bool = False


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    phone: str
    email: str
    company: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    freight_region: Optional[str] = None
    contact_pref: Optional[str] = None
    best_time: Optional[str] = None
    notes: Optional[str] = None
    items: str
    total: float
    status: str
    coupon_code: Optional[str] = None
    discount: float = 0.0
    payment_method: Optional[str] = None
    shipping_method: Optional[str] = None
    insurance: float = 0.0
    age_confirmed: int
    created_at: datetime


# ─── Bookings / inquiries ────────────────────────────────────────
class BookingCreate(BaseModel):
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: str
    service: str = "General Inquiry"
    product_interest: Optional[str] = None
    details: Optional[str] = None


class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: str
    service: str
    product_interest: Optional[str] = None
    details: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime


# ─── Coupons ─────────────────────────────────────────────────────
class CouponCreate(BaseModel):
    code: str
    kind: str = "percent"          # "percent" | "fixed"
    value: float
    active: bool = True
    min_subtotal: float = 0.0
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class CouponUpdate(BaseModel):
    kind: Optional[str] = None
    value: Optional[float] = None
    active: Optional[bool] = None
    min_subtotal: Optional[float] = None
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    kind: str
    value: float
    active: int
    min_subtotal: float
    expires_at: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime


# ─── Reviews ─────────────────────────────────────────────────────
class ReviewCreate(BaseModel):
    product_slug: str
    name: str
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def _rating_range(cls, v):
        if v < 1 or v > 5:
            raise ValueError("rating must be 1-5")
        return v


class ReviewUpdate(BaseModel):
    approved: Optional[bool] = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_slug: str
    name: str
    rating: int
    title: Optional[str] = None
    body: Optional[str] = None
    approved: int
    created_at: datetime
