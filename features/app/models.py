from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum


class ReservationStatus(enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    employee_uid = Column(String, unique=True, index=True, nullable=False)  # OIDC 'sub'
    email = Column(String, nullable=False, index=True)
    first_name = Column(String)
    last_name = Column(String)
    manager_name = Column(String)  # Manager's name for charging

    reservations = relationship("Reservation", back_populates="user")


class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True, index=True)
    manager_name = Column(String, unique=True, nullable=False, index=True)
    balance = Column(Numeric(10, 2), default=0, nullable=False)

    charges = relationship("Charge", back_populates="manager")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)  # e.g., "A1", "B2", etc.

    reservations = relationship("Reservation", back_populates="seat")


class Timeslot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    starts_at = Column(DateTime, nullable=False, index=True)
    ends_at = Column(DateTime, nullable=False, index=True)

    reservations = relationship("Reservation", back_populates="timeslot")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.CONFIRMED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # Field to track when the seat becomes available again (for 5-minute timer)
    available_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="reservations")
    seat = relationship("Seat", back_populates="reservations")
    timeslot = relationship("Timeslot", back_populates="reservations")
    charges = relationship("Charge", back_populates="reservation")

    # Constraints to prevent double-booking
    __table_args__ = (
        UniqueConstraint('user_id', 'timeslot_id', name='uq_user_timeslot'),
        UniqueConstraint('seat_id', 'timeslot_id', name='uq_seat_timeslot'),
    )


class Charge(Base):
    __tablename__ = "charges"

    id = Column(Integer, primary_key=True, index=True)
    manager_id = Column(Integer, ForeignKey("managers.id"), nullable=False)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    manager = relationship("Manager", back_populates="charges")
    reservation = relationship("Reservation", back_populates="charges")
