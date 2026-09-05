# Problem Statement — AI Merchant Gateway

## Track Alignment

**Razorpay Track 01 — AI Growth & Agentic Commerce**
> "Build an agent that grows revenue for a merchant on Razorpay test-mode APIs, or that makes a merchant transactable by an AI buyer end to end."
> Bar: Every money action explainable, bounded and gated. Show the audit trail and one failure handled gracefully.

---

## The Problem

E-commerce today is built entirely for human buyers. A human visits a site, browses, reads, decides, and pays.

AI agents are now becoming buyers. An autonomous agent may receive a high-level objective like:

> "Buy two wireless keyboards for my team, under ₹5,000 total, preferably mechanical, deliverable to Hyderabad."

The agent must independently discover products, compare them, understand policies, calculate totals, and complete payment — without a human in the loop for every step.

This creates a critical gap:

**Merchants have no infrastructure to safely transact with autonomous AI buyers.**

Giving an AI agent unrestricted access to a payment system is dangerous. Merchants need explicit control over:

- Maximum transaction amount
- Daily AI-agent spending limits
- Permitted product categories
- Maximum quantities per transaction
- Discount limits
- Human approval thresholds
- Full auditability of every financial action

Without this control layer, agentic commerce cannot be trusted or deployed at scale.

---

## Our Solution

**AI Merchant Gateway** — a merchant-side agentic commerce infrastructure layer that makes any merchant AI-ready.

The gateway exposes the merchant's catalog, policies, and payment infrastructure in a structured, AI-consumable form. An AI buyer interacts with it using natural language. The gateway's agent then:

```
AI Buyer Request
      ↓
Intent Understanding
      ↓
Merchant Catalog Search
      ↓
Product Matching & Reasoning
      ↓
Constraint Validation
      ↓
Deterministic Policy Evaluation
      ↓
DENY / REVIEW / APPROVE
      ↓
Human Approval Gate (if REVIEW)
      ↓
Razorpay Test Mode Order Creation
      ↓
Payment Execution
      ↓
Audit Trail
```

**Core principle:** The AI reasons and recommends. A deterministic policy engine enforces. The AI can never bypass merchant-defined financial rules.

---

## What Makes This an AI Project

The LLM handles:
- Natural language intent parsing → structured purchase constraints
- Catalog reasoning and product comparison
- Explaining why a product was selected
- Deciding which tool to call next (agent orchestration)

The deterministic policy engine handles:
- Hard transaction limits
- Daily spend tracking
- Category and quantity enforcement
- Approval routing

This separation is the architectural core of the project.

---

## Key Scenarios

### Scenario 1 — Autonomous Approval
> "I need three wireless keyboards under ₹8,000."

Agent finds 3 × ₹2,499 = ₹7,497. Policy checks pass. Razorpay order created automatically.

### Scenario 2 — Human Review Required
> "Buy a laptop for ₹9,000."

Amount exceeds the auto-approval threshold (₹7,500) but is below the hard limit (₹10,000). Transaction is held for human approval.

### Scenario 3 — Hard Block (mandatory demo)
> "Buy five monitors."

Total = ₹44,995. Hard limit = ₹10,000. Transaction is **denied immediately**. No payment is created. Audit trail records the violation.

---

## Five Core Components

| Component | Role |
|---|---|
| AI Buyer Interface | Natural language → structured purchase request |
| AI-Readable Merchant Catalog | Structured product data searchable by the agent |
| Merchant Policy Engine | Deterministic rule enforcement (APPROVE / REVIEW / DENY) |
| Razorpay Payment Layer | Test-mode order creation and payment status tracking |
| Audit & Explainability Layer | Full chronological record of every decision |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| Agent | LangGraph (stateful tool orchestration) |
| LLM | Structured tool-calling LLM |
| Database | SQLite (MVP) → PostgreSQL-ready |
| Payments | Razorpay Test Mode APIs |
| Config | Environment variables only — no hardcoded secrets |

---

## MVP Scope

- One merchant: **TechKart**
- 30–50 synthetic products (electronics + office equipment)
- One AI buyer: **Office Procurement Agent**
- Currency: INR only
- Payment provider: Razorpay Test Mode only
- Policies: max transaction amount, daily limit, allowed categories, max quantity, human approval threshold

---

## Track 01 Compliance Checklist

| Requirement | How We Meet It |
|---|---|
| Agent that makes merchant transactable by AI buyer | ✅ Full end-to-end AI buyer → Razorpay flow |
| Agent that grows merchant revenue | ✅ Post-payment upsell suggestions via `get_upsell_suggestions` tool |
| Every money action explainable | ✅ Audit trail records every decision with reasons |
| Every money action bounded | ✅ Deterministic policy engine enforces hard limits |
| Every money action gated | ✅ Human approval gate for REVIEW decisions |
| Audit trail shown | ✅ Visible in merchant dashboard per transaction |
| One failure handled gracefully | ✅ DENY scenario with clear explanation, no payment created |
| Razorpay test-mode APIs used | ✅ All payments via Razorpay Test Mode |

---

## The Core Story for Judges

> "AI agents are becoming buyers. We built the merchant-side control layer that lets them buy safely — with every financial action bounded, explainable, and gated — and that actively grows merchant revenue through intelligent post-purchase upsell suggestions."
