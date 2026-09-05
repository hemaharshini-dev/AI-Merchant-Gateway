from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from models.models import Product, Merchant

router = APIRouter(prefix="/catalog", tags=["Catalog"])


# --- Schemas ---

class ProductOut(BaseModel):
    id: str
    name: str
    description: str | None
    category: str
    price: float
    inventory: int
    attributes: dict
    shipping: dict
    return_policy: str
    tags: list

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    category: Optional[str] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    in_stock: Optional[bool] = True
    attributes: Optional[dict] = None
    quantity: Optional[int] = 1
    query: Optional[str] = None


class UpsellRequest(BaseModel):
    purchased_product_ids: list[str]


# --- Helpers ---

def product_matches_attributes(product: Product, required: dict) -> bool:
    for key, value in required.items():
        attr_val = product.attributes.get(key, "")
        if isinstance(value, str) and isinstance(attr_val, str):
            if value.lower() not in attr_val.lower():
                return False
        elif attr_val != value:
            return False
    return True


def score_product(product: Product, request: SearchRequest) -> int:
    score = 0
    if request.query:
        q = request.query.lower()
        if q in product.name.lower():
            score += 3
        if q in (product.description or "").lower():
            score += 1
        if any(q in tag.lower() for tag in (product.tags or [])):
            score += 2
    return score


# --- Endpoints ---

@router.get("/products", response_model=list[ProductOut])
def list_products(
    category: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(True),
    db: Session = Depends(get_db)
):
    q = db.query(Product)
    if category:
        q = q.filter(Product.category.ilike(f"%{category}%"))
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if in_stock:
        q = q.filter(Product.inventory > 0)
    return q.all()


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/inventory/{product_id}")
def check_inventory(product_id: str, quantity: int = Query(1), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Product not found")
    return {
        "product_id": product_id,
        "name": product.name,
        "requested_quantity": quantity,
        "available_inventory": product.inventory,
        "in_stock": product.inventory >= quantity
    }


@router.post("/search", response_model=list[ProductOut])
def search_products(request: SearchRequest, db: Session = Depends(get_db)):
    q = db.query(Product)

    if request.category:
        q = q.filter(Product.category.ilike(f"%{request.category}%"))
    if request.max_price is not None:
        q = q.filter(Product.price <= request.max_price)
    if request.min_price is not None:
        q = q.filter(Product.price >= request.min_price)
    if request.in_stock:
        qty = request.quantity or 1
        q = q.filter(Product.inventory >= qty)

    products = q.all()

    # Filter by attributes if provided
    if request.attributes:
        products = [p for p in products if product_matches_attributes(p, request.attributes)]

    # Filter by query keyword across name, description, tags
    if request.query:
        kw = request.query.lower()
        products = [
            p for p in products
            if kw in p.name.lower()
            or kw in (p.description or "").lower()
            or any(kw in tag.lower() for tag in (p.tags or []))
        ]

    # Sort by relevance score descending
    products.sort(key=lambda p: score_product(p, request), reverse=True)

    return products


@router.post("/upsell")
def get_upsell_suggestions(request: UpsellRequest, db: Session = Depends(get_db)):
    purchased = db.query(Product).filter(Product.id.in_(request.purchased_product_ids)).all()
    if not purchased:
        return {"suggestions": []}

    purchased_ids = set(request.purchased_product_ids)
    purchased_tags = set()
    purchased_categories = set()

    for p in purchased:
        purchased_categories.add(p.category)
        for tag in (p.tags or []):
            purchased_tags.add(tag.lower())

    # Accessory tag keywords that complement any purchase
    accessory_tags = {"accessories", "desk", "ergonomic", "usb-c", "cable management", "wrist rest"}
    relevant_tags = purchased_tags | accessory_tags

    candidates = db.query(Product).filter(
        Product.id.notin_(purchased_ids),
        Product.inventory > 0,
        Product.category.in_(purchased_categories)
    ).all()

    def suggestion_score(product: Product) -> int:
        product_tags = set(t.lower() for t in (product.tags or []))
        return len(product_tags & relevant_tags)

    candidates.sort(key=suggestion_score, reverse=True)
    top = candidates[:3]

    suggestions = []
    for p in top:
        product_tags = set(t.lower() for t in (p.tags or []))
        matched = product_tags & relevant_tags
        reason = f"Complements your purchase — matches: {', '.join(list(matched)[:3])}"
        suggestions.append({
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "reason": reason
        })

    return {"suggestions": suggestions}
