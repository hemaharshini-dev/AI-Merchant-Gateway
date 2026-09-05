from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.graph import run_purchase_agent

router = APIRouter(prefix="/agent", tags=["Agent"])


class PurchaseRequest(BaseModel):
    request: str
    buyer_id: str = "buyer_office_agent"


@router.post("/purchase")
def purchase(body: PurchaseRequest):
    try:
        result = run_purchase_agent(body.request, body.buyer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
