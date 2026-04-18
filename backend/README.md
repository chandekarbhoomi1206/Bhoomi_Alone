# Momeato Backend
Python backend for the restaurant website using FastAPI and Neon Postgres.

## 1. Create a virtual environment
<!-- powershell -->
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

## 2. Run the server
<!-- powershell -->
uvicorn app.main:app --reload

The backend will:
- serve the website at `http://127.0.0.1:8000`
- serve the admin page at `http://127.0.0.1:8000/admin.html`
- expose `POST /api/orders`
- expose `POST /api/reservations`
- expose `GET /api/admin/orders`
- expose `GET /api/admin/reservations`
- create tables automatically on startup
- save reservation pre-orders when the booking form includes the current cart
- save reservation phone numbers for admin follow-up

## Database tables
- `orders`
- `order_items`
- `reservations`