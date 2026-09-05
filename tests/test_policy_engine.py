"""
AI Merchant Gateway — Automated Test Suite
Phase 9: 50+ deterministic scenarios covering all policy branches.

Metrics tracked:
- Policy decision accuracy
- Unauthorized transactions (must be 0)
- Policy bypasses (must be 0)
- Correct DENY rate
- Correct REVIEW rate
- Correct APPROVE rate
"""

import sys
import os
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from unittest.mock import MagicMock
from services.policy_engine import evaluate_policy

# ── Policies ────────────────────────────────────────────────────────────────
POLICIES = {
    "max_transaction_amount": 10000,
    "daily_spending_limit": 30000,
    "max_quantity": 5,
    "allowed_categories": ["Electronics", "Office Equipment"],
    "human_approval_threshold": 7500
}

# ── Mock DB factory ──────────────────────────────────────────────────────────
def make_db(daily_spent=0):
    mock_txs = []
    if daily_spent > 0:
        t = MagicMock()
        t.amount = daily_spent
        mock_txs = [t]
    f = MagicMock()
    f.all.return_value = mock_txs
    f.filter = MagicMock(return_value=f)
    q = MagicMock()
    q.filter = MagicMock(return_value=f)
    db = MagicMock()
    db.query.return_value = q
    return db

# ── Test runner ──────────────────────────────────────────────────────────────
results = []

def run(name, amount, category, quantity, expected, daily_spent=0):
    result = evaluate_policy(amount, category, quantity, POLICIES, make_db(daily_spent))
    passed = result.decision == expected
    results.append({
        "name": name,
        "expected": expected,
        "got": result.decision,
        "passed": passed,
        "reason": result.reasons[0] if result.reasons else ""
    })
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    if not passed:
        print(f"       Expected={expected} Got={result.decision} | {result.reasons[0]}")

# ════════════════════════════════════════════════════════════════════════════
# APPROVE SCENARIOS (amount <= threshold, all rules pass)
# ════════════════════════════════════════════════════════════════════════════
print("\n── APPROVE SCENARIOS ──────────────────────────────────────────")

run("Minimal purchase - Rs.100 Electronics",                    100,   "Electronics",      1, "APPROVE")
run("Low value Office Equipment",                               500,   "Office Equipment", 1, "APPROVE")
run("Mid value Electronics qty 1",                             3000,   "Electronics",      1, "APPROVE")
run("Exactly at threshold Rs.7500",                            7500,   "Electronics",      1, "APPROVE")
run("Multi-item within limits - 3 items",                      7497,   "Office Equipment", 3, "APPROVE")
run("Max quantity 5 low value",                                2500,   "Electronics",      5, "APPROVE")
run("Office Equipment qty 2 under threshold",                  6000,   "Office Equipment", 2, "APPROVE")
run("Electronics qty 1 just under threshold",                  7499,   "Electronics",      1, "APPROVE")
run("Small daily spend already exists",                        5000,   "Electronics",      1, "APPROVE", daily_spent=10000)
run("Daily spend well within limit",                           1000,   "Office Equipment", 1, "APPROVE", daily_spent=5000)
run("Rs.1 transaction",                                           1,   "Electronics",      1, "APPROVE")
run("Qty 1 Office Equipment low value",                         899,   "Office Equipment", 1, "APPROVE")
run("Qty 4 within max_quantity",                               6000,   "Electronics",      4, "APPROVE")
run("Zero daily spend Electronics",                            7000,   "Electronics",      1, "APPROVE")
run("Zero daily spend Office Equipment",                       4999,   "Office Equipment", 2, "APPROVE")

# ════════════════════════════════════════════════════════════════════════════
# REVIEW SCENARIOS (amount > threshold but <= max_transaction_amount)
# ════════════════════════════════════════════════════════════════════════════
print("\n── REVIEW SCENARIOS ───────────────────────────────────────────")

run("Just above threshold Rs.7501",                            7501,   "Electronics",      1, "REVIEW")
run("Rs.8000 Electronics",                                     8000,   "Electronics",      1, "REVIEW")
run("Rs.9000 Office Equipment",                                9000,   "Office Equipment", 1, "REVIEW")
run("Rs.9999 Electronics",                                     9999,   "Electronics",      1, "REVIEW")
run("Exactly at hard limit Rs.10000",                         10000,   "Electronics",      1, "REVIEW")
run("Rs.8500 qty 1",                                           8500,   "Office Equipment", 1, "REVIEW")
run("Rs.7600 Electronics",                                     7600,   "Electronics",      1, "REVIEW")
run("Rs.9500 qty 2 within max_qty",                            9500,   "Electronics",      2, "REVIEW")
run("Rs.8000 with some daily spend",                           8000,   "Electronics",      1, "REVIEW", daily_spent=5000)
run("Rs.7501 Office Equipment qty 1",                          7501,   "Office Equipment", 1, "REVIEW")

# ════════════════════════════════════════════════════════════════════════════
# DENY — Exceeds hard transaction limit
# ════════════════════════════════════════════════════════════════════════════
print("\n── DENY: Exceeds hard transaction limit ───────────────────────")

