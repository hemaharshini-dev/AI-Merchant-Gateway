# AI Merchant Gateway

> Making merchants discoverable, purchasable, and safely transactable by AI buyers.

**Razorpay Track 01 — AI Growth & Agentic Commerce**

---

## What This Is

An AI-native merchant infrastructure layer that makes a merchant's catalog transactable by autonomous AI buyers — with every financial action bounded, explainable, and gated.

An AI buyer sends a natural language request. The system searches the catalog, selects products, evaluates the transaction against deterministic merchant policies, routes for human approval if needed, and executes payment via Razorpay Test Mode. Every decision is recorded in a full audit trail.

---

## Architecture

```
AI Buyer (natural language)
        ↓
LangGraph Agent (intent → tool orchestration)
        ↓
Merchant Catalog API  →  Policy Engine (deterministic)
                                ↓
                    APPROVE / REVIEW / DENY
                         ↓         ↓
                   Razorpay    Human Approval Gate
                   Test Mode        ↓
                         ↓    Approve / Reject
                    Payment
                         ↓
                   Audit Trail + Upsell Suggestions
```

**Key principle:** The LLM reasons and selects products. A deterministic policy engine enforces all financial rules. The LLM can never bypass merchant-defined limits.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python 3.13 + FastAPI |
| Agent | LangGraph + Groq (openai/gpt-oss-120b) |
| Database | SQLite (PostgreSQL-ready) |
| Payments | Razorpay Test Mode |

---

## Project Structure

```
AI-Merchant-Gateway/
├── backend/
│   ├── agent/
│   │   ├── graph.py          # LangGraph state machine
│   │   └── tools.py          # All agent tools
│   ├── db/
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   └── seed.py           # Merchant, products, buyer seed data
│   ├── models/
│   │   └── models.py         # All DB models
│   ├── routes/
│   │   ├── agent.py          # POST /agent/purchase
│   │   ├── approvals.py      # Human approval flow
│   │   ├── audit.py          # Audit trail endpoints
│   │   ├── catalog.py        # Product catalog + search + upsell
│   │   ├── merchant.py       # Merchant info + policy
│   │   ├── payments.py       # Razorpay order + webhook
│   │   └── policy.py         # Policy evaluation endpoint
│   ├── services/
│   │   ├── policy_engine.py  # Deterministic policy engine (zero LLM)
│   │   ├── razorpay_service.py
│   │   └── upsell_service.py
│   ├── config.py             # Pydantic settings from .env
│   ├── main.py               # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── BuyerView.jsx     # AI Buyer chat interface
│   │   │   ├── Dashboard.jsx     # Merchant dashboard
│   │   │   ├── Approvals.jsx     # Human approval flow
│   │   │   ├── Transactions.jsx  # All transactions list
│   │   │   └── TransactionDetail.jsx  # Audit trail view
│   │   ├── api.js            # Centralized API client
│   │   ├── App.jsx           # Router + sidebar layout
│   │   ├── main.jsx          # Entry point
│   │   └── index.css         # Global design system
│   ├── package.json
│   └── vite.config.js
├── tests/
│   └── test_policy_engine.py # 10 deterministic policy tests
├── problem_statement.md
├── plan_of_action.md
├── TROUBLESHOOTING.md
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.13+
- Node 22+
- Razorpay Test Mode account
- Groq API key (free tier at console.groq.com)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Create `backend/.env`:
```env
RAZORPAY_KEY_ID=rzp_test_your_key_here
RAZORPAY_KEY_SECRET=your_secret_here
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./ai_merchant_gateway.db
```

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

API docs: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

| Page | URL | Description |
|---|---|---|
| AI Buyer | `http://localhost:5173/` | Chat interface for purchase requests |
| Dashboard | `http://localhost:5173/dashboard` | Merchant overview + stats |
| Approvals | `http://localhost:5173/approvals` | Human approval queue |
| Transactions | `http://localhost:5173/transactions` | All transactions list |
| Transaction Detail | `http://localhost:5173/transactions/:id` | Full audit trail |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/catalog/products` | List all products |
| POST | `/catalog/search` | Search by constraints |
| POST | `/catalog/upsell` | Get upsell suggestions |
| GET | `/merchant/policy` | Get merchant policies |
| POST | `/policy/evaluate` | Evaluate a transaction |
| POST | `/agent/purchase` | Run full AI purchase flow |
| GET | `/approvals/pending` | List pending human approvals |
| POST | `/approvals/{id}/approve` | Approve a transaction |
| POST | `/approvals/{id}/reject` | Reject a transaction |
| POST | `/payments/create-order` | Create Razorpay order |
| GET | `/payments/status/{id}` | Get payment status |
| POST | `/payments/verify` | Verify payment signature |
| GET | `/audit/{id}` | Full audit trail for a transaction |
| GET | `/audit/transactions/all` | All transactions |
| GET | `/audit/recent/all` | Recent audit events |

---

## Demo Scenarios

### ACT 1 — Auto Approve
```json
POST /agent/purchase
{ "request": "I need one wireless mouse under Rs.1000" }
```
Expected: `policy_decision: APPROVE`, Razorpay order created automatically.

### ACT 2 — Human Review
```json
POST /agent/purchase
{ "request": "I need two webcams for our office" }
```
Expected: `policy_decision: REVIEW`, transaction held for merchant approval.

### ACT 3 — Hard Block
```json
POST /agent/purchase
{ "request": "Buy five 27 inch monitors for our design team" }
```
Expected: `policy_decision: DENY`, no order created, reason explained.

---

## Merchant Policies (TechKart)

```json
{
  "max_transaction_amount": 10000,
  "daily_spending_limit": 30000,
  "max_quantity": 5,
  "allowed_categories": ["Electronics", "Office Equipment"],
  "human_approval_threshold": 7500
}
```

---

## Important Notes

- Always start the **backend first**, then the frontend
- Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173`
- If you see a **Network Error** in the frontend, the backend is not running or CORS is misconfigured
- Always use `Ctrl+C` to stop uvicorn — closing the terminal leaves orphan processes on port 8000
- If port 8000 is stuck: `taskkill /IM python.exe /F` then restart

---

## Running Tests

```bash
cd AI-Merchant-Gateway
backend\.venv\Scripts\python.exe tests\test_policy_engine.py
```

Expected: 10/10 PASS, zero unauthorized transactions, zero policy bypasses.

---

## Security

- Razorpay secret key never sent to frontend
- All financial actions validated server-side before Razorpay API call
- LLM cannot directly call Razorpay — must go through gated tools
- Webhook signature verified via HMAC-SHA256
- `.env` never committed (in `.gitignore`)
