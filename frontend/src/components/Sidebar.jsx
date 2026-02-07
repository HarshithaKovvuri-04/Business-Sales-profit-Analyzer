import React, {useState, useContext} from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'

function buildItemsForRole(role){
  if(!role) return [
    {to:'/dashboard', label:'Dashboard'},
    {to:'/businesses', label:'Businesses'},
  ]
  if(role === 'owner') return [
    {to:'/dashboard', label:'Dashboard'},
    {to:'/businesses', label:'Businesses'},
    {to:'/finance', label:'Finance'},
    {to:'/inventory', label:'Inventory'},
    {to:'/settings', label:'Settings'}
  ]
  if(role === 'accountant') return [
    {to:'/businesses', label:'Businesses'},
    {to:'/accountant', label:'Financial Dashboard'},
    {to:'/finance', label:'Finance'},
    {to:'/inventory', label:'Inventory'},
    {to:'/settings', label:'Settings'}
  ]
  // staff
  return [
    {to:'/businesses', label:'Businesses'},
    {to:'/staff', label:'Staff Dashboard'},
    {to:'/inventory', label:'Inventory'},
    {to:'/finance', label:'Finance'}
  ]
}

export default function Sidebar(){
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout } = useContext(AuthContext)
  const navigate = useNavigate()
  const items = buildItemsForRole(user?.role)

  return (
    <aside className={`h-screen p-4 transition-width duration-200 ${collapsed? 'w-20':'w-64'} sidebar-surface shadow-elevated`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-fintech-accent to-fintech-accent2 flex items-center justify-center text-white font-bold">BA</div>
          {!collapsed && <div>
            <div className="font-semibold">BizAnalyzer</div>
            <div className="text-xs muted">Analytics</div>
          </div>}
        </div>
        <button className="text-sm" onClick={()=>setCollapsed(!collapsed)} aria-label="Toggle sidebar">{collapsed? '▶':'◀'}</button>
      </div>

      <nav className="flex flex-col gap-1">
        {items.map(i=> (
          <NavLink key={i.to} to={i.to} className={({isActive})=>`p-3 rounded-lg transition-colors text-sm ${isActive? 'bg-gradient-to-r from-fintech-accent/10 to-fintech-accent2/8 text-fintech-accent font-medium' : 'text-slate-700 hover:bg-slate-50'}`}>
            {!collapsed? i.label: i.label[0]}
          </NavLink>
        ))}
        <button className="mt-auto p-3 rounded-lg text-left hover:bg-red-50 text-red-600" onClick={()=>{logout(); navigate('/login')}}>Logout</button>
      </nav>
    </aside>
  )
}
