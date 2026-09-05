from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from db.database import get_db
from models.models import Transaction, PurchaseRequest, AuditEvent
from services import razorpay_service

router = APIRouter(prefix="/approvals", tags=["Approvals"])


def log_event(db, transaction_id, event_type, description, metadata=None):
    db.add(AuditEvent(
        transaction_id=transaction_id,
        event_type=event_type,
        description=description,
        event_metadata=metadata or {},
        timestamp=datetime.now(timezone.utc)
    ))
    db.commit()


@router.get("/pending")
def list_pending(db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(
        Transaction.policy_decision == "REVIEW",
        Transaction.approval_status == "pending_human"
    ).order_by(Transaction.created_at.desc()).all()

    results = []
    for tx in txs:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == tx.purchase_request_id).first()
        results.append({
            "transaction_id": tx.id,
            "amount": tx.amount,
            "policy_decision": tx.policy_decision,
            "policy_reasons": tx.policy_reasons,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "request": pr.natural_language_request if pr else None,
            "selected_products": pr.selected_products if pr else [],
        })
    return results


@router.post("/{transaction_id}/approve")
def approve(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.approval_status != "pending_human":
        raise HTTPException(status_code=400, detail=f"Transaction is not pending approval. Status: {tx.approval_status}")

    # Create Razorpay order now that human approved
    try:
        order = razorpay_service.create_order(
            amount_inr=tx.amount,
            receipt=tx.id[:40],
            notes={"transaction_id": tx.id, "approved_by": "human"}
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Razorpay error: {str(e)}")

    tx.approval_status = "approved"
    tx.policy_decision = "APPROVE"
    tx.razorpay_order_id = order["id"]
    tx.payment_status = "created"
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(db, tx.id, "HUMAN_APPROVED",
              f"Transaction approved by merchant. Razorpay order created: {order['id']}",
              {"razorpay_order_id": order["id"], "amount": tx.amount})

    return {
        "status": "approved",
        "transaction_id": tx.id,
        "razorpay_order_id": order["id"],
        "amount": tx.amount,
        "payment_status": "created"
    }


@router.post("/{transaction_id}/reject")
def reject(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if tx.approval_status != "pending_human":
        raise HTTPException(status_code=400, detail=f"Transaction is not pending approval. Status: {tx.approval_status}")

    tx.approval_status = "rejected"
    tx.payment_status = "rejected"
    tx.updated_at = datetime.now(timezone.utc)
    db.commit()

    log_event(db, tx.id, "HUMAN_REJECTED",
              "Transaction rejected by merchant. No payment will be processed.",
              {"amount": tx.amount})

    return {
        "status": "rejected",
        "transaction_id": tx.id,
        "message": "Transaction rejected. No payment processed."
    }
