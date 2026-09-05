import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMerchant, getAllTransactions, getPending } from '../api'

function Badge({ value }) {
  const v = (value || '').toLowerCase()
  if (v === 'approve' || v === 'approved') return <span className="badge badge-approve">{value}</span>
  if (v === 'review' || v === 'pending_human') return <span className="badge badge-review">{value}</span>
  if (v === 'deny' || v === 'denied' || v === 'rejected') return <span className="badge badge-deny">{value}</span>
  if (v === 'paid') return <span className="badge badge-paid">{value}</span>
  if (v === 'created') return <span className="badge badge-created">{value}</span>
  return <span className="badge badge-gray">{value || '—'}</span>
}

export default function Dashboard() {
  const [merchant, setMerchant] = useState(null)
  const [txs, setTxs] = useState([])
  const [pending, setPending] = useState([])
  const navigate = useNavigate()

  useEffect(() => {
    getMerchant().then(r => setMerchant(r.data))
    getAllTransactions().then(r => setTxs(r.data))
    getPending().then(r => setPending(r.data))
  }, [])

  const approved = txs.filter(t => t.policy_decision === 'APPROVE').length
  const denied   = txs.filter(t => t.policy_decision === 'DENY').length
  const review   = txs.filter(t => t.policy_decision === 'REVIEW').length
  const totalRev = txs.filter(t => t.payment_status === 'paid').reduce((s, t) => s + t.amount, 0)
  const policies = merchant?.policies || {}

  return (
    <div className="page">
      <div className="page-title">📊 Merchant Dashboard</div>
      <div className="page-sub">{merchant?.name || 'TechKart'} — AI Commerce Overview</div>

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <div className="stat"><div className="stat-value">{txs.length}</div><div className="stat-label">Total Transactions</div></div>
        <div className="stat"><div className="stat-value" style={{ color: 'var(--approve)' }}>{approved}</div><div className="stat-label">Auto Approved</div></div>
        <div className="stat"><div className="stat-value" style={{ color: 'var(--review)' }}>{pending.length}</div><div className="stat-label">Pending Approval</div></div>
        <div className="stat"><div className="stat-value" style={{ color: 'var(--deny)' }}>{denied}</div><div className="stat-label">Blocked</div></div>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Revenue Processed</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--accent2)' }}>
            Rs.{totalRev.toLocaleString('en-IN')}
          </div>
          <div className="text-muted text-sm mt-8">From {txs.filter(t => t.payment_status === 'paid').length} paid transactions</div>
        </div>
        <div className="card">
          <div className="card-title">Merchant Policies</div>
          {Object.keys(policies).length === 0 ? <div className="text-muted">Loading...</div> : (
            <div>
              <div className="policy-item"><span className="policy-key">Max Transaction</span><span className="policy-val">Rs.{policies.max_transaction_amount?.toLocaleString('en-IN')}</span></div>
              <div className="policy-item"><span className="policy-key">Daily Limit</span><span className="policy-val">Rs.{policies.daily_spending_limit?.toLocaleString('en-IN')}</span></div>
              <div className="policy-item"><span className="policy-key">Auto-Approval Threshold</span><span className="policy-val">Rs.{policies.human_approval_threshold?.toLocaleString('en-IN')}</span></div>
              <div className="policy-item"><span className="policy-key">Max Quantity</span><span className="policy-val">{policies.max_quantity} units</span></div>
              <div className="policy-item"><span className="policy-key">Allowed Categories</span><span className="policy-val">{policies.allowed_categories?.join(', ')}</span></div>
            </div>
          )}
        </div>
      </div>

      {pending.length > 0 && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--review)' }}>
          <div className="card-title" style={{ color: 'var(--review)' }}>⏳ Pending Approvals ({pending.length})</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Request</th><th>Amount</th><th>Reason</th><th></th></tr></thead>
              <tbody>
                {pending.map(t => (
                  <tr key={t.transaction_id}>
                    <td style={{ maxWidth: 260 }}>{t.request}</td>
                    <td style={{ fontWeight: 700 }}>Rs.{t.amount?.toLocaleString('en-IN')}</td>
                    <td className="text-muted text-sm">{t.policy_reasons?.[0]}</td>
                    <td><button className="btn btn-ghost" style={{ fontSize: 11 }} onClick={() => navigate('/approvals')}>Review</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-title">Recent Transactions</div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Request</th><th>Amount</th><th>Decision</th><th>Payment</th><th>Time</th><th></th></tr></thead>
            <tbody>
              {txs.slice(0, 10).map(t => (
                <tr key={t.transaction_id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/transactions/${t.transaction_id}`)}>
                  <td style={{ maxWidth: 240 }}>{t.request?.slice(0, 60)}{t.request?.length > 60 ? '…' : ''}</td>
                  <td style={{ fontWeight: 600 }}>Rs.{t.amount?.toLocaleString('en-IN')}</td>
                  <td><Badge value={t.policy_decision} /></td>
                  <td><Badge value={t.payment_status} /></td>
                  <td className="text-muted text-sm">{t.created_at ? new Date(t.created_at).toLocaleTimeString() : '—'}</td>
                  <td className="text-muted text-sm">→</td>
                </tr>
              ))}
              {txs.length === 0 && <tr><td colSpan={6} className="text-muted" style={{ textAlign: 'center', padding: 24 }}>No transactions yet. Try the AI Buyer.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
