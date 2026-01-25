import React, {useContext, useState, useEffect} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import api from '../api/axios'

export default function Finance(){
  const { activeBusiness } = useContext(BusinessContext)
  const [show, setShow] = useState(false)
  const [type, setType] = useState('Income')
  const [amount, setAmount] = useState('')
  const [category, setCategory] = useState('')
  // Inventory-aware form state
  const [source, setSource] = useState('manual') // 'manual' | 'inventory'
  const [inventoryItems, setInventoryItems] = useState([])
  const [inventoryLoading, setInventoryLoading] = useState(false)
  const [selectedInventoryId, setSelectedInventoryId] = useState(null)
  const [usedQuantity, setUsedQuantity] = useState(1)
  const [summary, setSummary] = useState({income:0, expense:0})
  const [invoiceFile, setInvoiceFile] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loadingTx, setLoadingTx] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingTx, setEditingTx] = useState(null)
  const [editInvoiceFile, setEditInvoiceFile] = useState(null)
  const [editSelectedInventoryId, setEditSelectedInventoryId] = useState(null)
  const [editUsedQuantity, setEditUsedQuantity] = useState(1)
  const [editSource, setEditSource] = useState('manual')
  const [updating, setUpdating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const { user } = useContext(AuthContext)
  

  useEffect(()=>{
    if(activeBusiness){
      api.get(`/summary/${activeBusiness.id}`).then(res=> setSummary(res.data)).catch(()=>{})
      fetchTransactions()
      fetchAvailableInventory()
    } else {
      setTransactions([])
    }
  }, [activeBusiness])

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

  const fetchTransactions = async ()=>{
    if(!activeBusiness) return
    setLoadingTx(true)
    try{
      const res = await api.get('/transactions', { params: { business_id: activeBusiness.id } })
      setTransactions(res.data || [])
    }catch(err){
      console.error('fetch transactions', err)
      setTransactions([])
    }finally{ setLoadingTx(false) }
  }

  const save = async (e)=>{
    e.preventDefault()
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

      // If an inventory item is selected (for Expense or Income), build inventory payload
      if(selectedInventoryId && selectedInventoryId !== 'manual'){
        const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
        if(!inv){
          throw new Error('Please select an inventory item')
        }
        const qty = Number(usedQuantity || 0)
        if(qty <= 0){
          throw new Error('Quantity must be at least 1')
        }
        if(type === 'Expense'){
          // Expense must not exceed available stock
          if(qty > inv.quantity){
            throw new Error('Selected quantity exceeds available stock')
          }
        }
        // Build payload differently for purchases (Expense) and sales (Income).
        let payload
        if(type === 'Expense'){
          // auto-calc amount = qty * cost_price; do not allow manual override for purchases
          const unitCost = Number(inv.cost_price || 0)
          const calcAmount = Number((qty * unitCost).toFixed(2))
          payload = { business_id: activeBusiness.id, type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: calcAmount, category: inv.category || null, invoice_url }
        } else {
          // Income (sale): amount must be provided by user (sale revenue)
          const saleAmount = parseFloat(amount)
          if(isNaN(saleAmount) || saleAmount <= 0) throw new Error('Enter a valid sale amount')
          payload = { business_id: activeBusiness.id, type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: saleAmount, category: inv.category || null, invoice_url }
        }
        await api.post('/transactions', payload)
      } else {
        // Manual flow (Income or Expense manual)
        await api.post('/transactions', {business_id: activeBusiness.id, type, amount: parseFloat(amount), category, invoice_url})
      }

      await fetchTransactions()
      // refresh available inventory immediately after successful inventory transaction
      await fetchAvailableInventory()
      // notify other parts of the app (Dashboard) that inventory changed so low-stock alerts refresh
      try{ window.dispatchEvent(new CustomEvent('inventory:updated')) }catch(e){}
    }catch(err){
      const detail = err?.response?.data?.detail || err.message || ''
      // backend returns 400 for validation such as insufficient inventory
      if(err?.response?.status === 400 && /insufficient/i.test(detail)){
        alert('Not enough stock for that item. Please reduce quantity or restock.')
      } else {
        console.error(err)
        alert(detail || 'Failed to save transaction')
      }
      setSaving(false)
      return
    }finally{ setSaving(false) }
    setShow(false); setAmount(''); setCategory('')
    setInvoiceFile(null)
    // reset inventory-specific form state as well
    setSelectedInventoryId(null)
    setUsedQuantity(1)
    // refresh summary
    const res = await api.get(`/summary/${activeBusiness.id}`)
    setSummary(res.data)
  }

  const openEdit = (tx)=>{
    setEditingTx({...tx})
    setEditInvoiceFile(null)
    // initialize edit modal inventory state if transaction is inventory-linked
    if(tx?.source === 'inventory'){
      setEditSource('inventory')
      setEditSelectedInventoryId(tx.inventory_id ?? null)
      setEditUsedQuantity(tx.used_quantity ?? 1)
    } else {
      setEditSource('manual')
      setEditSelectedInventoryId(null)
      setEditUsedQuantity(1)
    }
  }

  const saveEdit = async (e)=>{
    e.preventDefault()
    if(!editingTx) return
    setUpdating(true)
    try{
      let invoice_url = editingTx.invoice_url || null
      if(editInvoiceFile){
        const fd = new FormData()
        fd.append('business_id', activeBusiness.id)
        fd.append('file', editInvoiceFile)
        const up = await api.post('/transactions/upload', fd, {headers: {'Content-Type': 'multipart/form-data'}})
        invoice_url = up.data.invoice_url
      }
      // Build payload depending on whether this is inventory-linked
      if(editSource === 'inventory'){
        const inv = inventoryItems.find(i=>i.id === Number(editSelectedInventoryId))
        if(!inv) throw new Error('Please select an inventory item')
        const qty = Number(editUsedQuantity || 0)
        if(qty <= 0) throw new Error('Quantity must be at least 1')
        if(editingTx.type === 'Expense'){
          const prevUsed = Number(editingTx.used_quantity || 0)
          // if editing the same inventory item, available effectively includes previous used quantity
          const sameInventory = Number(editingTx.inventory_id) === Number(inv.id)
          const maxAllowed = sameInventory ? (inv.quantity + prevUsed) : inv.quantity
          if(qty > maxAllowed) throw new Error('Selected quantity exceeds available stock')
        }
        let payload
        if(editingTx.type === 'Expense'){
          // purchases: amount recalculated from cost_price
          const calcAmount = Number((qty * Number(inv.cost_price || 0)).toFixed(2))
          payload = { type: editingTx.type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: calcAmount, category: inv.category || null, invoice_url }
        } else {
          // sales: amount should come from editable field on editingTx (sale revenue)
          const saleAmount = parseFloat(editingTx.amount)
          if(isNaN(saleAmount) || saleAmount <= 0) throw new Error('Enter a valid sale amount')
          payload = { type: editingTx.type, source: 'inventory', inventory_id: inv.id, used_quantity: qty, amount: saleAmount, category: inv.category || null, invoice_url }
        }
        await api.put(`/transactions/${editingTx.id}`, payload)
      } else {
        // switching to manual or editing non-inventory transaction
        // if switching from inventory -> manual, backend will reconcile stock
        await api.put(`/transactions/${editingTx.id}`, { type: editingTx.type, amount: parseFloat(editingTx.amount), category: editingTx.category, invoice_url })
      }

      await fetchTransactions()
      // refresh inventory and notify dashboard
      await fetchAvailableInventory()
      try{ window.dispatchEvent(new CustomEvent('inventory:updated')) }catch(e){}
      setEditingTx(null)
    }catch(err){
      console.error(err)
      const detail = err?.response?.data?.detail || err.message || 'Failed to update transaction'
      alert(detail)
    }finally{ setUpdating(false) }
  }

  const doDelete = async (txId)=>{
    if(!confirm('Delete this transaction?')) return
    setDeletingId(txId)
    try{
      await api.delete(`/transactions/${txId}`)
      setTransactions(prev => prev.filter(t=>t.id !== txId))
      const res = await api.get(`/summary/${activeBusiness.id}`)
      setSummary(res.data)
    }catch(err){
      console.error(err)
      alert(err?.response?.data?.detail || err.message || 'Failed to delete')
    }finally{ setDeletingId(null) }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Transactions</h3>
          <Button onClick={()=>setShow(true)}>Add Transaction</Button>
        </div>
        {/* transaction table placeholder - will be populated by API */}
        <Card>
          {loadingTx ? (
            <div className="text-sm text-slate-500">Loading transactions...</div>
          ) : (
            <div>
              {transactions.length === 0 ? (
                <div className="text-sm text-slate-500">No transactions yet</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left">
                      <th className="p-2">Type</th>
                      <th className="p-2">Amount</th>
                      <th className="p-2">Category</th>
                      <th className="p-2">Invoice</th>
                      <th className="p-2">Date</th>
                      <th className="p-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map(tx=> (
                      <tr key={tx.id} className="border-t">
                        <td className="p-2">{tx.type}</td>
                        <td className="p-2">₹ {Number(tx.amount).toFixed(2)}</td>
                        <td className="p-2">{tx.category || '-'}</td>
                        <td className="p-2">{tx.invoice_url ? <a className="text-blue-600" href={tx.invoice_url}>View</a> : '-'}</td>
                        <td className="p-2">{new Date(tx.created_at).toLocaleString()}</td>
                        <td className="p-2">
                          {(activeBusiness?.role === 'owner' || activeBusiness?.role === 'accountant') ? (
                            <div className="flex gap-2">
                              <Button size="sm" onClick={()=>openEdit(tx)}>Edit</Button>
                              <Button size="sm" variant="danger" onClick={()=>doDelete(tx.id)} disabled={deletingId===tx.id}>{deletingId===tx.id? 'Deleting...':'Delete'}</Button>
                            </div>
                          ) : (
                            <span className="text-slate-500">No actions</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </Card>
      </div>

      <div>
        <Card>
          <div className="text-sm text-slate-500">Summary</div>
          <div className="text-xl font-semibold">Income: ₹ {summary.income?.toFixed(2) || '0.00'}</div>
          <div className="text-xl font-semibold">Expense: ₹ {summary.expense?.toFixed(2) || '0.00'}</div>
          <div className={`mt-2 px-2 py-1 rounded ${((summary.income||0)-(summary.expense||0))>=0? 'bg-green-100 text-green-700':'bg-red-100 text-red-700'}`}>Net: ₹ {(((summary.income||0)-(summary.expense||0))).toFixed(2)}</div>
        </Card>
      </div>

      {show && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">New Transaction</h4>
            <form onSubmit={save} className="flex flex-col gap-2">
              <div className="flex gap-2">
                <button type="button" className={`flex-1 px-3 py-2 rounded ${type==='Income'? 'bg-green-600 text-white':''}`} onClick={()=>setType('Income')}>Income</button>
                <button type="button" className={`flex-1 px-3 py-2 rounded ${type==='Expense'? 'bg-red-600 text-white':''}`} onClick={()=>setType('Expense')}>Expense</button>
              </div>
              {/* If Expense or Income, allow choosing source: manual entry or inventory-linked */}
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

              {/* Amount input: editable for manual entries and for inventory-linked Income (sales).
                  For inventory-linked Expense (purchases) the amount is auto-calculated from cost_price. */}
              {!(selectedInventoryId && selectedInventoryId !== 'manual' && type === 'Expense') ? (
                <input placeholder="Amount (₹)" type="number" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} className="px-3 py-2 rounded border" required />
              ) : (
                // show auto-calculated amount for inventory purchase (Expense); not editable by user
                <input placeholder="Amount (auto)" type="number" step="0.01" value={(() => {
                  const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
                  if(!inv) return ''
                  return Number((Number(inv.cost_price || 0) * Number(usedQuantity || 0)).toFixed(2))
                })()} readOnly className="px-3 py-2 rounded border bg-slate-50" />
              )}

              {/* Category: for Expense show inventory dropdown (with Manual option), for Income keep text input */}
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

              {/* When an inventory item is selected show quantity selector and available info */}
              {(type === 'Expense' || type === 'Income') && selectedInventoryId && selectedInventoryId !== 'manual' && (
                <div className="flex flex-col gap-2">
                  <div className="text-sm text-slate-500">Available: {inventoryItems.find(i=>i.id===Number(selectedInventoryId))?.quantity ?? 0}</div>
                  <div>
                    <label className="text-sm">Quantity</label>
                    <input type="number" min={1} value={usedQuantity} onChange={e=>{
                      const v = Number(e.target.value || 0)
                      const inv = inventoryItems.find(i=>i.id === Number(selectedInventoryId))
                      // For Expense enforce upper bound = available stock
                      if(type === 'Expense'){
                        if(inv){
                          if(v > inv.quantity){ setUsedQuantity(inv.quantity); return }
                          if(v < 1) return setUsedQuantity(1)
                        }
                      } else {
                        // Income: only enforce min >=1, no upper bound
                        if(v < 1) return setUsedQuantity(1)
                      }
                      setUsedQuantity(v)
                    }} className="w-full px-3 py-2 rounded border" />
                    {type === 'Expense' && Number(usedQuantity) > (inventoryItems.find(i=>i.id===Number(selectedInventoryId))?.quantity || 0) && (
                      <div className="text-sm text-red-600">Quantity exceeds available stock</div>
                    )}
                  </div>
                </div>
              )}

              <input type="file" onChange={e=>setInvoiceFile(e.target.files[0])} className="px-3 py-2 rounded border" />
              <div className="flex gap-2 justify-end">
                <Button type="submit">Save</Button>
                <Button variant="ghost" onClick={()=>setShow(false)}>Cancel</Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {editingTx && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">Edit Transaction</h4>
            <form onSubmit={saveEdit} className="flex flex-col gap-2">
              <div className="flex gap-2">
                <button type="button" className={`flex-1 px-3 py-2 rounded ${editingTx.type==='Income'? 'bg-green-600 text-white':''}`} onClick={()=>setEditingTx(et=>({...et, type:'Income'}))}>Income</button>
                <button type="button" className={`flex-1 px-3 py-2 rounded ${editingTx.type==='Expense'? 'bg-red-600 text-white':''}`} onClick={()=>setEditingTx(et=>({...et, type:'Expense'}))}>Expense</button>
              </div>

              {/* If editing an Expense or Income allow switching source */}
              {(editingTx.type === 'Expense' || editingTx.type === 'Income') && (
                <div className="flex gap-2">
                  <label className="flex items-center gap-2">
                    <input type="radio" name="editSource" checked={editSource==='manual'} onChange={()=>{ setEditSource('manual'); setEditSelectedInventoryId(null); setEditUsedQuantity(1); }} />
                    <span className="text-sm">Manual</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="radio" name="editSource" checked={editSource==='inventory'} onChange={()=>{ setEditSource('inventory'); }} />
                    <span className="text-sm">{editingTx.type === 'Income' ? 'Sell Inventory' : 'Purchase Inventory'}</span>
                  </label>
                </div>
              )}

              {/* Amount input: editable unless editing a purchase (Expense) linked to inventory,
                  which is auto-calculated from cost_price. */}
              {!(editSource === 'inventory' && editSelectedInventoryId && editingTx.type === 'Expense') ? (
                <input placeholder="Amount (₹)" type="number" step="0.01" value={editingTx.amount} onChange={e=>setEditingTx(et=>({...et, amount: e.target.value}))} className="px-3 py-2 rounded border" required />
              ) : (
                <input placeholder="Amount (auto)" type="number" step="0.01" value={(() => {
                  const inv = inventoryItems.find(i=>i.id === Number(editSelectedInventoryId))
                  if(!inv) return ''
                  return Number((Number(inv.cost_price || 0) * Number(editUsedQuantity || 0)).toFixed(2))
                })()} readOnly className="px-3 py-2 rounded border bg-slate-50" />
              )}

              {/* Category / Inventory selector for edit */}
              {(editingTx.type === 'Expense' || editingTx.type === 'Income') ? (
                <div>
                  <label className="text-sm">Category / Inventory</label>
                  <select value={editSelectedInventoryId ?? (editSource === 'manual' ? 'manual' : '')} onChange={e=>{
                    const v = e.target.value
                    setEditSelectedInventoryId(v === '' ? null : (v === 'manual' ? 'manual' : Number(v)))
                    setEditUsedQuantity(1)
                    if(v === 'manual') setEditingTx(et=>({...et, category: et.category || ''}))
                  }} className="w-full px-3 py-2 rounded border">
                    <option value="">-- select inventory or Manual --</option>
                    <option value="manual">Manual category</option>
                    {inventoryItems.map(it=> (
                      <option key={it.id} value={it.id}>{(it.category && it.category.trim() !== '') ? `${it.category} – ${it.item_name}` : `Uncategorized – ${it.item_name}`} (Available: {it.quantity})</option>
                    ))}
                  </select>
                  {editSelectedInventoryId === 'manual' && (
                    <input placeholder="Category" value={editingTx.category || ''} onChange={e=>setEditingTx(et=>({...et, category: e.target.value}))} className="mt-2 px-3 py-2 rounded border w-full" required />
                  )}
                </div>
              ) : (
                <input placeholder="Category" value={editingTx.category || ''} onChange={e=>setEditingTx(et=>({...et, category: e.target.value}))} className="px-3 py-2 rounded border" required />
              )}

              {/* Quantity selector when inventory selected in edit */}
              {editSource === 'inventory' && editSelectedInventoryId && (
                <div className="flex flex-col gap-2">
                  <div className="text-sm text-slate-500">Available: {inventoryItems.find(i=>i.id===Number(editSelectedInventoryId))?.quantity ?? 0}</div>
                  <div>
                    <label className="text-sm">Quantity</label>
                    <input type="number" min={1} value={editUsedQuantity} onChange={e=>{
                      const v = Number(e.target.value || 0)
                      const inv = inventoryItems.find(i=>i.id === Number(editSelectedInventoryId))
                      const prevUsed = Number(editingTx.used_quantity || 0)
                      const sameInventory = Number(editingTx.inventory_id) === Number(editSelectedInventoryId)
                      // For Expense compute a cap; for Income there is no upper bound
                      const maxAllowed = editingTx.type === 'Expense' ? (inv ? (sameInventory ? inv.quantity + prevUsed : inv.quantity) : 0) : Infinity
                      if(inv){
                        if(v > maxAllowed){ setEditUsedQuantity(maxAllowed); return }
                        if(v < 1) return setEditUsedQuantity(1)
                      }
                      setEditUsedQuantity(v)
                    }} className="w-full px-3 py-2 rounded border" />
                    {(() => {
                      if(editingTx.type !== 'Expense') return null
                      const inv = inventoryItems.find(i=>i.id===Number(editSelectedInventoryId))
                      const prevUsed = Number(editingTx.used_quantity || 0)
                      const sameInventory = Number(editingTx.inventory_id) === Number(editSelectedInventoryId)
                      const maxAllowed = inv ? (sameInventory ? inv.quantity + prevUsed : inv.quantity) : 0
                      if(Number(editUsedQuantity) > maxAllowed) return (<div className="text-sm text-red-600">Quantity exceeds available stock</div>)
                      return null
                    })()}
                  </div>
                </div>
              )}

              <div>
                <label className="text-sm">Invoice (replace)</label>
                <input type="file" onChange={e=>setEditInvoiceFile(e.target.files[0])} className="px-3 py-2 rounded border" />
                {editingTx.invoice_url && <div className="text-sm mt-1">Current: <a className="text-blue-600" href={editingTx.invoice_url}>{editingTx.invoice_url}</a></div>}
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="submit" disabled={updating}>{updating? 'Saving...':'Save'}</Button>
                <Button variant="ghost" onClick={()=>{ setEditingTx(null); setEditSelectedInventoryId(null); setEditUsedQuantity(1); setEditSource('manual'); setEditInvoiceFile(null); }}>Cancel</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
