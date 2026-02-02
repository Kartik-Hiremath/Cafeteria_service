from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking
from app.schemas import SeatResponse

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.get("/availability", response_model=List[SeatResponse])
def get_seat_availability(
    start_time: datetime = Query(..., description="Start time for availability check"),
    end_time: datetime = Query(..., description="End time for availability check"),
    db: Session = Depends(get_db)
):
    """Check seat availability for a given time range.
    
    Returns a list of all seats (1-100) with their availability status.
    A seat is 'reserved' if there's an overlapping booking, otherwise 'available'.
    
    Args:
        start_time: Start time of the desired booking period
        end_time: End time of the desired booking period
    
    Returns:
        List of seats with their availability status
    """
    # Define total number of seats (assuming seats 1-100)
    TOTAL_SEATS = 100
    
    # Get all bookings that overlap with the requested time range
    overlapping_bookings = (
        db.query(Booking.seat_number)
        .filter(
            (Booking.start_time < end_time) &
            (Booking.end_time > start_time)
        )
        .distinct()
        .all()
    )
    
    # Extract seat numbers that are booked
    booked_seat_numbers = {booking.seat_number for booking in overlapping_bookings}
    
    # Create response for all seats
    seats = []
    for seat_num in range(1, TOTAL_SEATS + 1):
        status = "reserved" if seat_num in booked_seat_numbers else "available"
        seats.append(SeatResponse(seat_number=seat_num, status=status))
    
    return seats
