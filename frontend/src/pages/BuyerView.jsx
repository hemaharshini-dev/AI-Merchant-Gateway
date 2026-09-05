import { useState, useRef, useEffect } from 'react'
import { runPurchase } from '../api'

const EXAMPLES = [
  'I need one wireless mouse under Rs.1000',
  'I need two webcams for our office video calls',
  'Buy five 27 inch monitors for our design team',
  'Get me a mechanical wireless keyboard under Rs.3000',
]

const INITIAL_MESSAGES = [
  { type: 'agent', text: "Hello! I'm your AI purchasing agent for TechKart.\n\nTell me what you need and I'll search the catalog, check policies, and complete the purchase for you." }
]

function loadMessages() {
  try {
    const saved = localStorage.getItem('buyer_chat')
    return saved ? JSON.parse(saved) : INITIAL_MESSAGES
  } catch { return INITIAL_MESSAGES }
}

function saveMessages(msgs) {
  try { localStorage.setItem('buyer_chat', JSON.stringify(msgs)) } catch {}
}

function DecisionBanner({ decision, amount }) {
  if (!decision || decision === 'pending') return null
  const map = {
    APPROVE: { cls: 'approve', icon: '✅', label: 'Auto Approved' },
    REVIEW:  { cls: 'review',  icon: '⏳', label: 'Human Approval Required' },
    DENY:    { cls: 'deny',    icon: '🚫', label: 'Transaction Blocked' },
  }
  const d = map[decision]
  if (!d) return null
  return (
    <div className={`decision-banner ${d.cls}`}>
      {d.icon} {d.label} {amount > 0 ? `— Rs.${amount.toLocaleString('en-IN')}` : ''}
    </div>
  )
}

function UpsellCard({ suggestions }) {
  if (!suggestions?.length) return null
  return (
    <div className="upsell-card mt-16">
      <div className="upsell-title">⚡ You may also like</div>
      {suggestions.map((s, i) => (
        <div className="upsell-item" key={i}>
          <div>
            <div style={{ fontWeight: 600 }}>{s.name}</div>
            <div className="text-muted text-sm">{s.reason}</div>
          </div>
          <div style={{ fontWeight: 700, color: 'var(--accent2)' }}>Rs.{s.price?.toLocaleString('en-IN')}</div>
        </div>
      ))}
    </div>
  )
}

function AgentMessage({ msg }) {
  return (
    <div className="msg msg-agent">
      <pre>{msg.text}</pre>
      <DecisionBanner decision={msg.decision} amount={msg.amount} />
      {msg.razorpay_order_id && (
        <div className="mt-8 text-sm" style={{ color: 'var(--accent2)' }}>
          🧾 Razorpay Order: <strong>{msg.razorpay_order_id}</strong>
        </div>
      )}
      <UpsellCard suggestions={msg.upsell} />
    </div>
  )
}

export default function BuyerView() {
  const [messages, setMessages] = useState(loadMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  function updateMessages(updater) {
    setMessages(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      saveMessages(next)
      return next
    })
  }

  async function send(text) {
    const req = text || input.trim()
    if (!req || loading) return
    setInput('')
    updateMessages(prev => [...prev, { type: 'user', text: req }])
    setLoading(true)
    try {
      const { data } = await runPurchase({ request: req })
      const upsell = data.upsell_suggestions?.suggestions || []
      updateMessages(prev => [...prev, {
        type: 'agent',
        text: data.agent_summary || 'Purchase flow completed.',
        decision: data.policy_decision,
        amount: data.amount,
        razorpay_order_id: data.razorpay_order_id,
        upsell,
      }])
    } catch (e) {
      updateMessages(prev => [...prev, { type: 'agent', text: `Error: ${e.response?.data?.detail || e.message}` }])
    }
    setLoading(false)
  }

  function clearChat() {
    localStorage.removeItem('buyer_chat')
    setMessages(INITIAL_MESSAGES)
  }

  return (
    <div className="page" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div className="flex justify-between items-center" style={{ marginBottom: 4 }}>
        <div className="page-title">AI Buyer</div>
        <button className="btn btn-ghost" style={{ fontSize: 11 }} onClick={clearChat}>Clear Chat</button>
      </div>
      <div className="page-sub">Enter a natural language purchase request. The agent will search, evaluate policy, and execute payment.</div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        {EXAMPLES.map((e, i) => (
          <button key={i} className="btn btn-ghost" style={{ fontSize: 11 }} onClick={() => send(e)}>{e}</button>
        ))}
      </div>

      <div className="chat-messages" style={{ flex: 1 }}>
        {messages.map((m, i) =>
          m.type === 'user'
            ? <div key={i} className="msg msg-user">{m.text}</div>
            : <AgentMessage key={i} msg={m} />
        )}
        {loading && (
          <div className="msg msg-agent" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div className="spinner" /> Agent is processing your request...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row" style={{ marginTop: 12 }}>
        <input
          className="input"
          placeholder="e.g. I need three wireless keyboards under Rs.8000..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          disabled={loading}
        />
        <button className="btn btn-primary" onClick={() => send()} disabled={loading || !input.trim()}>
          {loading ? <span className="spinner" /> : 'Send'}
        </button>
      </div>
    </div>
  )
}
