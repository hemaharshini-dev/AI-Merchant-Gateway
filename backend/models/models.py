from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from db.database import Base

def new_uuid():
    return str(uuid.uuid4())

def now_utc():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    currency = Column(String, default="INR")
    policies = Column(JSON, nullable=False)

    products = relationship("Product", back_populates="merchant")


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=new_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, default=0)
    attributes = Column(JSON, default=dict)
    shipping = Column(JSON, default=dict)
    return_policy = Column(String, default="7 days")
    tags = Column(JSON, default=list)

    merchant = relationship("Merchant", back_populates="products")


class AIBuyer(Base):
    __tablename__ = "ai_buyers"

    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    spending_limits = Column(JSON, default=dict)
    permitted_categories = Column(JSON, default=list)


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(String, primary_key=True, default=new_uuid)
    buyer_id = Column(String, ForeignKey("ai_buyers.id"), nullable=False)
    natural_language_request = Column(Text, nullable=False)
    parsed_constraints = Column(JSON, default=dict)
    selected_products = Column(JSON, default=list)
    calculated_amount = Column(Float, default=0.0)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=now_utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=new_uuid)
    purchase_request_id = Column(String, ForeignKey("purchase_requests.id"), nullable=False)
    amount = Column(Float, nullable=False)
    policy_decision = Column(String)        # APPROVE / REVIEW / DENY
    policy_reasons = Column(JSON, default=list)
    approval_status = Column(String, default="pending")  # pending / approved / rejected
    razorpay_order_id = Column(String)
    payment_status = Column(String, default="pending")   # pending / paid / failed
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)

    audit_events = relationship("AuditEvent", back_populates="transaction")
    upsell_suggestions = relationship("UpsellSuggestion", back_populates="transaction")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=new_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    event_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=now_utc)

    transaction = relationship("Transaction", back_populates="audit_events")


class UpsellSuggestion(Base):
    __tablename__ = "upsell_suggestions"

    id = Column(String, primary_key=True, default=new_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=False)
    suggested_product_id = Column(String, ForeignKey("products.id"), nullable=False)
    reason = Column(Text, nullable=False)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now_utc)

    transaction = relationship("Transaction", back_populates="upsell_suggestions")
    product = relationship("Product")
