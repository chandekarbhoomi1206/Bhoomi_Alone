import os
import smtplib
from email.message import EmailMessage
from urllib.parse import quote
from urllib.request import Request, urlopen


SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").strip().lower() == "true"
RESTAURANT_NOTIFICATION_EMAIL = os.getenv("RESTAURANT_NOTIFICATION_EMAIL", "").strip()
WHATSAPP_URL_TEMPLATE = os.getenv("WHATSAPP_URL_TEMPLATE", "").strip()


def is_email_configured() -> bool:
    return all(
        [
            SMTP_HOST,
            SMTP_FROM_EMAIL,
            RESTAURANT_NOTIFICATION_EMAIL,
        ]
    )


def send_email(subject: str, body: str, recipients: list[str]) -> None:
    if not SMTP_HOST or not SMTP_FROM_EMAIL or not recipients:
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USERNAME:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)


def send_whatsapp(phone: str, message: str) -> None:
    if not WHATSAPP_URL_TEMPLATE or not phone.strip():
        return

    url = (
        WHATSAPP_URL_TEMPLATE.replace("{phone}", quote(phone.strip()))
        .replace("{message}", quote(message))
    )
    request = Request(url, method="GET")
    with urlopen(request, timeout=20):
        return


def _format_items(items: list[dict]) -> str:
    if not items:
        return "No items"
    return "\n".join(
        f"- {item['name']} x {item['quantity']} ({item['price']} each)" for item in items
    )


def notify_order_created(order_data: dict) -> None:
    restaurant_body = f"""New order received.

Order ID: {order_data['order_id']}
Customer: {order_data['name']}
Phone: {order_data['phone']}
Email: {order_data['email']}
Address: {order_data['address']}
Payment type: {order_data['payment_type']}
Total: Rs. {order_data['total_amount']}

Items:
{_format_items(order_data['items'])}
"""
    customer_body = f"""Hi {order_data['name']},

Your order #{order_data['order_id']} has been received by Momeato.

Payment type: {order_data['payment_type']}
Total: Rs. {order_data['total_amount']}

Items:
{_format_items(order_data['items'])}

Delivery address:
{order_data['address']}
"""

    try:
        send_email(
            subject=f"New Momeato Order #{order_data['order_id']}",
            body=restaurant_body,
            recipients=[RESTAURANT_NOTIFICATION_EMAIL] if RESTAURANT_NOTIFICATION_EMAIL else [],
        )
    except Exception as exc:
        print(f"Restaurant order email failed: {exc}")

    try:
        send_email(
            subject=f"Momeato Order Confirmation #{order_data['order_id']}",
            body=customer_body,
            recipients=[order_data["email"]],
        )
    except Exception as exc:
        print(f"Customer order email failed: {exc}")

    whatsapp_message = (
        f"Momeato order #{order_data['order_id']} received. "
        f"Payment: {order_data['payment_type']}. Total: Rs. {order_data['total_amount']}."
    )
    try:
        send_whatsapp(order_data["phone"], whatsapp_message)
    except Exception as exc:
        print(f"Order WhatsApp notification failed: {exc}")


def notify_reservation_created(reservation_data: dict) -> None:
    preorder_section = ""
    if reservation_data["include_preorder"]:
        preorder_section = (
            f"\nPre-order total: Rs. {reservation_data['preorder_total']}\n"
            f"Pre-order items:\n{_format_items(reservation_data['preorder_items'])}\n"
        )

    restaurant_body = f"""New reservation received.

Reservation ID: {reservation_data['reservation_id']}
Customer: {reservation_data['name']}
Phone: {reservation_data['phone']}
Guests: {reservation_data['guests']}
Reservation time: {reservation_data['datetime']}
Notes: {reservation_data['message'] or 'No message'}
Pre-order included: {'Yes' if reservation_data['include_preorder'] else 'No'}
{preorder_section}
"""
    whatsapp_message = (
        f"Momeato booking #{reservation_data['reservation_id']} confirmed for "
        f"{reservation_data['guests']} guest(s) on {reservation_data['datetime']}."
    )

    try:
        send_email(
            subject=f"New Momeato Reservation #{reservation_data['reservation_id']}",
            body=restaurant_body,
            recipients=[RESTAURANT_NOTIFICATION_EMAIL] if RESTAURANT_NOTIFICATION_EMAIL else [],
        )
    except Exception as exc:
        print(f"Restaurant reservation email failed: {exc}")

    try:
        send_whatsapp(reservation_data["phone"], whatsapp_message)
    except Exception as exc:
        print(f"Reservation WhatsApp notification failed: {exc}")
