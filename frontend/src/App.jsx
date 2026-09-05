import { BrowserRouter, Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import './index.css'
import BuyerView from './pages/BuyerView'
import Dashboard from './pages/Dashboard'
import Approvals from './pages/Approvals'
import Transactions from './pages/Transactions'
import TransactionDetail from './pages/TransactionDetail'

function Sidebar() {
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
        ⏳ Approvals
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
