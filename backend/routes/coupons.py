"""Public coupon endpoint — validate a code against a subtotal.

GET /api/coupons/validate?code=RESEARCH20&subtotal=120
Returns the same shape as backend.services.coupons.validate_coupon.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.coupons import validate_coupon

router = APIRouter()


@router.get("/validate")
def validate(
    code: str = Query(""),
    subtotal: float = Query(0.0),
    db: Session = Depends(get_db),
):
    return validate_coupon(db, code, subtotal)
