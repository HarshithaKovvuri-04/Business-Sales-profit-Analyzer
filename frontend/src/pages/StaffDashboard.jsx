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
      <h1 className="text-2xl font-semibold mb-4">Staff Dashboard</h1>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-white rounded shadow">
          <h3 className="font-medium">Operational Stats (Today)</h3>
          <div>Total items sold: {stats? stats.total_items_sold_today: '—'}</div>
          <div>Transactions today: {stats? stats.transactions_today: '—'}</div>
        </div>

        <div className="p-4 bg-white rounded shadow">
          <h3 className="font-medium">Low Stock Alerts</h3>
          <ul>
            {lowStock.length === 0 && <li>No low-stock items</li>}
            {lowStock.map(i=> <li key={i.id}>{i.item_name} — {i.quantity}</li>)}
          </ul>
        </div>

        <div className="p-4 bg-white rounded shadow col-span-2">
          <h3 className="font-medium">Add Transaction</h3>
          <div className="mt-2">
            <Button onClick={()=>setShowModal(true)}>Add Transaction</Button>
            {showModal && (
              <TransactionModal visible={showModal} onClose={()=>setShowModal(false)} onSaved={async ()=>{ api.get(`/staff/stats/today?business_id=${activeBusiness.id}`).then(r=> setStats(r.data)).catch(()=> setStats(null)) }} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
