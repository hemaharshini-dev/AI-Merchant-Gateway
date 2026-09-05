import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import './index.css'
import BuyerView from './pages/BuyerView'
import Dashboard from './pages/Dashboard'
import Approvals from './pages/Approvals'
import Transactions from './pages/Transactions'
import TransactionDetail from './pages/TransactionDetail'
import { getPending } from './api'

function Sidebar() {
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    function fetchPending() {
      getPending().then(r => setPendingCount(r.data.length)).catch(() => {})
    }
    fetchPending()
    const interval = setInterval(fetchPending, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="sidebar">
      <div className="sidebar-logo">AI<span> Merchant</span></div>
      <NavLink to="/" end className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')}>
        🤖 AI Buyer
      </NavLink>
      <NavLink to="/dashboard" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')}>
        📊 Dashboard
      </NavLink>
      <NavLink to="/approvals" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')}>
        <span style={{ flex: 1 }}>⏳ Approvals</span>
        {pendingCount > 0 && (
          <span style={{ background: 'var(--review)', color: '#000', borderRadius: 10, padding: '1px 7px', fontSize: 10, fontWeight: 700 }}>
            {pendingCount}
          </span>
        )}
      </NavLink>
      <NavLink to="/transactions" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')}>
        📋 Transactions
      </NavLink>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <div className="main">
          <Routes>
            <Route path="/" element={<BuyerView />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/transactions/:id" element={<TransactionDetail />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
