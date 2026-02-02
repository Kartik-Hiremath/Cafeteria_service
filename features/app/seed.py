from datetime import datetime, timedelta, time
from decimal import Decimal
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Seat, Timeslot, Manager


def seed_initial_data():
    """Seed initial data: 100 seats and default timeslots"""
    db: Session = SessionLocal()
    
    try:
        # Seed seats (100 seats in a 10x10 grid: A1-A10, B1-B10, ..., J1-J10)
        existing_seats = db.query(Seat).count()
        if existing_seats == 0:
            seats = []
            for row in range(10):  # A-J
                for col in range(1, 11):  # 1-10
                    label = f"{chr(65 + row)}{col}"  # A1, A2, ..., J10
                    seat = Seat(label=label)
                    seats.append(seat)
            
            db.add_all(seats)
            db.commit()
            print(f"Seeded {len(seats)} seats")
        else:
            print(f"Seats already exist ({existing_seats} seats)")
        
        # Seed timeslots for full week (today + 6 days) - all week cafeteria open
        today = datetime.now().date()
        existing_timeslots = db.query(Timeslot).filter(
            Timeslot.starts_at >= datetime.combine(today, time.min)
        ).count()

        if existing_timeslots == 0:
            timeslots = []
            for day_offset in range(2):  # Today and tomorrow only
                target_date = today + timedelta(days=day_offset)
                start_time = datetime.combine(target_date, time(12, 0))
                for slot_num in range(6):  # 30-min slots: 12:00-15:00
                    slot_start = start_time + timedelta(minutes=slot_num * 30)
                    slot_end = slot_start + timedelta(minutes=30)
                    timeslots.append(Timeslot(starts_at=slot_start, ends_at=slot_end))

            db.add_all(timeslots)
            db.commit()
            print(f"Seeded {len(timeslots)} timeslots (today and tomorrow, 6 slots/day)")
        else:
            print(f"Timeslots already exist ({existing_timeslots} timeslots)")
            
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


# Default balance for managers with points (used by seed and admin reset)
MANAGER_DEFAULT_BALANCE = Decimal("50000.00")


def seed_managers():
    """Seed managers: 10 managers with Blu points + Admin + 1 manager with 0 points.
    Employees (emp001-emp010) are created on first Dummy W3ID login.
    """
    db: Session = SessionLocal()

    try:
        existing_managers = db.query(Manager).count()
        if existing_managers == 0:
            managers = []

            # 10 managers with Blu points
            for i in range(1, 11):
                managers.append(Manager(
                    manager_name=f"Manager {i}",
                    balance=MANAGER_DEFAULT_BALANCE,
                ))

            # Admin manager
            managers.append(Manager(
                manager_name="Admin",
                balance=MANAGER_DEFAULT_BALANCE,
            ))

            # 1 manager with 0 points (for demo: employee cannot book)
            managers.append(Manager(
                manager_name="Manager with 0 points",
                balance=Decimal("0.00"),
            ))

            db.add_all(managers)
            db.commit()
            print(f"Seeded {len(managers)} managers (10 + Admin with points, 1 with 0 points)")
        else:
            print(f"Managers already exist ({existing_managers} managers)")
            
    except Exception as e:
        print(f"Error seeding managers: {e}")
        db.rollback()
    finally:
        db.close()
