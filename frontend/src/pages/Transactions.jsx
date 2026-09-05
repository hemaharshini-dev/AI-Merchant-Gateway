import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAllTransactions } from '../api'

function Badge({ value }) {
  const v = (value || '').toLowerCase()
  if (v === 'approve') return <span className="badge badge-approve">{value}</span>
  if (v === 'review')  return <span className="badge badge-review">{value}</span>
  if (v === 'deny')    return <span className="badge badge-deny">{value}</span>
  if (v === 'paid')    return <span className="badge badge-paid">{value}</span>
  if (v === 'created') return <span className="badge badge-created">{value}</span>
  if (v === 'rejected')return <span className="badge badge-rejected">{value}</span>
  return <span className="badge badge-gray">{value || 'pending'}</span>
}

export default function Transactions() {
  const [txs, setTxs] = useState([])
  const navigate = useNavigate()

  useEffect(() => { getAllTransactions().then(r => setTxs(r.data)) }, [])

  return (
    <div className="page">
      <div className="page-title">📋 All Transactions</div>
      <div className="page-sub">Every AI purchase request and its outcome. Click a row to see the full audit trail.</div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Request</th>
                <th>Amount</th>
                <th>Decision</th>
                <th>Approval</th>
                <th>Payment</th>
                <th>Razorpay Order</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {txs.map(t => (
                <tr key={t.transaction_id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/transactions/${t.transaction_id}`)}>
                  <td style={{ maxWidth: 280 }}>{t.request?.slice(0, 70)}{t.request?.length > 70 ? '…' : ''}</td>
                  <td style={{ fontWeight: 600 }}>Rs.{t.amount?.toLocaleString('en-IN')}</td>
                  <td><Badge value={t.policy_decision} /></td>
                  <td><Badge value={t.approval_status} /></td>
                  <td><Badge value={t.payment_status} /></td>
                  <td className="text-muted text-sm">{t.razorpay_order_id || '—'}</td>
                  <td className="text-muted text-sm">{t.created_at ? new Date(t.created_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
              {txs.length === 0 && (
                <tr><td colSpan={7} className="text-muted" style={{ textAlign: 'center', padding: 32 }}>No transactions yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
