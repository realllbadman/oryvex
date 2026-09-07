"""Public review endpoints.

POST /api/reviews/          → submit a review (held for admin approval)
GET  /api/reviews/{slug}    → approved reviews for a product + rating summary
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Review
from backend.schemas import ReviewCreate, ReviewOut

router = APIRouter()


@router.post("/", response_model=ReviewOut, status_code=201)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    review = Review(
        product_slug=payload.product_slug.strip(),
        name=name[:60],
        rating=payload.rating,
        title=(payload.title or "").strip()[:120] or None,
        body=(payload.body or "").strip()[:2000] or None,
        approved=0,   # moderated: hidden until the admin approves it
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{slug}")
def product_reviews(slug: str, db: Session = Depends(get_db)):
    rows = (
        db.query(Review)
        .filter(Review.product_slug == slug, Review.approved == 1)
        .order_by(Review.created_at.desc())
        .all()
    )
    count = len(rows)
    average = round(sum(r.rating for r in rows) / count, 1) if count else 0.0
    return {
        "count": count,
        "average": average,
        "reviews": [ReviewOut.model_validate(r).model_dump(mode="json") for r in rows],
    }
