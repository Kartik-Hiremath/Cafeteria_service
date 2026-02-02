from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# login request schemas
class LoginRequest(BaseModel):
    w3_id: str
    name: str
    manager_w3_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# seat schemas
class SeatResponse(BaseModel):
    seat_number: int
    status: str

    class Config:
        orm_mode = True


# booking schemas
# request
class BookingCreate(BaseModel):
    seat_number: int
    start_time: datetime
    end_time: datetime

# response for listing bookings
class BookingListResponse(BaseModel):
    id: int
    user_id: int
    seat_number: int
    start_time: datetime
    end_time: datetime
    timestamp: datetime

    class Config:
        orm_mode = True

# response for creating booking (includes manager info)
class BookingResponse(BaseModel):
    id: int
    user_id: int
    seat_number: int
    start_time: datetime
    end_time: datetime
    timestamp: datetime
    manager_name: str
    amount_deducted: int
    manager_new_balance: int

    class Config:
        orm_mode = True


# user schema
class UserResponse(BaseModel):
    w3_id: str
    name: str
    manager_w3_id: Optional[str] = None

    class Config:
        orm_mode = True


# manager schemas
class ManagerResponse(BaseModel):
    w3_id: str
    name: str
    balance: int

    class Config:
        orm_mode = True


class ManagerBalanceUpdate(BaseModel):
    w3_id: str
    amount: int  # Amount to add or subtract from balance