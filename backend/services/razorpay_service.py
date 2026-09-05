import razorpay
from config import settings

_client = None

def get_client() -> razorpay.Client:
    global _client
    if _client is None:
        _client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    return _client


def create_order(amount_inr: float, receipt: str, notes: dict = None) -> dict:
    """Create a Razorpay order. Amount is in INR — converted to paise internally."""
    client = get_client()
    amount_paise = int(amount_inr * 100)
    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "notes": notes or {},
        "payment_capture": 1
    }
    order = client.order.create(data=payload)
    return order


def fetch_order(razorpay_order_id: str) -> dict:
    client = get_client()
    return client.order.fetch(razorpay_order_id)


def fetch_order_payments(razorpay_order_id: str) -> dict:
    client = get_client()
    return client.order.payments(razorpay_order_id)


def verify_payment_signature(payload: dict) -> bool:
    client = get_client()
    try:
        client.utility.verify_payment_signature(payload)
        return True
    except Exception:
        return False
