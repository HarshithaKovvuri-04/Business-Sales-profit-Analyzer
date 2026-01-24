import React, {useState, useContext} from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'

const items = [
  {to:'/dashboard', label:'Dashboard'},
  {to:'/businesses', label:'Businesses'},
  {to:'/finance', label:'Finance'},
  {to:'/inventory', label:'Inventory'},
  {to:'/settings', label:'Settings'}
]

export default function Sidebar(){
  const [collapsed, setCollapsed] = useState(false)
  const { user, logout } = useContext(AuthContext)
  const navigate = useNavigate()

  return (
    <aside className={`h-screen p-4 transition-width duration-200 ${collapsed? 'w-20':'w-64'} bg-white border-r`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md bg-gradient-to-br from-indigo-500 to-pink-500 flex items-center justify-center text-white font-bold">BA</div>
          {!collapsed && <div>
            <div className="font-semibold">BizAnalyzer AI</div>
            <div className="text-xs text-slate-500">Analytics</div>
          </div>}
        </div>
        <button className="text-sm" onClick={()=>setCollapsed(!collapsed)}>{collapsed? '▶':'◀'}</button>
      </div>

      <nav className="flex flex-col gap-1">
        {items.map(i=> (
          <NavLink key={i.to} to={i.to} className={({isActive})=>`p-3 rounded-md hover:bg-slate-100 ${isActive? 'bg-indigo-50':''}`}>
            {!collapsed? i.label: i.label[0]}
          </NavLink>
        ))}
        <button className="mt-auto p-3 rounded-md text-left hover:bg-red-50 text-red-600" onClick={()=>{logout(); navigate('/login')}}>Logout</button>
      </nav>
    </aside>
  )
}
