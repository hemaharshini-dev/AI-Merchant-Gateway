import { useEffect, useState } from 'react'
import { getPending, approveTransaction, rejectTransaction } from '../api'
import { useNavigate } from 'react-router-dom'

export default function Approvals() {
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState({})
  const [done, setDone] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    getPending().then(r => setPending(r.data))
    const interval = setInterval(() => {
      getPending().then(r => setPending(r.data))
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  async function act(id, action) {
    setLoading(l => ({ ...l, [id]: action }))
    try {
      const fn = action === 'approve' ? approveTransaction : rejectTransaction
      const { data } = await fn(id)
      setDone(d => ({ ...d, [id]: { action, data } }))
    } catch (e) {
      alert(e.response?.data?.detail || e.message)
    }
    setLoading(l => ({ ...l, [id]: null }))
  }

  return (
    <div className="page">
      <div className="page-title">Human Approvals</div>
      <div className="page-sub">Transactions that exceed the auto-approval threshold and require merchant review.</div>

      {pending.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: 48, color: 'var(--muted)' }}>
          No pending approvals. All transactions are within auto-approval limits.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {pending.map(t => {
          const result = done[t.transaction_id]
          return (
            <div key={t.transaction_id} className="card" style={{ borderColor: result ? (result.action === 'approve' ? 'var(--approve)' : 'var(--deny)') : 'var(--review)' }}>
              <div className="flex justify-between items-center" style={{ marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15 }}>{t.request}</div>
                  <div className="text-muted text-sm" style={{ marginTop: 4 }}>
                    Transaction ID: {t.transaction_id}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--review)' }}>
                    Rs.{t.amount?.toLocaleString('en-IN')}
                  </div>
                  <div className="text-muted text-sm">{t.created_at ? new Date(t.created_at).toLocaleString() : ''}</div>
                </div>
              </div>

              <div className="card" style={{ background: 'var(--surface2)', marginBottom: 14 }}>
                <div className="card-title">Policy Reason</div>
                <div style={{ color: 'var(--review)', fontSize: 13 }}>{t.policy_reasons?.[0]}</div>
              </div>

              {t.selected_products?.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div className="card-title">Selected Products</div>
                  {t.selected_products.map((p, i) => (
                    <div key={i} className="policy-item">
                      <span>{p.name} × {p.quantity}</span>
                      <span style={{ fontWeight: 600 }}>Rs.{p.total?.toLocaleString('en-IN')}</span>
                    </div>
                  ))}
                </div>
              )}

              {result ? (
                <div className={`decision-banner ${result.action === 'approve' ? 'approve' : 'deny'}`}>
                  {result.action === 'approve'
                    ? `✅ Approved — Razorpay order created: ${result.data.razorpay_order_id}`
                    : '🚫 Rejected — No payment will be processed.'}
                </div>
              ) : (
                <div className="flex gap-8">
                  <button
                    className="btn btn-success"
                    disabled={!!loading[t.transaction_id]}
                    onClick={() => act(t.transaction_id, 'approve')}
                  >
                    {loading[t.transaction_id] === 'approve' ? <span className="spinner" /> : '✅ Approve'}
                  </button>
                  <button
                    className="btn btn-danger"
                    disabled={!!loading[t.transaction_id]}
                    onClick={() => act(t.transaction_id, 'reject')}
                  >
                    {loading[t.transaction_id] === 'reject' ? <span className="spinner" /> : '🚫 Reject'}
                  </button>
                  <button className="btn btn-ghost" onClick={() => navigate(`/transactions/${t.transaction_id}`)}>
                    View Audit Trail
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
