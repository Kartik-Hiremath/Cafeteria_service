from typing import List
from datetime import datetime
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Booking, Manager
from app.schemas import BookingResponse, BookingListResponse, BookingCreate
from app.auth.jwt import decode_access_token

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/upcoming", response_model=List[BookingListResponse])
def get_upcoming_bookings(token: str, db: Session = Depends(get_db)):
    """Return upcoming bookings for the authenticated user.

    The endpoint expects an access `token` (same as used for login). It decodes
    the token to find the user's `w3_id`, looks up the `User`, and returns any
    bookings whose `start_time` is after the current time.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    w3_id = payload.get("sub")
    if not w3_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing w3_id (sub claim)",
        )

    user = db.query(User).filter(User.w3_id == w3_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    now = datetime.utcnow()

    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .filter(Booking.start_time > now)
        .all()
    )

    results = []
    for b in bookings:
        results.append(
            {
                "id": b.id,
                "user_id": b.user_id,
                "seat_number": b.seat_number,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "timestamp": b.timestamp,
            }
        )

    return results


@router.get("/current", response_model=List[BookingListResponse])
def get_current_bookings(token: str, db: Session = Depends(get_db)):
    """Return bookings that are currently active for the authenticated user.

    A booking is considered current when `start_time < now < end_time`.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    w3_id = payload.get("sub")
    if not w3_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing w3_id (sub claim)",
        )

    user = db.query(User).filter(User.w3_id == w3_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    now = datetime.utcnow()

    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .filter(Booking.start_time < now)
        .filter(Booking.end_time > now)
        .all()
    )

    results = []
    for b in bookings:
        results.append(
            {
                "id": b.id,
                "user_id": b.user_id,
                "seat_number": b.seat_number,
                "start_time": b.start_time,
                "end_time": b.end_time,
                "timestamp": b.timestamp,
            }
        )

    return results



@router.post("/create", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """Create a new booking for an available seat.
    
    This endpoint:
    1. Authenticates the user via token
    2. Validates the seat is available (no overlapping bookings)
    3. Deducts $3 from the user's manager's balance
    4. Creates the booking with a random booking ID
    """
    # Decode token and get user
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    w3_id = payload.get("sub")
    if not w3_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token missing w3_id (sub claim)",
        )

    # Get user from database
    user = db.query(User).filter(User.w3_id == w3_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Check for overlapping bookings for this seat
    overlapping_booking = (
        db.query(Booking)
        .filter(Booking.seat_number == booking_data.seat_number)
        .filter(
            (Booking.start_time < booking_data.end_time) &
            (Booking.end_time > booking_data.start_time)
        )
        .first()
    )

    if overlapping_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Seat {booking_data.seat_number} is already booked for the requested time slot",
        )

    # Validate start_time is before end_time
    if booking_data.start_time >= booking_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before end time",
        )

    # Get manager and deduct $3 from balance
    if not user.manager_w3_id:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a manager assigned",
        )

    manager = db.query(Manager).filter(Manager.w3_id == user.manager_w3_id).first()
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Manager with w3_id {user.manager_w3_id} not found",
        )

    # Check if manager has sufficient balance
    if manager.balance < 3:  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient manager balance. Current balance: ${manager.balance}",
        )

    # Store manager info before deduction
    amount_deducted = 3
    manager_name = manager.name if manager.name else manager.w3_id  # type: ignore
    
    # Deduct $3 from manager's balance
    manager.balance -= amount_deducted  # type: ignore
    manager_new_balance = manager.balance  # type: ignore

    # Create booking with random ID
    # Generate a random booking ID that doesn't exist
    while True:
        booking_id = random.randint(100000, 999999)
        existing_booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not existing_booking:
            break

    # Create the booking
    new_booking = Booking(
        id=booking_id,
        user_id=user.id,
        seat_number=booking_data.seat_number,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        timestamp=datetime.utcnow()
    )

    # Commit all changes
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    # Return response with manager information
    return BookingResponse(
        id=new_booking.id,  # type: ignore
        user_id=new_booking.user_id,  # type: ignore
        seat_number=new_booking.seat_number,  # type: ignore
        start_time=new_booking.start_time,  # type: ignore
        end_time=new_booking.end_time,  # type: ignore
        timestamp=new_booking.timestamp,  # type: ignore
        manager_name=manager_name,  # type: ignore
        amount_deducted=amount_deducted,
        manager_new_balance=manager_new_balance  # type: ignore
    )
