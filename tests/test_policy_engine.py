import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from unittest.mock import MagicMock
from services.policy_engine import evaluate_policy

POLICIES = {
    "max_transaction_amount": 10000,
    "daily_spending_limit": 30000,
    "max_quantity": 5,
    "allowed_categories": ["Electronics", "Office Equipment"],
    "human_approval_threshold": 7500
}

def make_db(daily_spent=0):
    """Mock DB that returns a fixed daily spend total."""
    mock_txs = []
    if daily_spent > 0:
        mock_tx = MagicMock()
        mock_tx.amount = daily_spent
        mock_txs = [mock_tx]

    # policy_engine does: db.query(Transaction).filter(...).filter(...).all()
    mock_all = MagicMock(return_value=mock_txs)
    mock_inner_filter = MagicMock()
    mock_inner_filter.all = mock_all
    mock_inner_filter.filter = MagicMock(return_value=mock_inner_filter)

    mock_query_obj = MagicMock()
    mock_query_obj.filter = MagicMock(return_value=mock_inner_filter)

    db = MagicMock()
    db.query = MagicMock(return_value=mock_query_obj)
    return db


def test(name, result, expected_decision):
    status = "PASS" if result.decision == expected_decision else "FAIL"
    print(f"[{status}] {name}: got={result.decision} expected={expected_decision} | {result.reasons[0]}")
    assert result.decision == expected_decision, f"FAILED: {name}"


# APPROVE cases
test("Low value auto-approve",
     evaluate_policy(4500, "Electronics", 1, POLICIES, make_db()),
     "APPROVE")

test("Exactly at approval threshold",
     evaluate_policy(7500, "Office Equipment", 1, POLICIES, make_db()),
     "APPROVE")

test("Multi-item within limits",
     evaluate_policy(7497, "Office Equipment", 3, POLICIES, make_db()),
     "APPROVE")

# REVIEW cases
test("Above approval threshold, below hard limit",
     evaluate_policy(9000, "Electronics", 1, POLICIES, make_db()),
     "REVIEW")

test("Just above threshold",
     evaluate_policy(7501, "Office Equipment", 2, POLICIES, make_db()),
     "REVIEW")

# DENY cases
test("Exceeds hard transaction limit",
     evaluate_policy(44995, "Electronics", 5, POLICIES, make_db()),
     "DENY")

test("Exceeds max quantity",
     evaluate_policy(2000, "Electronics", 6, POLICIES, make_db()),
     "DENY")

test("Disallowed category",
     evaluate_policy(500, "Clothing", 1, POLICIES, make_db()),
     "DENY")

test("Daily limit exceeded",
     evaluate_policy(5000, "Electronics", 1, POLICIES, make_db(daily_spent=28000)),
     "DENY")

test("Exactly at hard limit — should REVIEW (above threshold)",
     evaluate_policy(10000, "Electronics", 1, POLICIES, make_db()),
     "REVIEW")

print("\nAll policy engine tests passed.")
