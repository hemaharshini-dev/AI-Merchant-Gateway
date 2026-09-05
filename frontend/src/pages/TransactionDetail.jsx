import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAuditTrail } from '../api'

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

function eventColor(type) {
  if (type?.includes('DENY') || type?.includes('FAIL') || type?.includes('REJECT')) return 'var(--deny)'
  if (type?.includes('APPROVE') || type?.includes('PAID') || type?.includes('VERIFIED') || type?.includes('CAPTURED')) return 'var(--approve)'
  if (type?.includes('REVIEW') || type?.includes('HUMAN')) return 'var(--review)'
  return 'var(--accent)'
}

export default function TransactionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)

  useEffect(() => { getAuditTrail(id).then(r => setData(r.data)) }, [id])

  if (!data) return <div className="page"><div className="spinner" /> Loading...</div>

  return (
    <div className="page">
      <button className="btn btn-ghost" style={{ marginBottom: 20, fontSize: 12 }} onClick={() => navigate(-1)}>← Back</button>

      <div className="page-title">Transaction Detail</div>
      <div className="page-sub" style={{ fontFamily: 'monospace', fontSize: 12 }}>{id}</div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Purchase Request</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{data.request}</div>
          {data.selected_products?.length > 0 && (
            <div>
              <div className="card-title" style={{ marginTop: 12 }}>Selected Products</div>
              {data.selected_products.map((p, i) => (
                <div key={i} className="policy-item">
                  <span>{p.name} × {p.quantity}</span>
                  <span style={{ fontWeight: 600 }}>Rs.{p.total?.toLocaleString('en-IN')}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">Transaction Summary</div>
          <div className="policy-item">
            <span className="policy-key">Amount</span>
            <span className="policy-val" style={{ fontSize: 18 }}>Rs.{data.amount?.toLocaleString('en-IN')}</span>
          </div>
          <div className="policy-item">
            <span className="policy-key">Policy Decision</span>
            <Badge value={data.policy_decision} />
          </div>
          <div className="policy-item">
            <span className="policy-key">Approval Status</span>
            <Badge value={data.approval_status} />
          </div>
          <div className="policy-item">
            <span className="policy-key">Payment Status</span>
            <Badge value={data.payment_status} />
          </div>
          {data.razorpay_order_id && (
            <div className="policy-item">
              <span className="policy-key">Razorpay Order</span>
              <span className="policy-val" style={{ fontSize: 11, fontFamily: 'monospace' }}>{data.razorpay_order_id}</span>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Audit Trail</div>
        {data.audit_trail?.length === 0 && <div className="text-muted">No audit events recorded.</div>}
        <div className="timeline">
          {data.audit_trail?.map((e, i) => (
            <div key={i} className="timeline-item" style={{ '--dot-color': eventColor(e.event_type) }}>
              <div className="timeline-time">{e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '—'}</div>
              <div className="timeline-content">
                <div className="timeline-type" style={{ color: eventColor(e.event_type) }}>{e.event_type}</div>
                <div className="timeline-desc">{e.description}</div>
                {e.metadata && Object.keys(e.metadata).length > 0 && (
                  <div className="text-muted text-sm mt-8" style={{ fontFamily: 'monospace' }}>
                    {JSON.stringify(e.metadata)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
