# Troubleshooting Log — AI Merchant Gateway

A running record of every issue encountered during the build and how it was resolved.

---

## Issue 1 — `pip` not found on PATH

**Phase:** 1 — Project Scaffold

**Error:**
```
Command '.venvScriptspip' not found on PATH.
```

**Cause:**
Windows cmd.exe does not expand backslash paths in the same way as Unix shells when called directly without `cmd /c`.

**Fix:**
Prefix all venv commands with `cmd /c` to ensure proper path resolution:
```bash
cmd /c ".venv\Scripts\pip.exe install -r requirements.txt"
```

---

## Issue 2 — SQLAlchemy reserved column name `metadata`

**Phase:** 1 — Database Models

**Error:**
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved
when using the Declarative API.
```

**Cause:**
SQLAlchemy's `DeclarativeBase` uses `metadata` internally as a class-level attribute. Naming a column `metadata` conflicts with it.

**Fix:**
Renamed the column from `metadata` to `event_metadata` in the `AuditEvent` model:
```python
event_metadata = Column(JSON, default=dict)
```

---

## Issue 3 — `razorpay` package uses `pkg_resources` (removed in Python 3.13)

**Phase:** 4 — Razorpay Integration

**Error:**
```
ModuleNotFoundError: No module named 'pkg_resources'
```

**Cause:**
`razorpay==1.4.1` imports `pkg_resources` from `setuptools`, which is no longer bundled with Python 3.13.

**Fix — Step 1:** Install `setuptools` explicitly:
```bash
pip install setuptools
```
This did not resolve it because the razorpay package itself still used the old import pattern.

**Fix — Step 2:** Upgrade razorpay to v2 which removed the dependency:
```bash
pip install --upgrade razorpay
```
Installed `razorpay==2.0.1`. Updated `requirements.txt` accordingly.

---

## Issue 4 — Windows terminal `UnicodeEncodeError` for `₹` symbol

**Phase:** 3 — Policy Engine, Test Scripts

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9'
```

**Cause:**
Windows terminal uses `cp1252` encoding by default which does not support the `₹` (Rupee) Unicode character.

**Fix:**
Replaced all `₹` symbols in policy engine reason strings with ASCII `Rs.`:
```python
# Before
f"Transaction amount ₹{amount:,.0f}"
# After
f"Transaction amount Rs.{amount:,.0f}"
```
For test output strings, used `.encode('ascii', errors='replace').decode()`.

---

## Issue 5 — Policy engine daily limit test failing

**Phase:** 3 — Policy Engine Tests

**Error:**
```
AssertionError: FAILED: Daily limit exceeded — got=APPROVE expected=DENY
```

**Cause:**
The mock DB object's `.filter().filter().all()` chain was not set up correctly. The policy engine chains two `.filter()` calls on the query, but the mock only handled one level of chaining.

**Fix:**
Rewrote the mock to make `.filter()` return itself, so any number of chained calls resolve to the same mock object:
```python
mock_inner_filter.filter = MagicMock(return_value=mock_inner_filter)
```

---

## Issue 6 — Groq model `llama-3.3-70b-versatile` not found

**Phase:** 5 — AI Agent

**Error:**
```
groq.NotFoundError: The model `llama-3.3-70b-versatile` does not exist
or you do not have access to it.
```

**Cause:**
The free Groq tier on this account does not have access to `llama-3.3-70b-versatile`. Available models differ by account tier and region.

**Fix:**
Listed available models programmatically:
```python
from groq import Groq
client = Groq(api_key=...)
for m in client.models.list().data:
    print(m.id)
```
Switched to `openai/gpt-oss-120b` which was available and supports tool calling.

---

## Issue 7 — LangGraph `GraphRecursionError` at limit 25

**Phase:** 5 — AI Agent

**Error:**
```
langgraph.errors.GraphRecursionError: Recursion limit of 25 reached
without hitting a stop condition.
```

**Cause:**
The agent workflow requires ~10 tool calls per purchase request (search → details → inventory → policy → record → create order → status → upsell). The default LangGraph recursion limit of 25 was too low for the full workflow.

