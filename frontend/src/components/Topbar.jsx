import React, {useContext} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import { AuthContext } from '../contexts/AuthContext'

export default function Topbar(){
  const { businesses, activeBusiness, setActiveBusiness } = useContext(BusinessContext)
  const { user } = useContext(AuthContext)

  return (
    <header className="flex items-center justify-between p-4 border-b bg-transparent">
      <div className="flex items-center gap-4">
        <select value={activeBusiness?.id || ''} onChange={(e)=>{
          const b = businesses.find(x=> x.id == e.target.value)
          setActiveBusiness(b)
        }} className="px-3 py-2 rounded-lg bg-white/60 border border-slate-100">
          {businesses.map(b=> <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
      </div>

      <div className="flex items-center gap-4">
        <button aria-label="Notifications" className="p-2 rounded-lg hover:bg-slate-50">
          🔔
        </button>
        <div className="flex items-center gap-3">
          <div className="text-sm text-slate-700">{user?.username}</div>
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-fintech-accent to-fintech-accent2 flex items-center justify-center text-white">{(user?.username || 'U').slice(0,1).toUpperCase()}</div>
        </div>
      </div>
    </header>
  )
}
