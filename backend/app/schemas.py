from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrderItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    price: int = Field(gt=0, le=100000)
    quantity: int = Field(gt=0, le=100)


class OrderCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    phone: str = Field(pattern=r"^\d{10}$")
    email: EmailStr
    address: str = Field(min_length=12, max_length=1000)
    payment_type: Literal["PREPAID", "COD"]
    items: list[OrderItemCreate] = Field(min_length=1, max_length=100)


class ReservationCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    phone: str = Field(pattern=r"^\d{10}$")
    guests: int = Field(ge=1, le=100)
    datetime: datetime
    message: str | None = Field(default=None, max_length=500)
    include_preorder: bool = False
    preorder_items: list[OrderItemCreate] = Field(default_factory=list, max_length=100)


class ApiMessage(BaseModel):
    message: str


class OrderResponse(ApiMessage):
    order_id: int
    total_amount: int


class ReservationResponse(ApiMessage):
    reservation_id: int


class HealthResponse(BaseModel):
    status: str


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    phone: str
    email: str
    address: str
    payment_type: str
    payment_status: str
    total_amount: int
    created_at: datetime


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_name: str
    unit_price: int
    quantity: int


class AdminOrderOut(OrderOut):
    items: list[OrderItemOut]


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    phone: str
    guests: int
    reservation_at: datetime
    message: str | None
    include_preorder: bool
    preorder_items: list[dict] | None
    preorder_total: int | None
    created_at: datetime
