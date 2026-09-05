import json
from typing import TypedDict, Annotated
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from config import settings
from db.database import SessionLocal
from models.models import PurchaseRequest, Transaction, AuditEvent
from agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are an AI purchasing agent for TechKart, an electronics and office equipment merchant.

Your job is to help an AI buyer purchase products by following this EXACT workflow in order:
1. Search the product catalog using search_products
2. Get product details using get_product_details for the best match
3. Check inventory using check_inventory
4. Calculate total using calculate_order_total
5. Record the selected product using record_selected_products (use the purchase_request_id from SYSTEM tag)
6. Update the transaction amount using update_transaction (use the transaction_id from SYSTEM tag)
7. Get merchant policy using get_merchant_policy
8. Evaluate the transaction using evaluate_transaction_policy
9. Record the policy decision using record_policy_decision (use the transaction_id from SYSTEM tag)
10. Based on the decision:
    - APPROVE: call create_razorpay_order with the transaction_id, then get_payment_status, then get_upsell_suggestions
    - REVIEW: call request_human_approval with the transaction_id, then stop
    - DENY: stop and explain clearly — do NOT create any order

CRITICAL RULES:
- ALWAYS extract transaction_id and purchase_request_id from the [SYSTEM: ...] tag in the user message
- ALWAYS call update_transaction before evaluate_transaction_policy
- ALWAYS call record_policy_decision after evaluate_transaction_policy
- NEVER call create_razorpay_order unless the decision is APPROVE
- NEVER skip the policy evaluation step
- NEVER call get_upsell_suggestions unless payment is confirmed paid
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    transaction_id: str
    purchase_request_id: str
    policy_decision: str
    final_summary: str


def log_event(db, transaction_id: str, event_type: str, description: str, metadata: dict = None):
    if not transaction_id:
        return
    event = AuditEvent(
        transaction_id=transaction_id,
        event_type=event_type,
        description=description,
        event_metadata=metadata or {},
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()


def build_graph():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=settings.GROQ_API_KEY,
        temperature=0
    ).bind_tools(ALL_TOOLS)

    tool_node = ToolNode(ALL_TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {**state, "messages": messages + [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_purchase_agent(natural_language_request: str, buyer_id: str = "buyer_office_agent") -> dict:
    db = SessionLocal()
    try:
        # Create PurchaseRequest record
        pr = PurchaseRequest(
            buyer_id=buyer_id,
            natural_language_request=natural_language_request,
            status="processing"
        )
        db.add(pr)
        db.flush()

        # Create Transaction record (amount/decision filled in by agent)
        tx = Transaction(
            purchase_request_id=pr.id,
            amount=0.0,
            policy_decision="pending",
            approval_status="pending"
        )
        db.add(tx)
        db.commit()

        log_event(db, tx.id, "PURCHASE_REQUEST_RECEIVED",
                  f"AI buyer submitted request: {natural_language_request}",
                  {"buyer_id": buyer_id, "purchase_request_id": pr.id})

        # Inject transaction_id into the request so the agent can use it
        augmented_request = (
            f"{natural_language_request}\n\n"
            f"[SYSTEM: transaction_id={tx.id}, purchase_request_id={pr.id}]"
        )

        graph = get_graph()
        initial_state: AgentState = {
            "messages": [HumanMessage(content=augmented_request)],
            "transaction_id": tx.id,
            "purchase_request_id": pr.id,
            "policy_decision": "pending",
            "final_summary": ""
        }

        final_state = graph.invoke(initial_state, config={"recursion_limit": 50})

        # Extract final assistant message
        final_message = ""
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                final_message = msg.content
                break

        # Refresh transaction from DB to get latest state
        db.expire_all()
        tx = db.query(Transaction).filter(Transaction.id == tx.id).first()
        pr = db.query(PurchaseRequest).filter(PurchaseRequest.id == pr.id).first()

        # Update purchase request status
        pr.status = "completed"
        db.commit()

        log_event(db, tx.id, "AGENT_COMPLETED",
                  "Agent workflow completed.",
                  {"policy_decision": tx.policy_decision, "payment_status": tx.payment_status})

        return {
            "transaction_id": tx.id,
            "purchase_request_id": pr.id,
            "policy_decision": tx.policy_decision,
            "approval_status": tx.approval_status,
            "payment_status": tx.payment_status,
            "razorpay_order_id": tx.razorpay_order_id,
            "amount": tx.amount,
            "agent_summary": final_message
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
