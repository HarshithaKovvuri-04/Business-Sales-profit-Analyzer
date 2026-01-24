import React, {useContext} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import { AuthContext } from '../contexts/AuthContext'

export default function Topbar(){
  const { businesses, activeBusiness, setActiveBusiness } = useContext(BusinessContext)
  const { user } = useContext(AuthContext)

  return (
    <div className="flex items-center justify-between p-4 border-b bg-transparent">
      <div className="flex items-center gap-4">
        <select value={activeBusiness?.id || ''} onChange={(e)=>{
          const b = businesses.find(x=> x.id == e.target.value)
          setActiveBusiness(b)
        }} className="px-3 py-2 rounded-md bg-white/40 glass">
          {businesses.map(b=> <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-sm text-slate-600">{user?.username}</div>
        <div className="px-2 py-1 text-xs bg-indigo-100 rounded">{user?.role}</div>
      </div>
    </div>
  )
}
