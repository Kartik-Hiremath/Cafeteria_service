from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


# User schemas
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    employee_uid: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    manager_name: Optional[str] = None


# Timeslot schemas
class TimeslotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    starts_at: datetime
    ends_at: datetime


# Seat schemas
class SeatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    label: str
    available: bool = True
    mine: bool = False


# Reservation schemas
class ReservationCreate(BaseModel):
    seat_id: int
    timeslot_id: int


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    seat_id: int
    timeslot_id: int
    status: str
    created_at: datetime
    available_at: Optional[datetime] = None
    seat: SeatResponse
    timeslot: TimeslotResponse


# Charge schemas
class ChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    manager_id: int
    reservation_id: int
    amount: Decimal
    created_at: datetime