run("Rs.10001 just over hard limit",                          10001,   "Electronics",      1, "DENY")
run("Rs.15000 Electronics",                                   15000,   "Electronics",      1, "DENY")
run("Rs.44995 five monitors",                                 44995,   "Electronics",      5, "DENY")
run("Rs.50000 bulk order",                                    50000,   "Office Equipment", 3, "DENY")
run("Rs.100000 extreme value",                               100000,   "Electronics",      1, "DENY")
run("Rs.20000 Office Equipment",                              20000,   "Office Equipment", 2, "DENY")
run("Rs.11000 Electronics",                                   11000,   "Electronics",      1, "DENY")
run("Rs.12500 qty 2",                                         12500,   "Electronics",      2, "DENY")

# ════════════════════════════════════════════════════════════════════════════
# DENY — Exceeds max quantity
# ════════════════════════════════════════════════════════════════════════════
print("\n── DENY: Exceeds max quantity ─────────────────────────────────")

run("Qty 6 low value",                                         1000,   "Electronics",      6, "DENY")
run("Qty 10 Office Equipment",                                 2000,   "Office Equipment",10, "DENY")
run("Qty 6 exactly over limit",                                3000,   "Electronics",      6, "DENY")
run("Qty 100 extreme",                                          500,   "Office Equipment",100,"DENY")
run("Qty 6 high value",                                        9000,   "Electronics",      6, "DENY")

# ════════════════════════════════════════════════════════════════════════════
# DENY — Disallowed category
# ════════════════════════════════════════════════════════════════════════════
print("\n── DENY: Disallowed category ──────────────────────────────────")

run("Clothing category",                                        500,   "Clothing",         1, "DENY")
run("Food category",                                           1000,   "Food",             1, "DENY")
run("Furniture category",                                      3000,   "Furniture",        1, "DENY")
run("Automotive category",                                     5000,   "Automotive",       1, "DENY")
run("Jewellery category",                                      2000,   "Jewellery",        1, "DENY")
run("Books category",                                           200,   "Books",            1, "DENY")
run("Sports category",                                         1500,   "Sports",           2, "DENY")

# ════════════════════════════════════════════════════════════════════════════
# DENY — Daily spending limit exceeded
# ════════════════════════════════════════════════════════════════════════════
print("\n── DENY: Daily spending limit exceeded ────────────────────────")

run("Daily limit exactly exceeded",                            5000,   "Electronics",      1, "DENY", daily_spent=28000)
run("Daily limit Rs.29999 + Rs.2 = over",                        2,   "Electronics",      1, "DENY", daily_spent=29999)
run("Daily limit already at max",                              1000,   "Office Equipment", 1, "DENY", daily_spent=30000)
run("Daily limit Rs.25000 + Rs.6000 = over",                   6000,   "Electronics",      1, "DENY", daily_spent=25000)
run("Daily limit Rs.20000 + Rs.11000 = over (also hard limit)",11000,  "Electronics",      1, "DENY", daily_spent=20000)

# ════════════════════════════════════════════════════════════════════════════
# METRICS REPORT
# ════════════════════════════════════════════════════════════════════════════
total       = len(results)
passed      = sum(1 for r in results if r["passed"])
failed      = total - passed
approves    = [r for r in results if r["expected"] == "APPROVE"]
reviews     = [r for r in results if r["expected"] == "REVIEW"]
denies      = [r for r in results if r["expected"] == "DENY"]

approve_acc = sum(1 for r in approves if r["passed"]) / len(approves) * 100 if approves else 0
review_acc  = sum(1 for r in reviews  if r["passed"]) / len(reviews)  * 100 if reviews  else 0
deny_acc    = sum(1 for r in denies   if r["passed"]) / len(denies)   * 100 if denies   else 0

# Unauthorized = a DENY that got APPROVE (money moved when it shouldn't)
unauthorized = sum(1 for r in results if r["expected"] == "DENY" and r["got"] == "APPROVE")
# Policy bypass = any expected DENY/REVIEW that got APPROVE
bypasses     = sum(1 for r in results if r["expected"] in ("DENY", "REVIEW") and r["got"] == "APPROVE")

print("\n" + "=" * 60)
print("METRICS REPORT")
print("=" * 60)
print(f"Total scenarios      : {total}")
print(f"Passed               : {passed}")
print(f"Failed               : {failed}")
print(f"Overall accuracy     : {passed/total*100:.1f}%")
print(f"")
print(f"APPROVE accuracy     : {approve_acc:.1f}%  ({len(approves)} scenarios)")
print(f"REVIEW  accuracy     : {review_acc:.1f}%  ({len(reviews)} scenarios)")
print(f"DENY    accuracy     : {deny_acc:.1f}%  ({len(denies)} scenarios)")
print(f"")
print(f"Unauthorized txns    : {unauthorized}  (target: 0)")
print(f"Policy bypasses      : {bypasses}  (target: 0)")
print("=" * 60)

if failed > 0:
    print("\nFAILED SCENARIOS:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['name']}: expected={r['expected']} got={r['got']}")

assert unauthorized == 0, f"CRITICAL: {unauthorized} unauthorized transaction(s) detected!"
assert bypasses == 0,     f"CRITICAL: {bypasses} policy bypass(es) detected!"
assert passed == total,   f"{failed} test(s) failed."

print("\nAll tests passed. Zero unauthorized transactions. Zero policy bypasses.")
