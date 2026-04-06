# Momeato Backend

Python backend for the restaurant website using FastAPI and Neon Postgres.

## 1. Create a virtual environment

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Configure Neon

Copy `.env.example` to `.env` and paste your Neon connection string into `DATABASE_URL`.

```powershell
Copy-Item .env.example .env
```

Use the pooled Neon connection string in this format:

```text
postgresql+psycopg://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
```

Also set an admin password in `.env`:

```env
ADMIN_PASSWORD=your-strong-admin-password
```

For confirmations, add SMTP settings and the restaurant email:

```env
RESTAURANT_NOTIFICATION_EMAIL=restaurant@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@example.com
SMTP_USE_TLS=true
```

Optional WhatsApp confirmation:

```env
WHATSAPP_URL_TEMPLATE=https://example.com/send?phone={phone}&text={message}
```

The template should support both `{phone}` and `{message}` placeholders.

## 3. Run the server

```powershell
uvicorn app.main:app --reload
```

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
- send email confirmations to the restaurant and order customer when SMTP is configured
- send WhatsApp confirmations to the booking/order phone number when `WHATSAPP_URL_TEMPLATE` is configured

## Database tables

- `orders`
- `order_items`
- `reservations`

## Notes

- `PREPAID` orders are stored with payment status `reported_paid` because the current page uses QR confirmation rather than a payment gateway callback.
- `COD` orders are stored with payment status `pending_cod`.
- Admin API access is protected with the `ADMIN_PASSWORD` from your `.env` file.
- Reservation customer confirmation currently uses WhatsApp only unless you later add reservation email collection.
