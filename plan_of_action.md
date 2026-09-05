# Plan of Action — AI Merchant Gateway

## Build Philosophy

- Solid payment/policy primitives first, AI agent layer last
- Each phase produces a working, testable artifact
- Never hardcode credentials — `.env` only
- LLM reasons, policy engine enforces — never mix these responsibilities
- Upsell is a revenue-growth layer on top of a completed transaction — never a blocker to the core flow

---

## Phase 1 — Project Scaffold & Database

**Goal:** Runnable project skeleton with all entities persisted.

### Tasks
- Initialize repo structure: `backend/`, `frontend/`, `agent/`
- Set up FastAPI app with health check endpoint
- Set up SQLite with SQLAlchemy (PostgreSQL-ready models)
- Define and migrate all core entities:
  - `Merchant` (id, name, currency, policies JSON)
  - `Product` (id, merchant_id, name, description, category, price, inventory, attributes JSON, shipping JSON, return_policy)
  - `AIBuyer` (id, name, spending_limits JSON, permitted_categories JSON)
  - `PurchaseRequest` (id, buyer_id, natural_language_request, parsed_constraints JSON, selected_products JSON, calculated_amount, status)
  - `Transaction` (id, purchase_request_id, amount, policy_decision, approval_status, razorpay_order_id, payment_status, created_at, updated_at)
  - `AuditEvent` (id, transaction_id, event_type, description, metadata JSON, timestamp)
  - `UpsellSuggestion` (id, transaction_id, suggested_product_id, reason, accepted, created_at)
- Seed database with:
  - 1 merchant: **TechKart**
  - 30–50 synthetic products (electronics + office equipment)
  - 1 AI buyer: **Office Procurement Agent**
  - Merchant policy config

### Deliverable
`GET /health` returns 200. DB seeded and queryable.

---

## Phase 2 — Merchant Catalog API

**Goal:** AI-readable product catalog with search.

### Tasks
- `GET /catalog/products` — list all products with filters (category, max_price, in_stock)
- `GET /catalog/products/{id}` — single product detail
- `POST /catalog/search` — structured search by constraints (category, max_price, attributes, quantity)
- `GET /catalog/inventory/{id}` — stock check
- `GET /merchant/policy` — return current merchant policy config
- `POST /catalog/upsell` — given a list of purchased product IDs, return up to 3 complementary product suggestions with reasons (rule-based: same category accessories, frequently bought together tags on seed data)

### Deliverable
Catalog fully queryable via API. Search returns ranked matches. Upsell endpoint returns relevant suggestions.

---

## Phase 3 — Deterministic Policy Engine

**Goal:** Zero-LLM rule enforcement for all financial decisions.

### Tasks
- Implement `PolicyEngine` class (pure Python, no LLM)
- Evaluate a proposed transaction against:
  - `max_transaction_amount` → DENY if exceeded
  - `daily_spending_limit` → DENY if daily total exceeded
  - `allowed_categories` → DENY if category not permitted
  - `max_quantity` → DENY if quantity exceeded
  - `human_approval_threshold` → REVIEW if amount exceeds threshold but below hard limit
  - All checks pass → APPROVE
- Return structured result:
  ```json
  {
    "decision": "APPROVE | REVIEW | DENY",
    "allowed": true | false,
    "reasons": [],
    "requires_human_approval": false
  }
  ```
- `POST /policy/evaluate` endpoint wrapping the engine
- Unit tests covering all decision branches

### Deliverable
Policy engine correctly classifies 100% of test cases. No LLM involved.

---

## Phase 4 — Razorpay Integration

**Goal:** Test-mode order creation and payment status tracking.

### Tasks
- Load `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` from `.env` only
- `POST /payments/create-order` — creates Razorpay test order (amount in paise)
  - Only callable after policy engine returns APPROVE
  - Validates amount server-side before calling Razorpay
- `GET /payments/status/{order_id}` — fetches order/payment status from Razorpay
- `POST /payments/webhook` — receives Razorpay payment webhook, updates transaction status
- Never expose secret key to frontend or logs

### Deliverable
Razorpay test order created end-to-end. Payment status tracked. Secrets never leave backend.

---

## Phase 5 — AI Agent (LangGraph)

**Goal:** Stateful agent that orchestrates the full purchase flow using tools.

### Tasks
- Define agent tools (each backed by Phase 2–4 APIs):
  - `search_products(constraints)` — safe, no approval needed
  - `get_product_details(product_id)` — safe
  - `check_inventory(product_id, quantity)` — safe
  - `get_merchant_policy()` — safe
  - `calculate_order_total(items)` — safe
  - `evaluate_transaction_policy(transaction)` — calls Phase 3 engine
  - `create_razorpay_order(transaction_id)` — gated: requires APPROVE status
  - `get_payment_status(order_id)` — safe
  - `request_human_approval(transaction_id)` — triggers REVIEW flow
  - `get_upsell_suggestions(transaction_id)` — safe, called only after payment succeeds; returns complementary product suggestions with reasons
- Implement LangGraph state machine:
  ```
  START → parse_intent → search_catalog → evaluate_products
       → calculate_total → check_policy
       → [DENY: stop] [REVIEW: human_gate] [APPROVE: create_order]
       → payment_status → upsell_suggestions → audit_log → END
  ```
