import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timezone
from db.database import get_db
from models.models import Transaction, AuditEvent, Merchant
from services import razorpay_service
from services.policy_engine import evaluate_policy
from config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


class CreateOrderRequest(BaseModel):
    transaction_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def log_event(db: Session, transaction_id: str, event_type: str, description: str, metadata: dict = None):
    event = AuditEvent(
        transaction_id=transaction_id,
        event_type=event_type,
        description=description,
        event_metadata=metadata or {},
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()


@router.post("/create-order")
def create_order(request: CreateOrderRequest, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == request.transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Gate: only APPROVE status transactions can create an order
    if tx.policy_decision not in ("APPROVE",) or tx.approval_status != "approved":
        raise HTTPException(
            status_code=403,
            detail=f"Cannot create order. Policy decision: {tx.policy_decision}, Approval: {tx.approval_status}"
        )

    if tx.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Razorpay order already created for this transaction.")

    try:
        order = razorpay_service.create_order(
            amount_inr=tx.amount,
            receipt=tx.id[:40],
            notes={"transaction_id": tx.id}
        )
    except Exception as e:
        log_event(db, tx.id, "PAYMENT_ORDER_FAILED", f"Razorpay order creation failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    tx.razorpay_order_id = order["id"]
    tx.payment_status = "created"
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(db, tx.id, "RAZORPAY_ORDER_CREATED",
              f"Razorpay order created: {order['id']}",
              {"razorpay_order_id": order["id"], "amount_paise": order["amount"]})

    return {
        "razorpay_order_id": order["id"],
        "amount_paise": order["amount"],
        "currency": order["currency"],
        "key_id": settings.RAZORPAY_KEY_ID,   # safe — test key ID is public-facing
        "transaction_id": tx.id
    }


@router.get("/status/{transaction_id}")
def get_payment_status(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if not tx.razorpay_order_id:
        return {"transaction_id": transaction_id, "payment_status": tx.payment_status, "razorpay_order_id": None}

    try:
        order = razorpay_service.fetch_order(tx.razorpay_order_id)
        payments = razorpay_service.fetch_order_payments(tx.razorpay_order_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    return {
        "transaction_id": transaction_id,
        "razorpay_order_id": tx.razorpay_order_id,
        "payment_status": tx.payment_status,
        "razorpay_order_status": order.get("status"),
        "payments": payments.get("items", [])
    }


@router.post("/verify")
def verify_payment(request: PaymentVerifyRequest, db: Session = Depends(get_db)):
    """Called after frontend completes Razorpay checkout to verify and confirm payment."""
    is_valid = razorpay_service.verify_payment_signature({
        "razorpay_order_id": request.razorpay_order_id,
        "razorpay_payment_id": request.razorpay_payment_id,
        "razorpay_signature": request.razorpay_signature
    })

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid payment signature.")

    tx = db.query(Transaction).filter(
        Transaction.razorpay_order_id == request.razorpay_order_id
    ).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found for this order.")

    tx.payment_status = "paid"
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(db, tx.id, "PAYMENT_VERIFIED",
              f"Payment verified successfully. Payment ID: {request.razorpay_payment_id}",
              {"razorpay_payment_id": request.razorpay_payment_id})

    return {"status": "success", "transaction_id": tx.id, "payment_status": "paid"}


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """Razorpay webhook — verifies signature and updates payment status."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    import json
    payload = json.loads(body)
    event = payload.get("event")

    if event == "payment.captured":
        order_id = payload["payload"]["payment"]["entity"]["order_id"]
        payment_id = payload["payload"]["payment"]["entity"]["id"]

        tx = db.query(Transaction).filter(Transaction.razorpay_order_id == order_id).first()
        if tx:
            tx.payment_status = "paid"
            tx.updated_at = datetime.now(timezone.utc)
            db.commit()
            log_event(db, tx.id, "PAYMENT_CAPTURED",
                      f"Payment captured via webhook. Payment ID: {payment_id}",
                      {"razorpay_payment_id": payment_id, "event": event})

    elif event == "payment.failed":
        order_id = payload["payload"]["payment"]["entity"]["order_id"]
        tx = db.query(Transaction).filter(Transaction.razorpay_order_id == order_id).first()
        if tx:
            tx.payment_status = "failed"
            tx.updated_at = datetime.now(timezone.utc)
            db.commit()
            log_event(db, tx.id, "PAYMENT_FAILED",
                      "Payment failed via webhook.",
                      {"event": event})

    return {"status": "ok"}
