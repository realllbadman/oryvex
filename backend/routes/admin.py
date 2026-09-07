"""Admin API — HTTP Basic Auth on every route.

  GET    /stats
  GET    /orders            GET /orders/{id}   PATCH /orders/{id}   DELETE /orders/{id}
  GET    /bookings          GET /bookings/{id} PATCH /bookings/{id} DELETE /bookings/{id}
  GET    /products
  POST   /products/{slug}/coa   (multipart: file + coa_lab + purity)
"""
import json
import os
import secrets
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Booking, Coupon, Order, Product, Review
from backend.schemas import (BookingOut, BookingUpdate, CouponCreate,
                             CouponOut, CouponUpdate, OrderOut, OrderUpdate,
                             ReviewOut, ReviewUpdate)

router = APIRouter()
security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")

COA_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "coa"
ALLOWED_COA_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
}


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    user_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# ─── Stats ───────────────────────────────────────────────────────
@router.get("/stats")
def stats(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    return {
        "total_orders": db.query(Order).count(),
        "pending_orders": db.query(Order).filter(Order.status == "pending").count(),
        "orders_this_month": db.query(Order)
        .filter(Order.created_at >= month_start).count(),
        "total_bookings": db.query(Booking).count(),
        "pending_bookings": db.query(Booking)
        .filter(Booking.status == "pending").count(),
    }


# ─── Orders ──────────────────────────────────────────────────────
@router.get("/orders", response_model=list[OrderOut])
def list_orders(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.created_at.desc()).all()


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, _: str = Depends(require_admin),
              db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderUpdate,
                 _: str = Depends(require_admin), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


@router.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, _: str = Depends(require_admin),
                 db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()


# ─── Bookings / inquiries ────────────────────────────────────────
@router.get("/bookings", response_model=list[BookingOut])
def list_bookings(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Booking).order_by(Booking.created_at.desc()).all()


@router.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, _: str = Depends(require_admin),
                db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.patch("/bookings/{booking_id}", response_model=BookingOut)
def update_booking(booking_id: int, payload: BookingUpdate,
                   _: str = Depends(require_admin), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: int, _: str = Depends(require_admin),
                   db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()


# ─── Products + COA management ───────────────────────────────────
def _product_dict(p: Product) -> dict:
    return {
        "id": p.id, "slug": p.slug, "name": p.name, "category": p.category,
        "purity": p.purity, "price": p.price, "in_stock": bool(p.in_stock),
        "badge": p.badge, "coa_file": p.coa_file, "coa_lab": p.coa_lab,
    }


@router.get("/products")
def list_products(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return [_product_dict(p) for p in db.query(Product).order_by(Product.name).all()]


@router.post("/products/{slug}/coa")
async def upload_coa(
    slug: str,
    file: UploadFile = File(None),
    coa_lab: str = Form(None),
    purity: str = Form(None),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Text fields (lab name / purity) can be updated with or without a file.
    if coa_lab is not None:
        product.coa_lab = coa_lab or None
    if purity is not None:
        product.purity = purity or None

    if file is not None and file.filename:
        ext = ALLOWED_COA_TYPES.get((file.content_type or "").lower())
        if not ext:
            raise HTTPException(
                status_code=400,
                detail="COA must be a PDF, PNG, JPG, or WEBP file",
            )
        COA_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"{slug}-{uuid.uuid4().hex[:8]}{ext}"
        dest = COA_DIR / fname
        with dest.open("wb") as out:
            out.write(await file.read())
        product.coa_file = f"/static/coa/{fname}"

    db.commit()
    db.refresh(product)
    return _product_dict(product)


@router.delete("/products/{slug}/coa")
def remove_coa(
    slug: str,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove a product's COA — clears the link, the lab name, and deletes the
    uploaded file from disk. Product reverts to 'COA pending'."""
    product = db.query(Product).filter(Product.slug == slug).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old = product.coa_file
    product.coa_file = None
    product.coa_lab = None
    db.commit()

    # best-effort delete of the file on disk (only inside static/coa/)
    if old and old.startswith("/static/coa/"):
        f = COA_DIR / Path(old).name
        try:
            if f.resolve().parent == COA_DIR.resolve() and f.exists():
                f.unlink()
        except OSError:
            pass

    db.refresh(product)
    return _product_dict(product)


# ─── Coupons ─────────────────────────────────────────────────────
@router.get("/coupons", response_model=list[CouponOut])
def list_coupons(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("/coupons", response_model=CouponOut, status_code=201)
def create_coupon(payload: CouponCreate, _: str = Depends(require_admin),
                  db: Session = Depends(get_db)):
    code = payload.code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    data = payload.model_dump()
    data["code"] = code
    data["active"] = 1 if payload.active else 0
    coupon = Coupon(**data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.patch("/coupons/{coupon_id}", response_model=CouponOut)
def update_coupon(coupon_id: int, payload: CouponUpdate,
                  _: str = Depends(require_admin), db: Session = Depends(get_db)):
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "active":
            value = 1 if value else 0
        setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/coupons/{coupon_id}", status_code=204)
def delete_coupon(coupon_id: int, _: str = Depends(require_admin),
                  db: Session = Depends(get_db)):
    coupon = db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(coupon)
    db.commit()


# ─── Reviews (moderation) ────────────────────────────────────────
@router.get("/reviews", response_model=list[ReviewOut])
def list_reviews(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Review).order_by(Review.created_at.desc()).all()


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, payload: ReviewUpdate,
                  _: str = Depends(require_admin), db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if payload.approved is not None:
        review.approved = 1 if payload.approved else 0
    db.commit()
    db.refresh(review)
    return review


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(review_id: int, _: str = Depends(require_admin),
                  db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(review)
    db.commit()
