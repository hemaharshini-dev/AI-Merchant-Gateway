from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db.database import get_db
from models.models import AuditEvent, Transaction, PurchaseRequest

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/{transaction_id}")
def get_audit_trail(transaction_id: str, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")

    pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == tx.purchase_request_id).first()
    events = db.query(AuditEvent).filter(
        AuditEvent.transaction_id == transaction_id
    ).order_by(AuditEvent.timestamp.asc()).all()

    return {
        "transaction_id": transaction_id,
        "amount": tx.amount,
        "policy_decision": tx.policy_decision,
        "approval_status": tx.approval_status,
        "payment_status": tx.payment_status,
        "razorpay_order_id": tx.razorpay_order_id,
        "request": pr.natural_language_request if pr else None,
        "selected_products": pr.selected_products if pr else [],
        "audit_trail": [
            {
                "event_type": e.event_type,
                "description": e.description,
                "metadata": e.event_metadata,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None
            }
            for e in events
        ]
    }


@router.get("/recent/all")
def get_recent_events(limit: int = Query(50, le=200), db: Session = Depends(get_db)):
    events = db.query(AuditEvent).order_by(
        AuditEvent.timestamp.desc()
    ).limit(limit).all()

    return [
        {
            "event_id": e.id,
            "transaction_id": e.transaction_id,
            "event_type": e.event_type,
            "description": e.description,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None
        }
        for e in events
    ]


@router.get("/transactions/all")
def get_all_transactions(db: Session = Depends(get_db)):
    txs = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    results = []
    for tx in txs:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == tx.purchase_request_id).first()
        results.append({
            "transaction_id": tx.id,
            "amount": tx.amount,
            "policy_decision": tx.policy_decision,
            "approval_status": tx.approval_status,
            "payment_status": tx.payment_status,
            "razorpay_order_id": tx.razorpay_order_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "request": pr.natural_language_request if pr else None,
            "selected_products": pr.selected_products if pr else [],
        })
    return results