**Fix:**
Increased the recursion limit when invoking the graph:
```python
graph.invoke(initial_state, config={"recursion_limit": 50})
```

---

## Issue 8 — Agent not writing back to DB (transaction fields stayed `pending`)

**Phase:** 5 — AI Agent

**Symptom:**
Agent ran successfully and created a Razorpay order, but `policy_decision`, `approval_status`, and `amount` fields on the `Transaction` record remained at their initial `pending`/`0.0` values.

**Cause:**
The agent tools each opened their own DB sessions and wrote to their own tables, but no tool was explicitly updating the `Transaction` record's core fields (`amount`, `policy_decision`, `approval_status`). The agent was reasoning correctly but not persisting the decisions.

**Fix:**
Added three new explicit DB write-back tools:
- `update_transaction(transaction_id, amount, category, quantity)` — sets amount before policy check
- `record_policy_decision(transaction_id, decision, reasons)` — writes APPROVE/REVIEW/DENY to DB
- `record_selected_products(purchase_request_id, ...)` — saves selected product to purchase request

Updated the system prompt to instruct the agent to call these tools at the correct steps.

---

## Issue 9 — Stale uvicorn processes blocking new server

**Phase:** 5–7 — Server Startup

**Symptom:**
After adding all routers to `main.py`, `http://127.0.0.1:8000/docs` still showed only the `/health` endpoint even after restarting uvicorn.

**Diagnosis:**
```bash
netstat -ano | findstr :8000
```
Revealed **two processes** (PIDs 2600 and 4300) both listening on port 8000 simultaneously — old stale uvicorn processes from earlier sessions were still running and intercepting requests before the new server could respond.

**Fix:**
Killed all Python processes:
```bash
taskkill /IM python.exe /F
```
Then restarted uvicorn fresh. Port 8000 was confirmed free before restarting.

**Prevention:**
Always press `Ctrl+C` in the terminal where uvicorn is running before closing the terminal window. Closing the window without `Ctrl+C` leaves orphan processes.

---

## Issue 10 — `cmd /c` single-line Python `-c` commands failing with quotes

**Phase:** Multiple

**Error:**
```
Got EOF while in a quoted string
```
or
```
SyntaxError: unterminated string literal
```

**Cause:**
Windows `cmd /c` does not handle nested single and double quotes in inline Python `-c` commands reliably, especially when the Python code itself contains quotes.

**Fix:**
Wrote all multi-line verification and test logic to temporary `.py` files and ran those instead of inline `-c` commands:
```bash
# Instead of this (breaks):
cmd /c ".venv\Scripts\python.exe -c "import main; print('OK')""

# Do this (works):
# Write to check.py, then:
cmd /c ".venv\Scripts\python.exe check.py"
```

---

## Issue 11 — Frontend Network Error (CORS mismatch)

**Phase:** 8 — React Frontend

**Symptom:**
Clicking any query in the AI Buyer interface showed a `Network Error`. All backend endpoints were working correctly when tested directly.

**Cause:**
Two separate mismatches:

1. The CORS middleware in `main.py` only allowed `http://localhost:5173`, but the browser was making requests to `http://127.0.0.1:8000`. Browsers treat `localhost` and `127.0.0.1` as **different origins**, so the preflight OPTIONS request was being rejected.

2. The Axios base URL in `api.js` was set to `http://127.0.0.1:8000` while the frontend was served from `http://localhost:5173`, creating a cross-origin mismatch.

**Fix:**
Added both origins to the CORS allow list in `backend/main.py`:
```python
allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
```

Changed the Axios base URL in `frontend/src/api.js` to use `localhost` consistently:
```js
const api = axios.create({ baseURL: 'http://localhost:8000' })
```

Restarted the backend after the CORS change (middleware changes require a full restart, not just a hot-reload).

**Prevention:**
Always use `localhost` consistently across both frontend API calls and backend CORS config. Never mix `localhost` and `127.0.0.1` in the same project.
