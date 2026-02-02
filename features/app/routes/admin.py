from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models import (
    User, Manager, Seat, Timeslot, Reservation, Charge, ReservationStatus
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
def get_dashboard_data(db: Session = Depends(get_db)):
    """
    Get real-time dashboard data for admin/developer view.
    
    Returns:
    - Active reservations with seat and user info
    - Manager balances
    - Recent charges
    - Seat occupancy status
    - Statistics
    """
    # Get all active reservations considering the 5-minute timer
    from datetime import datetime
    current_time = datetime.utcnow()
    active_reservations = db.query(Reservation).filter(
        and_(
            Reservation.status == ReservationStatus.CONFIRMED,
            or_(
                # For backward compatibility (no available_at set)
                Reservation.available_at == None,
                # For timed reservations: available_at is in the future
                Reservation.available_at > current_time
            )
        )
    ).all()
    
    reservations_data = []
    for res in active_reservations:
        reservations_data.append({
            "id": res.id,
            "user_email": res.user.email,
            "user_name": f"{res.user.first_name or ''} {res.user.last_name or ''}".strip() or res.user.email,
            "seat_label": res.seat.label,
            "timeslot_start": res.timeslot.starts_at.isoformat(),
            "timeslot_end": res.timeslot.ends_at.isoformat(),
            "created_at": res.created_at.isoformat(),
            "available_at": res.available_at.isoformat() if res.available_at else None,
            "manager_name": res.user.manager_name
        })
    
    # Get all managers with balances
    managers = db.query(Manager).order_by(Manager.manager_name).all()
    manager_data = [
        {
            "id": m.id,
            "name": m.manager_name,
            "balance": float(m.balance)
        }
        for m in managers
    ]
    
    # Get recent charges (last 20)
    recent_charges = db.query(Charge).order_by(Charge.created_at.desc()).limit(20).all()
    charges_data = []
    for charge in recent_charges:
        charges_data.append({
            "id": charge.id,
            "manager_name": charge.manager.manager_name,
            "amount": float(charge.amount),
            "created_at": charge.created_at.isoformat(),
            "reservation_id": charge.reservation_id
        })
    
    # Get seat occupancy status considering the 5-minute timer
    from datetime import datetime
    current_time = datetime.utcnow()
    all_seats = db.query(Seat).order_by(Seat.id).all()
    seat_occupancy = []
    for seat in all_seats:
        # Get all reservations for this seat
        seat_reservations = db.query(Reservation).filter(
            and_(
                Reservation.seat_id == seat.id,
                Reservation.status == ReservationStatus.CONFIRMED
            )
        ).all()
        
        # Count active reservations based on 5-minute timer
        active_count = 0
        for reservation in seat_reservations:
            # Check if reservation is still active based on timer
            if reservation.available_at is None or reservation.available_at > current_time:
                # Reservation is still active
                active_count += 1
            # Note: We don't need to check timeslot end here since the timer controls availability
        
        seat_occupancy.append({
            "id": seat.id,
            "label": seat.label,
            "active_reservations": active_count,
            "is_occupied": active_count > 0
        })
    
    # Statistics
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    bookings_today = db.query(Reservation).filter(
        and_(
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.created_at >= today_start,
            Reservation.created_at < today_end
        )
    ).count()
    
    total_revenue = db.query(func.sum(Charge.amount)).scalar() or 0
    
    most_booked_seats = db.query(
        Seat.label,
        func.count(Reservation.id).label('booking_count')
    ).join(Reservation, Seat.id == Reservation.seat_id).filter(
        Reservation.status == ReservationStatus.CONFIRMED
    ).group_by(Seat.id, Seat.label).order_by(
        func.count(Reservation.id).desc()
    ).limit(10).all()
    
    return {
        "active_reservations": reservations_data,
        "managers": manager_data,
        "recent_charges": charges_data,
        "seat_occupancy": seat_occupancy,
        "statistics": {
            "total_active_reservations": len(active_reservations),
            "bookings_today": bookings_today,
            "total_revenue": float(total_revenue),
            "most_booked_seats": [
                {"seat": seat[0], "bookings": seat[1]}
                for seat in most_booked_seats
            ]
        }
    }


@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """
    Get detailed statistics for admin dashboard.
    """
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Total bookings today
    bookings_today = db.query(Reservation).filter(
        and_(
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.created_at >= today_start,
            Reservation.created_at < today_end
        )
    ).count()
    
    # Total revenue
    total_revenue = db.query(func.sum(Charge.amount)).scalar() or 0
    
    # Active reservations count
    active_reservations = db.query(Reservation).filter(
        Reservation.status == ReservationStatus.CONFIRMED
    ).count()
    
    # Manager with lowest balance
    lowest_balance_manager = db.query(Manager).order_by(Manager.balance.asc()).first()
    
    # Most active manager (by charges)
    most_active_manager = db.query(
        Manager.manager_name,
        func.count(Charge.id).label('charge_count')
    ).join(Charge, Manager.id == Charge.manager_id).group_by(
        Manager.id, Manager.manager_name
    ).order_by(func.count(Charge.id).desc()).first()
    
    return {
        "bookings_today": bookings_today,
        "total_revenue": float(total_revenue),
        "active_reservations": active_reservations,
        "lowest_balance_manager": {
            "name": lowest_balance_manager.manager_name if lowest_balance_manager else None,
            "balance": float(lowest_balance_manager.balance) if lowest_balance_manager else 0
        },
        "most_active_manager": {
            "name": most_active_manager[0] if most_active_manager else None,
            "charges": most_active_manager[1] if most_active_manager else 0
        }
    }


@router.get("/bookings")
def get_all_bookings(db: Session = Depends(get_db)):
    """
    Get all bookings for the full week (today through today+6) organized by timeslot.
    """
    from datetime import datetime
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    timeslots_for_dates = db.query(Timeslot).filter(
        func.date(Timeslot.starts_at) >= today,
        func.date(Timeslot.starts_at) <= tomorrow,
    ).order_by(Timeslot.starts_at).all()

    timeslot_ids = [t.id for t in timeslots_for_dates]
    if not timeslot_ids:
        reservations_for_dates = []
    else:
        reservations_for_dates = db.query(Reservation).filter(
            and_(
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.timeslot_id.in_(timeslot_ids),
            )
        ).all()
    
    # Group reservations by timeslot
    reservations_by_timeslot = {}
    for reservation in reservations_for_dates:
        timeslot_id = reservation.timeslot_id
        if timeslot_id not in reservations_by_timeslot:
            reservations_by_timeslot[timeslot_id] = []
        reservations_by_timeslot[timeslot_id].append({
            "id": reservation.id,
            "user_email": reservation.user.email,
            "user_name": f"{reservation.user.first_name or ''} {reservation.user.last_name or ''}".strip() or reservation.user.email,
            "seat_label": reservation.seat.label,
            "created_at": reservation.created_at.isoformat(),
            "available_at": reservation.available_at.isoformat() if reservation.available_at else None,
            "manager_name": reservation.user.manager_name
        })
    
    # Prepare timeslot data with reservations
    timeslot_data = []
    for timeslot in timeslots_for_dates:
        timeslot_reservations = reservations_by_timeslot.get(timeslot.id, [])
        timeslot_data.append({
            "id": timeslot.id,
            "starts_at": timeslot.starts_at.isoformat(),
            "ends_at": timeslot.ends_at.isoformat(),
            "date": timeslot.starts_at.strftime('%Y-%m-%d'),
            "time_range": f"{timeslot.starts_at.strftime('%H:%M')} - {timeslot.ends_at.strftime('%H:%M')}",
            "reservations_count": len(timeslot_reservations),
            "reservations": timeslot_reservations
        })
    
    # Group by date
    bookings_by_date = {}
    for timeslot in timeslot_data:
        date = timeslot["date"]
        if date not in bookings_by_date:
            bookings_by_date[date] = []
        bookings_by_date[date].append(timeslot)
    
    dates = [today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")]
    return {
        "bookings_by_date": bookings_by_date,
        "dates": dates,
    }


@router.post("/reset")
def reset_system(db: Session = Depends(get_db)):
    """
    Reset the system: Cancel all reservations and restore manager balances.
    ACID: Single transaction; rollback on any failure.
    """
    from app.seed import MANAGER_DEFAULT_BALANCE

    try:
        active_reservations = db.query(Reservation).filter(
            Reservation.status == ReservationStatus.CONFIRMED
        ).all()

        for r in active_reservations:
            r.status = ReservationStatus.CANCELLED

        managers = db.query(Manager).all()
        for m in managers:
            if m.manager_name == "Manager with 0 points":
                m.balance = Decimal("0.00")
            else:
                m.balance = MANAGER_DEFAULT_BALANCE

        db.commit()
        return {
            "message": "System reset successful",
            "cancelled_reservations": len(active_reservations),
            "restored_managers": len(managers),
        }
    except Exception:
        db.rollback()
        raise