- Upsell node runs only after a successful payment — it never blocks or delays the transaction
- Agent presents upsell as: `"Your order is complete. You may also want: [product] — [reason]."`
- Upsell suggestions are stored in `UpsellSuggestion` table and shown in the dashboard
- `POST /agent/purchase` — accepts natural language request, runs full agent flow, returns structured result including upsell suggestions if payment succeeded
- Agent writes AuditEvent records at every state transition

### Deliverable
Full agent flow works end-to-end for all three scenarios (APPROVE, REVIEW, DENY). Successful transactions surface upsell suggestions.

---

## Phase 6 — Human Approval Flow

**Goal:** Merchant can review and approve/reject REVIEW-status transactions.

### Tasks
- `GET /approvals/pending` — list all transactions awaiting human approval
- `POST /approvals/{transaction_id}/approve` — merchant approves → triggers Razorpay order creation
- `POST /approvals/{transaction_id}/reject` — merchant rejects → transaction marked REJECTED, audit logged
- Approval actions write AuditEvent records

### Deliverable
Human can approve or reject a pending transaction. Approved transactions proceed to payment. Rejected ones stop cleanly.

---

## Phase 7 — Audit Trail API

**Goal:** Full chronological audit trail per transaction, visible via API.

### Tasks
- `GET /audit/{transaction_id}` — returns all AuditEvents for a transaction in chronological order
- `GET /audit/recent` — last N audit events across all transactions
- Each event includes: event_type, description, metadata, timestamp
- Ensure all agent state transitions, policy decisions, approval actions, and payment events are recorded

### Deliverable
Any transaction's full decision history is retrievable and human-readable.

---

## Phase 8 — React Frontend

**Goal:** Two-view UI — AI Buyer interface + Merchant Dashboard.

### Tasks

**AI Buyer View**
- Chat-style input for natural language purchase requests
- Display: parsed intent, matched products, selected product, policy evaluation result, transaction status, payment result
- Show APPROVE / REVIEW / DENY outcome clearly
- After successful payment, show upsell suggestions as a non-intrusive card: "Customers also bought" with product name, price, and reason

**Merchant Dashboard**
- Merchant info + AI commerce status
- Product catalog table
- Current policy config
- Recent transactions (status, amount, decision)
- Pending approvals with Approve / Reject buttons
- Blocked transactions list
- Upsell performance panel: suggestions shown, suggestions accepted, estimated additional revenue
- Audit log viewer (per transaction)

**Transaction Detail Page**
- Buyer, products, amount, policy checks, decision, approval status, Razorpay order ID, payment status, agent reasoning summary, full audit trail

### Deliverable
Both views functional. Human approval flow completable from the dashboard.

---

## Phase 9 — Automated Test Suite

**Goal:** Deterministic coverage of all policy and agent scenarios.

### Tasks
- 50+ simulated purchase requests covering:
  - Valid low-value transactions (→ APPROVE)
  - Transactions above approval threshold (→ REVIEW)
  - Transactions above hard limit (→ DENY)
  - Disallowed categories (→ DENY)
  - Excessive quantities (→ DENY)
  - Insufficient inventory (→ DENY)
  - Ambiguous/invalid requests
  - Human-approved transactions
  - Human-rejected transactions
  - Successful payments
  - Failed payments
  - Upsell suggestions returned after successful payment
  - No upsell shown after DENY or REVIEW-rejected transactions
- Measure and assert:
  - Policy decision accuracy: 100%
  - Unauthorized transactions: 0
  - Policy bypasses: 0
  - Blocked transactions correctly identified: X/Y
  - Upsell shown only on completed transactions: 100%

### Deliverable
Test suite runs, all assertions pass, metrics printed.

---

## Phase 10 — Polish & Demo Prep

**Goal:** Reliable 5-minute demo covering all three acts.

### Tasks
- Seed a clean demo database state
- Verify Act 1 (discovery + auto-approve), Act 2 (autonomous payment + upsell suggestion), Act 3 (hard block + human review) all work end-to-end
- Add loading states and error messages to frontend
- Write `.env.example` with placeholder keys
- Write `README.md` with setup instructions
- Final security check: no secrets in frontend, no secrets in logs, no hardcoded credentials anywhere

### Deliverable
Demo-ready. Judges can run it locally with their own Razorpay test keys.

---

## File Structure (Target)

```
AI-Merchant-Gateway/
├── backend/
│   ├── main.py
│   ├── models/
│   ├── routes/
│   │   ├── catalog.py
│   │   ├── policy.py
│   │   ├── payments.py
│   │   ├── approvals.py
│   │   ├── upsell.py
│   │   └── audit.py
│   ├── services/
│   │   ├── policy_engine.py
│   │   ├── upsell_service.py
│   │   └── razorpay_service.py
│   ├── agent/
│   │   ├── graph.py
│   │   └── tools.py
│   ├── db/
│   │   ├── database.py
│   │   └── seed.py
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── BuyerView.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── TransactionDetail.jsx
│   │   └── components/
│   └── vite.config.js
├── tests/
│   └── test_scenarios.py
├── problem_statement.md
├── plan_of_action.md
└── README.md
```

---

## When You Need the Razorpay Keys

Keys are needed at **Phase 4**. Before that, all work is local (DB, catalog, policy engine, agent tools).

When ready, provide:
- `RAZORPAY_KEY_ID=rzp_test_...`
- `RAZORPAY_KEY_SECRET=...`

These go into `backend/.env` only. Never committed, never logged, never sent to frontend.
