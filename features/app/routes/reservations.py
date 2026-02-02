from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Manager, Seat, Timeslot, Reservation, Charge, ReservationStatus
)
from app.schemas import (
    TimeslotResponse, SeatResponse, ReservationCreate, ReservationResponse
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])

# Fixed Blu-Dollar amount per reservation
RESERVATION_PRICE = Decimal("10.00")  # Adjust as needed


def get_current_user_from_session(request: Request, db: Session = Depends(get_db)):
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


@router.get("/timeslots", response_model=list[TimeslotResponse], summary="Get Timeslots", description="Returns all available timeslots for a specific date")
def get_timeslots(date: str, db: Session = Depends(get_db)):
    """
    Get timeslots for a specific date.
    
    - **date**: Date in YYYY-MM-DD format
    - Returns all 30-minute timeslots (12:00-15:00) for the specified date
    - Timeslots are ordered by start time
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Restrict to today and tomorrow only
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    if target_date < today or target_date > tomorrow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only book seats for today or tomorrow"
        )
    
    # Get timeslots for the target date
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    timeslots = db.query(Timeslot).filter(
        Timeslot.starts_at >= start_of_day,
        Timeslot.starts_at < end_of_day + timedelta(days=1)
    ).order_by(Timeslot.starts_at).all()
    
    return timeslots


@router.get("/seats", response_model=list[SeatResponse], summary="Get Seats", description="Returns all 100 seats with availability status for a timeslot")
def get_seats(
    timeslot_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get all seats with availability for a specific timeslot.
    
    - **timeslot_id**: ID of the timeslot
    - Returns all 100 seats (A1-J10)
    - Shows availability status (available/booked)
    - Shows ownership status (mine: true/false) if user is authenticated
    - Seats are ordered by ID
    """
    # Verify timeslot exists
    timeslot = db.query(Timeslot).filter(Timeslot.id == timeslot_id).first()
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeslot not found"
        )
    
    # Get all seats
    seats = db.query(Seat).order_by(Seat.id).all()
    
    # Get confirmed reservations for this timeslot
    reservations = db.query(Reservation).filter(
        and_(
            Reservation.timeslot_id == timeslot_id,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).all()
    
    # Determine which seats are truly reserved based on the 5-minute timer
    from datetime import datetime
    current_time = datetime.utcnow()
    reserved_seat_ids = set()
    
    for r in reservations:
        # If the reservation's available_at is in the future, the seat is still reserved
        # (regardless of timeslot end time - the timer takes precedence)
        if r.available_at and r.available_at > current_time:
            reserved_seat_ids.add(r.seat_id)
        # If available_at is None or in the past, the seat is available
        # (This handles legacy reservations without available_at set and expired reservations)
        else:
            # Seat is available now, don't add to reserved set
            continue
    
    # Get current user's reservation for this timeslot (if any)
    user_id = request.session.get("user_id")
    my_seat_id = None
    if user_id:
        my_reservation = next(
            (r for r in reservations if r.user_id == user_id),
            None
        )
        if my_reservation:
            my_seat_id = my_reservation.seat_id
    
    # Build response with availability and ownership
    result = []
    for seat in seats:
        seat_dict = {
            "id": seat.id,
            "label": seat.label,
            "available": seat.id not in reserved_seat_ids,
            "mine": seat.id == my_seat_id if my_seat_id else False
        }
        result.append(SeatResponse(**seat_dict))
    
    return result


@router.get("/mine", response_model=list[ReservationResponse], summary="Get My Reservations", description="Returns all confirmed reservations for the current user")
def get_my_reservations(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get current user's reservations.
    
    - Returns all confirmed reservations for authenticated user
    - Includes seat and timeslot details
    - Ordered by creation date (newest first)
    - Requires authentication
    """
    user = get_current_user_from_session(request, db)
    
    reservations = db.query(Reservation).filter(
        and_(
            Reservation.user_id == user.id,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).order_by(Reservation.created_at.desc()).all()
    
    result = []
    for res in reservations:
        result.append(ReservationResponse(
            id=res.id,
            user_id=res.user_id,
            seat_id=res.seat_id,
            timeslot_id=res.timeslot_id,
            status=res.status.value,
            created_at=res.created_at,
            available_at=res.available_at,
            seat=SeatResponse(
                id=res.seat.id,
                label=res.seat.label,
                available=False,
                mine=True
            ),
            timeslot=TimeslotResponse(
                id=res.timeslot.id,
                starts_at=res.timeslot.starts_at,
                ends_at=res.timeslot.ends_at
            )
        ))
    
    return result


@router.get("/verify", summary="Verify System Status", description="Check system status without modifying data")
def verify_system_status(db: Session = Depends(get_db)):
    """
    Verify system is working (read-only check).
    
    Returns:
    - Total seats count
    - Total timeslots count
    - Total reservations count
    - Manager balances
    - Recent charges
    """
    seats_count = db.query(Seat).count()
    timeslots_count = db.query(Timeslot).count()
    reservations_count = db.query(Reservation).filter(
        Reservation.status == ReservationStatus.CONFIRMED
    ).count()
    
    managers = db.query(Manager).all()
    manager_balances = [
        {"manager_name": m.manager_name, "balance": float(m.balance)}
        for m in managers
    ]
    
    recent_charges = db.query(Charge).order_by(Charge.created_at.desc()).limit(5).all()
    charges_list = [
        {
            "id": c.id,
            "amount": float(c.amount),
            "created_at": c.created_at.isoformat(),
            "manager_id": c.manager_id
        }
        for c in recent_charges
    ]
    
    return {
        "status": "operational",
        "seats": seats_count,
        "timeslots": timeslots_count,
        "active_reservations": reservations_count,
        "managers": manager_balances,
        "recent_charges": charges_list
    }


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, summary="Create Reservation", description="Books a seat for a timeslot and charges manager account")
def create_reservation(
    reservation_data: ReservationCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new reservation.
    
    - **seat_id**: ID of the seat to book
    - **timeslot_id**: ID of the timeslot
    - Validates seat and timeslot exist
    - Checks seat availability
    - Prevents double-booking (user or seat already reserved)
    - Charges 10.00 Blu-Dollars to manager account
    - Returns 409 Conflict if double-booking attempted
    - Returns 402 Payment Required if insufficient balance
    - Requires authentication
    """
    user = get_current_user_from_session(request, db)
    
    # Verify seat exists
    seat = db.query(Seat).filter(Seat.id == reservation_data.seat_id).first()
    if not seat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seat not found"
        )
    
    # Verify timeslot exists
    timeslot = db.query(Timeslot).filter(Timeslot.id == reservation_data.timeslot_id).first()
    if not timeslot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeslot not found"
        )
    
    # One seat per user: user can only have 1 active reservation
    active_reservations_count = db.query(Reservation).filter(
        and_(
            Reservation.user_id == user.id,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).count()

    if active_reservations_count >= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can only book one seat. Please cancel your existing reservation to book a new one."
        )
    
    # Check if seat is already reserved for this timeslot
    existing_seat_reservation = db.query(Reservation).filter(
        and_(
            Reservation.seat_id == reservation_data.seat_id,
            Reservation.timeslot_id == reservation_data.timeslot_id,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).first()
    
    if existing_seat_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This seat is already booked for this timeslot. Please select a different seat or timeslot."
        )
    
    # Get or create manager
    if not user.manager_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a manager assigned"
        )
    
    manager = db.query(Manager).filter(
        Manager.manager_name == user.manager_name
    ).first()
    
    if not manager:
        manager = Manager(
            manager_name=user.manager_name,
            balance=Decimal("1000.00")  # Default starting balance
        )
        db.add(manager)
        db.flush()
    
    # Check manager balance
    if manager.balance < RESERVATION_PRICE:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient manager balance"
        )
    
    # Create reservation and charge in a transaction
    try:
        # Calculate when the seat becomes available again (5 minutes after booking)
        available_time = datetime.utcnow() + timedelta(minutes=5)
        
        # Create reservation
        reservation = Reservation(
            user_id=user.id,
            seat_id=reservation_data.seat_id,
            timeslot_id=reservation_data.timeslot_id,
            status=ReservationStatus.CONFIRMED,
            available_at=available_time
        )
        db.add(reservation)
        db.flush()  # Get reservation.id
        
        # Deduct from employee's manager balance
        manager.balance -= RESERVATION_PRICE

        # Credit Admin (revenue from charges)
        admin_manager = db.query(Manager).filter(Manager.manager_name == "Admin").first()
        if admin_manager:
            admin_manager.balance += RESERVATION_PRICE

        # Create charge record
        charge = Charge(
            manager_id=manager.id,
            reservation_id=reservation.id,
            amount=RESERVATION_PRICE
        )
        db.add(charge)
        
        db.commit()
        db.refresh(reservation)
        
        return ReservationResponse(
            id=reservation.id,
            user_id=reservation.user_id,
            seat_id=reservation.seat_id,
            timeslot_id=reservation.timeslot_id,
            status=reservation.status.value,
            created_at=reservation.created_at,
            available_at=reservation.available_at,
            seat=SeatResponse(
                id=seat.id,
                label=seat.label,
                available=False,
                mine=True
            ),
            timeslot=TimeslotResponse(
                id=timeslot.id,
                starts_at=timeslot.starts_at,
                ends_at=timeslot.ends_at
            )
        )
        
    except IntegrityError as e:
        db.rollback()
        # Race condition: concurrent booking of same seat/timeslot
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reservation conflict: seat or user already has a reservation for this timeslot",
        ) from e
    except Exception as e:
        db.rollback()
        error_str = str(e).lower()
        if any(
            k in error_str
            for k in [
                "uq_user_timeslot",
                "uq_seat_timeslot",
                "unique constraint",
                "duplicate key",
                "violates unique",
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Reservation conflict: seat or user already has a reservation for this timeslot",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reservation: {str(e)}",
        ) from e
