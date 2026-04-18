import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)

from .db import Base, engine, get_db
from .models import Order, OrderItem, Reservation
from .schemas import (
    AdminOrderOut,
    HealthResponse,
    OrderCreate,
    OrderOut,
    OrderResponse,
    ReservationCreate,
    ReservationOut,
    ReservationResponse,
)


app = FastAPI(title="Momeato Backend", version="1.0.0")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-admin").strip().strip("\"'")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE reservations
                ADD COLUMN IF NOT EXISTS phone VARCHAR(10)
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE reservations
                SET phone = ''
                WHERE phone IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE reservations
                ADD COLUMN IF NOT EXISTS include_preorder BOOLEAN NOT NULL DEFAULT FALSE
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE reservations
                ADD COLUMN IF NOT EXISTS preorder_items JSON
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE reservations
                ADD COLUMN IF NOT EXISTS preorder_total INTEGER
                """
            )
        )


@app.get("/api/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


def require_admin_password(x_admin_password: str | None = Header(default=None)) -> None:
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password.")


@app.post("/api/orders", response_model=OrderResponse, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    total_amount = sum(item.price * item.quantity for item in payload.items)
    payment_status = "reported_paid" if payload.payment_type == "PREPAID" else "pending_cod"

    order = Order(
        customer_name=payload.name.strip(),
        phone=payload.phone,
        email=payload.email,
        address=payload.address.strip(),
        payment_type=payload.payment_type,
        payment_status=payment_status,
        total_amount=total_amount,
        items=[
            OrderItem(
                item_name=item.name.strip(),
                unit_price=item.price,
                quantity=item.quantity,
            )
            for item in payload.items
        ],
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return OrderResponse(
        message="Order saved successfully.",
        order_id=order.id,
        total_amount=order.total_amount,
    )


@app.post("/api/reservations", response_model=ReservationResponse, status_code=201)
def create_reservation(
    payload: ReservationCreate, db: Session = Depends(get_db)
) -> ReservationResponse:
    if payload.include_preorder and not payload.preorder_items:
        raise HTTPException(
            status_code=400,
            detail="Preorder was selected, but no cart items were provided.",
        )

    preorder_items = None
    preorder_total = None

    if payload.include_preorder:
        preorder_items = [
            {
                "name": item.name.strip(),
                "price": item.price,
                "quantity": item.quantity,
            }
            for item in payload.preorder_items
        ]
        preorder_total = sum(item["price"] * item["quantity"] for item in preorder_items)

    reservation = Reservation(
        customer_name=payload.name.strip(),
        phone=payload.phone,
        guests=payload.guests,
        reservation_at=payload.datetime,
        message=payload.message.strip() if payload.message else None,
        include_preorder=payload.include_preorder,
        preorder_items=preorder_items,
        preorder_total=preorder_total,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return ReservationResponse(
        message="Reservation saved successfully.",
        reservation_id=reservation.id,
    )


@app.get("/api/admin/orders", response_model=list[AdminOrderOut])
def list_orders(
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(require_admin_password),
    db: Session = Depends(get_db),
) -> list[Order]:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@app.get("/api/admin/reservations", response_model=list[ReservationOut])
def list_reservations(
    limit: int = Query(default=500, ge=1, le=1000),
    _: None = Depends(require_admin_password),
    db: Session = Depends(get_db),
) -> list[Reservation]:
    statement = (
        select(Reservation)
        .order_by(Reservation.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


frontend_dir = BASE_DIR.parent
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
