"""Booking / inquiry routes ('Ask a question', 'Request COA', 'Bulk quote').

POST /api/bookings/  (TRAILING SLASH). Saves the inquiry and fires both the
customer receipt and the owner alert via BackgroundTasks.
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Booking
from backend.schemas import BookingCreate, BookingOut
from backend.services import email

router = APIRouter()


@router.post("/", response_model=BookingOut, status_code=201)
def create_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    booking = Booking(**payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Snapshot fields so the background task doesn't touch a detached ORM row.
    snapshot = BookingOut.model_validate(booking).model_dump()
    background_tasks.add_task(email.send_customer_confirmation, snapshot)
    background_tasks.add_task(email.send_owner_notification, snapshot)
    return booking
