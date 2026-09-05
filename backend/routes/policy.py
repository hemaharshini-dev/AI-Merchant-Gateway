from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from models.models import Merchant
from services.policy_engine import evaluate_policy

router = APIRouter(prefix="/policy", tags=["Policy"])


class PolicyEvaluateRequest(BaseModel):
    amount: float
    category: str
    quantity: int


@router.post("/evaluate")
def evaluate(request: PolicyEvaluateRequest, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == "merchant_techkart").first()
    result = evaluate_policy(
        amount=request.amount,
        category=request.category,
        quantity=request.quantity,
        policies=merchant.policies,
        db=db
    )
    return {
        "decision": result.decision,
        "allowed": result.allowed,
        "reasons": result.reasons,
        "requires_human_approval": result.requires_human_approval
    }
