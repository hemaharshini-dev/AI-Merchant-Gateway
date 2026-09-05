"""
Demo Reset Script
Clears all transactions, purchase requests, audit events, and upsell suggestions
so the demo starts from a clean state. Keeps merchant, products, and AI buyer intact.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from db.database import SessionLocal
from models.models import Transaction, PurchaseRequest, AuditEvent, UpsellSuggestion

def reset():
    db = SessionLocal()
    try:
        u = db.query(UpsellSuggestion).delete()
        a = db.query(AuditEvent).delete()
        t = db.query(Transaction).delete()
        p = db.query(PurchaseRequest).delete()
        db.commit()
        print(f"Demo reset complete.")
        print(f"  Deleted: {p} purchase requests, {t} transactions, {a} audit events, {u} upsell suggestions")
        print(f"  Merchant, products, and AI buyer are intact.")
        print(f"  Ready for demo.")
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("Reset demo data? This clears all transactions. (yes/no): ").strip().lower()
    if confirm == "yes":
        reset()
    else:
        print("Cancelled.")
