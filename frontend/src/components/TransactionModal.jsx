import React, {useState, useEffect, useContext} from 'react'
import Card from './ui/Card'
import Button from './ui/Button'
import api from '../api/axios'
import { BusinessContext } from '../contexts/BusinessContext'
import { AuthContext } from '../contexts/AuthContext'

export default function TransactionModal({visible, onClose, onSaved}){
  const { activeBusiness } = useContext(BusinessContext)
  const { user } = useContext(AuthContext)
  const [type, setType] = useState('Income')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('')
  const [source, setSource] = useState('manual')
  const [inventoryItems, setInventoryItems] = useState([])
  const [inventoryLoading, setInventoryLoading] = useState(false)
  const [selectedInventoryId, setSelectedInventoryId] = useState(null)
  const [usedQuantity, setUsedQuantity] = useState(1)
  const [invoiceFile, setInvoiceFile] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(()=>{
    if(visible && activeBusiness){
      fetchAvailableInventory()
    }
  }, [visible, activeBusiness])

  const fetchAvailableInventory = async ()=>{
    if(!activeBusiness) return
    setInventoryLoading(true)
    try{
      const res = await api.get('/inventory/available', { params: { business_id: activeBusiness.id } })
      setInventoryItems(res.data || [])
    }catch(err){
      console.error('fetch available inventory', err)
      setInventoryItems([])
    }finally{ setInventoryLoading(false) }
  }

  const save = async (e)=>{
    e && e.preventDefault()
    if(!activeBusiness) return alert('Select a business')
    setSaving(true)
    try{
      let invoice_url = null
      if(invoiceFile){
        const fd = new FormData()
        fd.append('business_id', activeBusiness.id)
        fd.append('file', invoiceFile)
        const up = await api.post('/transactions/upload', fd, {headers: {'Content-Type': 'multipart/form-data'}})
        invoice_url = up.data.invoice_url
      }

      if(selectedInventoryId && selectedInventoryId !== 'manual'){
        const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
        if(!inv) throw new Error('Please select an inventory item')
        const qty = Number(usedQuantity || 0)
        if(qty <= 0) throw new Error('Quantity must be at least 1')
        if(type === 'Expense'){
          if(qty > inv.quantity) throw new Error('Selected quantity exceeds available stock')
        }
        let payload
        if(type === 'Expense'){
          const unitCost = Number(inv.cost_price || 0)
          const calcAmount = Number((qty * unitCost).toFixed(2))
          payload = { business_id: activeBusiness.id, type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: calcAmount, category: inv.category || null, invoice_url }
        } else {
          const saleAmount = parseFloat(amount)
          if(isNaN(saleAmount) || saleAmount <= 0) throw new Error('Enter a valid sale amount')
          payload = { business_id: activeBusiness.id, type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: saleAmount, category: inv.category || null, invoice_url }
        }
        await api.post('/transactions', payload)
      } else {
        await api.post('/transactions', {business_id: activeBusiness.id, type, amount: parseFloat(amount), category, invoice_url})
      }

      // On success notify and refresh
      try{ window.dispatchEvent(new CustomEvent('inventory:updated')) }catch(e){}
      if(onSaved) await onSaved()
      if(user?.role === 'staff'){
        alert('Transaction submitted')
      }
      // reset
      setType('Income'); setAmount(''); setCategory(''); setSelectedInventoryId(null); setUsedQuantity(1); setInvoiceFile(null)
      onClose && onClose()
    }catch(err){
      const detail = err?.response?.data?.detail || err.message || ''
      if(err?.response?.status === 400 && /insufficient/i.test(detail)){
        alert('Not enough stock for that item. Please reduce quantity or restock.')
      } else {
        console.error(err)
        alert(detail || 'Failed to save transaction')
      }
    }finally{ setSaving(false) }
  }

  if(!visible) return null
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black/30">
      <Card className="w-full max-w-md">
        <h4 className="text-lg font-semibold mb-3">New Transaction</h4>
        <form onSubmit={save} className="flex flex-col gap-2">
          <div className="flex gap-2">
            <button type="button" className={`flex-1 px-3 py-2 rounded ${type==='Income'? 'bg-green-600 text-white':''}`} onClick={()=>setType('Income')}>Income</button>
            <button type="button" className={`flex-1 px-3 py-2 rounded ${type==='Expense'? 'bg-red-600 text-white':''}`} onClick={()=>setType('Expense')}>Expense</button>
          </div>

          {(type === 'Expense' || type === 'Income') && (
            <div className="flex gap-2">
              <label className="flex items-center gap-2">
                <input type="radio" name="source" checked={source==='manual'} onChange={()=>{ setSource('manual'); setSelectedInventoryId(null); }} />
                <span className="text-sm">Manual</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="source" checked={source==='inventory'} onChange={()=>{ setSource('inventory'); }} />
                <span className="text-sm">{type === 'Income' ? 'Sell Inventory' : 'Purchase Inventory'}</span>
              </label>
            </div>
          )}

          {!(selectedInventoryId && selectedInventoryId !== 'manual' && type === 'Expense') ? (
            <input placeholder="Amount (₹)" type="number" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} className="px-3 py-2 rounded border" required />
          ) : (
            <input placeholder="Amount (auto)" type="number" step="0.01" value={(() => {
              const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
              if(!inv) return ''
              return Number((Number(inv.cost_price || 0) * Number(usedQuantity || 0)).toFixed(2))
            })()} readOnly className="px-3 py-2 rounded border bg-slate-50" />
          )}

          {(type === 'Expense' || type === 'Income') ? (
            <div>
              <label className="text-sm">Category / Inventory</label>
              <select value={selectedInventoryId ?? ''} onChange={e=>{
                const v = e.target.value
                setSelectedInventoryId(v === '' ? null : (v === 'manual' ? 'manual' : Number(v)))
                setUsedQuantity(1)
                if(v === 'manual') setAmount('')
              }} className="w-full px-3 py-2 rounded border">
                <option value="">-- select inventory or Manual --</option>
                <option value="manual">Manual category</option>
                {inventoryItems.map(it=> (
                  <option key={it.id} value={it.id}>{(it.category && it.category.trim() !== '') ? `${it.category} – ${it.item_name}` : `Uncategorized – ${it.item_name}`} (Available: {it.quantity})</option>
                ))}
              </select>
              {selectedInventoryId === 'manual' && (
                <input placeholder="Category" value={category} onChange={e=>setCategory(e.target.value)} className="mt-2 px-3 py-2 rounded border w-full" required />
              )}
            </div>
          ) : (
            <input placeholder="Category" value={category} onChange={e=>setCategory(e.target.value)} className="px-3 py-2 rounded border" required />
          )}

          {(type === 'Expense' || type === 'Income') && selectedInventoryId && selectedInventoryId !== 'manual' && (
            <div className="flex flex-col gap-2">
              <div className="text-sm text-slate-500">Available: {inventoryItems.find(i=>i.id===Number(selectedInventoryId))?.quantity ?? 0}</div>
              <div>
                <label className="text-sm">Quantity</label>
                <input type="number" min={1} value={usedQuantity} onChange={e=>{
                  const v = Number(e.target.value || 0)
                  const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
                  if(type === 'Expense'){
                    if(inv){
                      if(v > inv.quantity){ setUsedQuantity(inv.quantity); return }
                      if(v < 1) return setUsedQuantity(1)
                    }
                  } else {
                    if(v < 1) return setUsedQuantity(1)
                  }
                  setUsedQuantity(v)
                }} className="w-full px-3 py-2 rounded border" />
              </div>
            </div>
          )}

          <input type="file" onChange={e=>setInvoiceFile(e.target.files[0])} className="px-3 py-2 rounded border" />
          <div className="flex gap-2 justify-end">
            <Button type="submit" disabled={saving}>{saving? 'Saving...':'Save'}</Button>
            <Button variant="ghost" onClick={()=>{ onClose && onClose(); }} >Cancel</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
