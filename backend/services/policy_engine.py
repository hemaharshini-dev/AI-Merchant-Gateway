from dataclasses import dataclass
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from models.models import Transaction


@dataclass
class PolicyResult:
    decision: str           # APPROVE / REVIEW / DENY
    allowed: bool
    reasons: list[str]
    requires_human_approval: bool


def evaluate_policy(
    amount: float,
    category: str,
    quantity: int,
    policies: dict,
    db: Session,
    merchant_id: str = "merchant_techkart"
) -> PolicyResult:
    reasons = []

    max_amount = policies.get("max_transaction_amount", 10000)
    daily_limit = policies.get("daily_spending_limit", 30000)
    max_qty = policies.get("max_quantity", 5)
    allowed_categories = [c.lower() for c in policies.get("allowed_categories", [])]
    approval_threshold = policies.get("human_approval_threshold", 7500)

    # --- Hard rule: category ---
    if allowed_categories and category.lower() not in allowed_categories:
        reasons.append(f"Category '{category}' is not permitted. Allowed: {policies.get('allowed_categories')}")
        return PolicyResult(decision="DENY", allowed=False, reasons=reasons, requires_human_approval=False)

    # --- Hard rule: quantity ---
    if quantity > max_qty:
        reasons.append(f"Quantity {quantity} exceeds maximum allowed {max_qty}.")
        return PolicyResult(decision="DENY", allowed=False, reasons=reasons, requires_human_approval=False)

    # --- Hard rule: transaction amount ---
    if amount > max_amount:
        reasons.append(f"Transaction amount Rs.{amount:,.0f} exceeds hard limit of Rs.{max_amount:,.0f}.")
        return PolicyResult(decision="DENY", allowed=False, reasons=reasons, requires_human_approval=False)

    # --- Hard rule: daily spending limit ---
    from datetime import datetime
    today_start = datetime.combine(date.today(), datetime.min.time())
    daily_spent = db.query(Transaction).filter(
        Transaction.payment_status == "paid",
        Transaction.created_at >= today_start
    ).all()
    total_spent_today = sum(t.amount for t in daily_spent)

    if total_spent_today + amount > daily_limit:
        reasons.append(
            f"Daily limit of Rs.{daily_limit:,.0f} would be exceeded. "
            f"Already spent: Rs.{total_spent_today:,.0f}, requested: Rs.{amount:,.0f}."
        )
        return PolicyResult(decision="DENY", allowed=False, reasons=reasons, requires_human_approval=False)

    # --- Soft rule: human approval threshold ---
    if amount > approval_threshold:
        reasons.append(
            f"Transaction amount Rs.{amount:,.0f} exceeds auto-approval threshold of Rs.{approval_threshold:,.0f}. "
            f"Human approval required."
        )
        return PolicyResult(decision="REVIEW", allowed=True, reasons=reasons, requires_human_approval=True)

    # --- All checks passed ---
    reasons.append("All policy checks passed.")
    return PolicyResult(decision="APPROVE", allowed=True, reasons=reasons, requires_human_approval=False)
