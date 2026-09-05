from langchain_core.tools import tool
from sqlalchemy.orm import Session
from models.models import Product, Merchant, Transaction, PurchaseRequest, AuditEvent, UpsellSuggestion
from services.policy_engine import evaluate_policy
from services import razorpay_service
from datetime import datetime, timezone


# --- Tool: search_products ---
@tool
def search_products(query: str, category: str = "", max_price: float = 0, quantity: int = 1) -> str:
    """Search the merchant catalog. Provide query keywords, optional category, max_price, quantity."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        q = db.query(Product).filter(Product.inventory >= quantity)
        if category:
            q = q.filter(Product.category.ilike(f"%{category}%"))
        if max_price > 0:
            q = q.filter(Product.price <= max_price)
        products = q.all()
        if query:
            kw = query.lower()
            products = [
                p for p in products
                if kw in p.name.lower()
                or kw in (p.description or "").lower()
                or any(kw in t.lower() for t in (p.tags or []))
            ]
        if not products:
            return "No products found matching the criteria."
        lines = []
        for p in products[:8]:
            lines.append(f"ID:{p.id} | {p.name} | Rs.{p.price} | Stock:{p.inventory} | {p.category} | Attrs:{p.attributes}")
        return "\n".join(lines)
    finally:
        db.close()


# --- Tool: get_product_details ---
@tool
def get_product_details(product_id: str) -> str:
    """Get full details of a product by its ID."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return f"Product {product_id} not found."
        return (
            f"ID:{p.id} | Name:{p.name} | Category:{p.category} | Price:Rs.{p.price} "
            f"| Stock:{p.inventory} | Attrs:{p.attributes} | Shipping:{p.shipping} "
            f"| Return:{p.return_policy} | Tags:{p.tags}"
        )
    finally:
        db.close()


# --- Tool: check_inventory ---
@tool
def check_inventory(product_id: str, quantity: int) -> str:
    """Check if a product has sufficient inventory for the requested quantity."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return f"Product {product_id} not found."
        if p.inventory >= quantity:
            return f"IN_STOCK: {p.name} has {p.inventory} units. Requested {quantity} — available."
        return f"INSUFFICIENT_STOCK: {p.name} has only {p.inventory} units. Requested {quantity}."
    finally:
        db.close()


# --- Tool: get_merchant_policy ---
@tool
def get_merchant_policy() -> str:
    """Get the merchant's transaction policies."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).filter(Merchant.id == "merchant_techkart").first()
        p = merchant.policies
        return (
            f"Merchant: {merchant.name} | Currency: {merchant.currency} | "
            f"Max transaction: Rs.{p['max_transaction_amount']} | "
            f"Daily limit: Rs.{p['daily_spending_limit']} | "
            f"Max quantity: {p['max_quantity']} | "
            f"Allowed categories: {p['allowed_categories']} | "
            f"Auto-approval threshold: Rs.{p['human_approval_threshold']}"
        )
    finally:
        db.close()


# --- Tool: calculate_order_total ---
@tool
def calculate_order_total(product_id: str, quantity: int) -> str:
    """Calculate the total cost for a product and quantity."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            return f"Product {product_id} not found."
        total = p.price * quantity
        return f"Product:{p.name} | Unit price:Rs.{p.price} | Qty:{quantity} | Total:Rs.{total}"
    finally:
        db.close()


# --- Tool: evaluate_transaction_policy ---
@tool
def evaluate_transaction_policy(amount: float, category: str, quantity: int) -> str:
    """Evaluate a proposed transaction against merchant policies. Returns APPROVE, REVIEW, or DENY."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        merchant = db.query(Merchant).filter(Merchant.id == "merchant_techkart").first()
        result = evaluate_policy(amount, category, quantity, merchant.policies, db)
        return (
            f"DECISION:{result.decision} | "
            f"ALLOWED:{result.allowed} | "
            f"HUMAN_APPROVAL_REQUIRED:{result.requires_human_approval} | "
            f"REASONS:{'; '.join(result.reasons)}"
        )
    finally:
        db.close()


