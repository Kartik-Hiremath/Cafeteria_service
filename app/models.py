from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    w3_id = Column(String, unique=True, index=True)
    name = Column(String)
    manager_w3_id = Column(String)

    bookings = relationship("Booking", back_populates="user")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    seat_number = Column(Integer, nullable=False)

    start_time = Column(DateTime)
    end_time = Column(DateTime)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookings")


class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True, index=True)
    w3_id = Column(String, unique=True, index=True)
    name = Column(String)
    balance = Column(Integer, default=0)
