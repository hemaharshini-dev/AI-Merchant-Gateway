from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import engine
from models.models import Base
from db.seed import seed
from routes.catalog import router as catalog_router
from routes.merchant import router as merchant_router
from routes.policy import router as policy_router
from routes.payments import router as payments_router
from routes.agent import router as agent_router
from routes.approvals import router as approvals_router
from routes.audit import router as audit_router

Base.metadata.create_all(bind=engine)
seed()

app = FastAPI(title="AI Merchant Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router)
app.include_router(merchant_router)
app.include_router(policy_router)
app.include_router(payments_router)
app.include_router(agent_router)
app.include_router(approvals_router)
app.include_router(audit_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "AI Merchant Gateway"}
