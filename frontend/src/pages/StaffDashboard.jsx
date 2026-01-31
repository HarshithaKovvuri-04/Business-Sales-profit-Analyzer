import React, {useContext, useEffect, useState} from 'react'
import api from '../api/axios'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import TransactionModal from '../components/TransactionModal'

export default function StaffDashboard(){
  const { user } = useContext(AuthContext)
  const { activeBusiness } = useContext(BusinessContext)
  const [lowStock, setLowStock] = useState([])
  const [stats, setStats] = useState(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(()=>{
    if(!user || user.role !== 'staff' || !activeBusiness) return
    api.get(`/staff/low_stock?business_id=${activeBusiness.id}`).then(res=> setLowStock(res.data)).catch(()=> setLowStock([]))
    api.get(`/staff/stats/today?business_id=${activeBusiness.id}`).then(res=> setStats(res.data)).catch(()=> setStats(null))
  }, [user, activeBusiness])

  if(!user || user.role !== 'staff') return <div>Access denied</div>
  if(!activeBusiness) return <div>Please select a business.</div>
  const submitSale = async (e)=>{
    e.preventDefault()
    try{
      // Build payload consistent with owner flow: use same /transactions endpoint
      const payload = {
        business_id: activeBusiness.id,
        type: 'Income',
        amount: parseFloat(amount),
      }
      if(inventoryId){
        payload.source = 'inventory'
        payload.inventory_id = Number(inventoryId)
        payload.used_quantity = Number(usedQty || 0)
      }
      await api.post('/transactions', payload)
      // refresh stats-only view
      api.get(`/staff/stats/today?business_id=${activeBusiness.id}`).then(r=> setStats(r.data))
      alert('Sale recorded')
    }catch(err){
      console.error(err)
      alert(err?.response?.data?.detail || 'Failed to record sale')
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Staff Dashboard</h1>
        <div>
          <Button onClick={()=>setShowModal(true)} className="px-6 py-3 text-base">Add Transaction</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <h3 className="font-medium text-slate-500">Operational Stats (Today)</h3>
          <div className="mt-2 text-lg font-semibold">{stats? stats.total_items_sold_today: '—'}</div>
          <div className="text-sm text-slate-500">Items sold</div>
          <div className="mt-3 text-lg font-semibold">{stats? stats.transactions_today: '—'}</div>
          <div className="text-sm text-slate-500">Transactions</div>
        </Card>

        <Card>
          <h3 className="font-medium text-slate-500">Low Stock Alerts</h3>
          <ul className="mt-2 space-y-2">
            {lowStock.length === 0 && <li className="text-sm text-slate-500">No low-stock items</li>}
            {lowStock.map(i=> <li key={i.id} className="flex justify-between"><span>{i.item_name}</span><span className={`inline-block px-2 py-1 rounded-full text-sm ${i.quantity<=5?'bg-fintech-danger/10 text-fintech-danger':'bg-yellow-100 text-yellow-700'}`}>{i.quantity}</span></li>)}
          </ul>
        </Card>

        <Card className="md:col-span-3">
          <h3 className="font-medium text-slate-500">Quick Actions</h3>
          <div className="mt-3 flex gap-3">
            <Button onClick={()=>setShowModal(true)}>Add Transaction</Button>
            <Button variant="ghost" onClick={()=>{ api.get(`/staff/stats/today?business_id=${activeBusiness.id}`).then(r=> setStats(r.data)).catch(()=> setStats(null)) }}>Refresh</Button>
          </div>
        </Card>

        {showModal && (
          <TransactionModal visible={showModal} onClose={()=>setShowModal(false)} onSaved={async ()=>{ api.get(`/staff/stats/today?business_id=${activeBusiness.id}`).then(r=> setStats(r.data)).catch(()=> setStats(null)) }} />
        )}
      </div>
    </div>
  )
}
