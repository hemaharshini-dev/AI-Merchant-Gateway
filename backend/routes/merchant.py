from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.database import get_db
from models.models import Merchant

router = APIRouter(prefix="/merchant", tags=["Merchant"])


class MerchantOut(BaseModel):
    id: str
    name: str
    currency: str
    policies: dict

    class Config:
        from_attributes = True


@router.get("/", response_model=MerchantOut)
def get_merchant(db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == "merchant_techkart").first()
    return merchant


@router.get("/policy")
def get_policy(db: Session = Depends(get_db)):
    merchant = db.query(Merchant).filter(Merchant.id == "merchant_techkart").first()
    return {"merchant_id": merchant.id, "merchant_name": merchant.name, "policies": merchant.policies}