# --- Tool: create_razorpay_order ---
@tool
def create_razorpay_order(transaction_id: str) -> str:
    """Create a Razorpay order for an APPROVED transaction. Only callable after policy evaluation passes."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return f"Transaction {transaction_id} not found."
        if tx.policy_decision != "APPROVE" or tx.approval_status != "approved":
            return f"BLOCKED: Cannot create order. Decision={tx.policy_decision}, Approval={tx.approval_status}"
        if tx.razorpay_order_id:
            return f"Order already exists: {tx.razorpay_order_id}"
        order = razorpay_service.create_order(tx.amount, tx.id[:40], {"transaction_id": tx.id})
        tx.razorpay_order_id = order["id"]
        tx.payment_status = "created"
        tx.updated_at = datetime.now(timezone.utc)
        db.add(AuditEvent(
            transaction_id=tx.id,
            event_type="RAZORPAY_ORDER_CREATED",
            description=f"Razorpay order created: {order['id']}",
            event_metadata={"razorpay_order_id": order["id"]},
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        return f"ORDER_CREATED: razorpay_order_id={order['id']} | amount_paise={order['amount']} | status={order['status']}"
    finally:
        db.close()


# --- Tool: get_payment_status ---
@tool
def get_payment_status(transaction_id: str) -> str:
    """Get the current payment status of a transaction."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return f"Transaction {transaction_id} not found."
        if not tx.razorpay_order_id:
            return f"No Razorpay order yet. Payment status: {tx.payment_status}"
        order = razorpay_service.fetch_order(tx.razorpay_order_id)
        return (
            f"transaction_id={tx.id} | razorpay_order_id={tx.razorpay_order_id} | "
            f"payment_status={tx.payment_status} | razorpay_status={order.get('status')}"
        )
    finally:
        db.close()


# --- Tool: request_human_approval ---
@tool
def request_human_approval(transaction_id: str) -> str:
    """Flag a transaction as requiring human approval (REVIEW state)."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return f"Transaction {transaction_id} not found."
        tx.approval_status = "pending_human"
        tx.updated_at = datetime.now(timezone.utc)
        db.add(AuditEvent(
            transaction_id=tx.id,
            event_type="HUMAN_APPROVAL_REQUESTED",
            description="Transaction requires human approval before payment can proceed.",
            event_metadata={"amount": tx.amount, "policy_decision": tx.policy_decision},
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        return f"PENDING_HUMAN_APPROVAL: Transaction {transaction_id} is awaiting merchant review."
    finally:
        db.close()


# --- Tool: get_upsell_suggestions ---
@tool
def get_upsell_suggestions(transaction_id: str) -> str:
    """Get upsell product suggestions after a successful payment. Only call after payment is confirmed."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return "Transaction not found."
        if tx.payment_status != "paid":
            return "Upsell suggestions are only available after successful payment."

        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == tx.purchase_request_id).first()
        purchased_ids = [item["product_id"] for item in (pr.selected_products or [])]
        if not purchased_ids:
            return "No purchased products found."

        purchased = db.query(Product).filter(Product.id.in_(purchased_ids)).all()
        purchased_tags = set()
        purchased_categories = set()
        for p in purchased:
            purchased_categories.add(p.category)
            for tag in (p.tags or []):
                purchased_tags.add(tag.lower())

        accessory_tags = {"accessories", "desk", "ergonomic", "usb-c", "wrist rest"}
        relevant_tags = purchased_tags | accessory_tags

        candidates = db.query(Product).filter(
            Product.id.notin_(purchased_ids),
            Product.inventory > 0,
            Product.category.in_(purchased_categories)
        ).all()

        candidates.sort(
            key=lambda p: len(set(t.lower() for t in (p.tags or [])) & relevant_tags),
            reverse=True
        )
        top = candidates[:3]

        # Persist suggestions
        existing = db.query(UpsellSuggestion).filter(UpsellSuggestion.transaction_id == transaction_id).first()
        if not existing:
            for p in top:
                matched = set(t.lower() for t in (p.tags or [])) & relevant_tags
                db.add(UpsellSuggestion(
                    transaction_id=transaction_id,
                    suggested_product_id=p.id,
                    reason=f"Complements your purchase — matches: {', '.join(list(matched)[:3])}",
                ))
            db.commit()

        if not top:
            return "No upsell suggestions available."

        lines = [f"You may also like:"]
        for p in top:
            matched = set(t.lower() for t in (p.tags or [])) & relevant_tags
            lines.append(f"- {p.name} | Rs.{p.price} | {', '.join(list(matched)[:3])}")
        return "\n".join(lines)
    finally:
        db.close()


