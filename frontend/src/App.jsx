import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import './index.css'
import BuyerView from './pages/BuyerView'
import Dashboard from './pages/Dashboard'
import Approvals from './pages/Approvals'
import Transactions from './pages/Transactions'
import TransactionDetail from './pages/TransactionDetail'
import { getPending } from './api'

function useTheme() {
  const [theme, setTheme] = useState(() => localStorage.getItem('rzp_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('rzp_theme', theme)
  }, [theme])

  return [theme, () => setTheme(t => t === 'dark' ? 'light' : 'dark')]
}

function Sidebar({ theme, toggleTheme }) {
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    function fetchPending() {
      getPending().then(r => setPendingCount(r.data.length)).catch(() => {})
    }
    fetchPending()
    const interval = setInterval(fetchPending, 10000)
    return () => clearInterval(interval)
  }, [])

  const navItems = [
    { to: '/',             icon: '⚡', label: 'AI Buyer',      end: true },
    { to: '/dashboard',    icon: '▦',  label: 'Dashboard' },
    { to: '/approvals',    icon: '◎',  label: 'Approvals',    badge: pendingCount },
    { to: '/transactions', icon: '≡',  label: 'Transactions' },
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">⚡</div>
          <div className="sidebar-brand-name">AI<span>Gateway</span></div>
        </div>
        <div className="sidebar-tagline">Powered by Razorpay</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
          >
            <span className="nav-link-icon">{item.icon}</span>
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge > 0 && <span className="pending-dot">{item.badge}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <span className="sidebar-footer-label">TechKart Store</span>
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'dark' ? '☀ Light' : '☾ Dark'}
        </button>
      </div>
    </div>
  )
}

function AnimatedMain({ children }) {
  const location = useLocation()
  return (
    <div key={location.pathname} className="fade-up" style={{ minHeight: '100%' }}>
      {children}
    </div>
  )
}

export default function App() {
  const [theme, toggleTheme] = useTheme()

  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar theme={theme} toggleTheme={toggleTheme} />
        <div className="main">
          <AnimatedMain>
            <Routes>
              <Route path="/"               element={<BuyerView />} />
              <Route path="/dashboard"      element={<Dashboard />} />
              <Route path="/approvals"      element={<Approvals />} />
              <Route path="/transactions"   element={<Transactions />} />
              <Route path="/transactions/:id" element={<TransactionDetail />} />
            </Routes>
          </AnimatedMain>
        </div>
      </div>
    </BrowserRouter>
  )
}