# --- Tool: update_transaction ---
@tool
def update_transaction(transaction_id: str, amount: float, category: str, quantity: int) -> str:
    """Update the transaction record with the calculated amount, category and quantity after product selection. Call this before evaluate_transaction_policy."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return f"Transaction {transaction_id} not found."
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == tx.purchase_request_id).first()
        tx.amount = amount
        # store category+quantity in purchase_request parsed_constraints
        pr.parsed_constraints = {"category": category, "quantity": quantity, "amount": amount}
        db.add(AuditEvent(
            transaction_id=tx.id,
            event_type="TRANSACTION_CALCULATED",
            description=f"Transaction amount set to Rs.{amount} for {quantity}x {category} item(s).",
            event_metadata={"amount": amount, "category": category, "quantity": quantity},
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        return f"Transaction updated: amount=Rs.{amount}, category={category}, quantity={quantity}"
    finally:
        db.close()


# --- Tool: record_policy_decision ---
@tool
def record_policy_decision(transaction_id: str, decision: str, reasons: str) -> str:
    """Record the policy decision (APPROVE/REVIEW/DENY) on the transaction after evaluate_transaction_policy. Always call this after evaluate_transaction_policy."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return f"Transaction {transaction_id} not found."
        tx.policy_decision = decision
        tx.policy_reasons = [reasons]
        if decision == "APPROVE":
            tx.approval_status = "approved"
        elif decision == "DENY":
            tx.approval_status = "rejected"
        # REVIEW stays as pending_human (set by request_human_approval)
        db.add(AuditEvent(
            transaction_id=tx.id,
            event_type=f"POLICY_{decision}",
            description=f"Policy decision: {decision}. {reasons}",
            event_metadata={"decision": decision, "reasons": reasons},
            timestamp=datetime.now(timezone.utc)
        ))
        db.commit()
        return f"Policy decision recorded: {decision}"
    finally:
        db.close()


# --- Tool: record_selected_products ---
@tool
def record_selected_products(purchase_request_id: str, product_id: str, product_name: str, quantity: int, unit_price: float) -> str:
    """Record the selected product on the purchase request."""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == purchase_request_id).first()
        if not pr:
            return f"PurchaseRequest {purchase_request_id} not found."
        pr.selected_products = [{"product_id": product_id, "name": product_name, "quantity": quantity, "unit_price": unit_price, "total": unit_price * quantity}]
        pr.calculated_amount = unit_price * quantity
        db.commit()
        return f"Selected product recorded: {product_name} x{quantity} @ Rs.{unit_price} = Rs.{unit_price*quantity}"
    finally:
        db.close()


ALL_TOOLS = [
    search_products,
    get_product_details,
    check_inventory,
    get_merchant_policy,
    calculate_order_total,
    update_transaction,
    record_selected_products,
    evaluate_transaction_policy,
    record_policy_decision,
    create_razorpay_order,
    get_payment_status,
    request_human_approval,
    get_upsell_suggestions,
]
