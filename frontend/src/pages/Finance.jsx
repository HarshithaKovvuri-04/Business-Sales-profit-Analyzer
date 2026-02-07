import React, {useContext, useState, useEffect} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import api from '../api/axios'
import TransactionModal from '../components/TransactionModal'

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
  const [viewingTx, setViewingTx] = useState(null)
  const [editInvoiceFile, setEditInvoiceFile] = useState(null)
  const [editSelectedInventoryId, setEditSelectedInventoryId] = useState(null)
  const [editUsedQuantity, setEditUsedQuantity] = useState(1)
  const [editSource, setEditSource] = useState('manual')
  const [updating, setUpdating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const { user } = useContext(AuthContext)
  

  useEffect(()=>{
    if(activeBusiness){
      // Use authoritative analytics summary (COGS-based) for finance totals
      api.get(`/analytics/summary/${activeBusiness.id}`).then(res=>{
        const s = res.data || { total_income:0, total_expense:0, profit:0 }
        setSummary({ income: s.total_income, expense: s.total_expense, profit: s.profit })
      }).catch(()=>{})
      // fetch transactions for all roles (frontend will hide sensitive columns for staff)
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
      // use joined transactions endpoint to include inventory item_name
      const res = await api.get('/transactions/list', { params: { business_id: activeBusiness.id } })
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

      // Refresh transaction list for all roles
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
    const res = await api.get(`/analytics/summary/${activeBusiness.id}`)
    const s = res.data || { total_income:0, total_expense:0, profit:0 }
    setSummary({ income: s.total_income, expense: s.total_expense, profit: s.profit })
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
      const res = await api.get(`/analytics/summary/${activeBusiness.id}`)
      const s = res.data || { total_income:0, total_expense:0, profit:0 }
      setSummary({ income: s.total_income, expense: s.total_expense, profit: s.profit })
    }catch(err){
      console.error(err)
      alert(err?.response?.data?.detail || err.message || 'Failed to delete')
    }finally{ setDeletingId(null) }
  }

  const downloadReceipt = async (txId) => {
    try{
      const res = await api.get(`/transactions/${txId}/receipt`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `transaction_${txId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    }catch(err){
      console.error('download receipt', err)
      alert(err?.response?.data?.detail || err.message || 'Failed to download receipt')
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4 gap-3">
          <h3 className="text-lg font-semibold">Transactions</h3>
          <div className="flex items-center gap-2">
            <input type="date" className="px-3 py-2 rounded-lg border border-slate-200 bg-transparent" />
            {/* Owners and staff may create transactions; accountants are read-only */}
            {activeBusiness?.role !== 'accountant' && (
              <Button onClick={()=>setShow(true)} className="px-5 py-2">Add Transaction</Button>
            )}
          </div>
        </div>
        {/* show transaction history to all roles; staff see a simplified table */}
        <Card>
          {loadingTx ? (
            <div className="text-sm text-slate-500">Loading transactions...</div>
          ) : (
            <div>
              {transactions.length === 0 ? (
                <div className="text-sm text-slate-500">No transactions yet</div>
              ) : (
                <div className="overflow-auto">
                  <table className="w-full text-sm border-separate" style={{borderSpacing: '0 10px'}}>
                    <thead>
                      <tr className="text-left">
                        {activeBusiness?.role === 'staff' ? (
                          <>
                            <th className="p-2 text-slate-500">Item</th>
                            <th className="p-2 text-slate-500">Quantity</th>
                            <th className="p-2 text-slate-500">Selling Price</th>
                            <th className="p-2 text-slate-500">Total Amount</th>
                            <th className="p-2 text-slate-500">Date</th>
                            <th className="p-2 text-slate-500">Actions</th>
                          </>
                        ) : (
                          <>
                            <th className="p-2 text-slate-500">Type</th>
                            <th className="p-2 text-slate-500">Amount</th>
                            <th className="p-2 text-slate-500">Category</th>
                            <th className="p-2 text-slate-500">Invoice</th>
                            <th className="p-2 text-slate-500">Date</th>
                            <th className="p-2 text-slate-500">Actions</th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map(tx=> (
                        <tr key={tx.id} className="bg-card rounded-lg shadow-elevated">
                          {activeBusiness?.role === 'staff' ? (
                            <>
                              <td className="p-3">{tx.item_name || '-'}</td>
                              <td className="p-3">{Number(tx.used_quantity || 1)}</td>
                              <td className="p-3">₹ {Number(tx.amount).toFixed(2)}</td>
                              <td className="p-3">₹ {Number(tx.amount).toFixed(2)}</td>
                              <td className="p-3">{new Date(tx.created_at).toLocaleString()}</td>
                              <td className="p-3">
                                <div className="flex gap-2 items-center">
                                  <Button size="sm" onClick={()=>downloadReceipt(tx.id)}>Download Receipt</Button>
                                </div>
                              </td>
                            </>
                          ) : (
                            <>
                              <td className="p-3">{tx.type}</td>
                              <td className="p-3">₹ {Number(tx.amount).toFixed(2)}</td>
                              <td className="p-3">{tx.category || '-'}</td>
                              <td className="p-3">{tx.invoice_url ? <a className="text-fintech-accent" href={tx.invoice_url}>View</a> : '-'}</td>
                              <td className="p-3">{new Date(tx.created_at).toLocaleString()}</td>
                              <td className="p-3">
                                <div className="flex gap-2 items-center">
                                  {activeBusiness?.role === 'owner' ? (
                                    <>
                                      <div className="flex gap-2">
                                        <Button size="sm" onClick={()=>openEdit(tx)}>Edit</Button>
                                        <Button size="sm" variant="danger" onClick={()=>doDelete(tx.id)} disabled={deletingId===tx.id}>{deletingId===tx.id? 'Deleting...':'Delete'}</Button>
                                      </div>
                                      <Button size="sm" onClick={()=>downloadReceipt(tx.id)}>Download Receipt</Button>
                                    </>
                                  ) : activeBusiness?.role === 'accountant' ? (
                                    <>
                                      <div className="flex gap-2">
                                        <Button size="sm" onClick={()=>setViewingTx(tx)}>View</Button>
                                      </div>
                                      <Button size="sm" onClick={()=>downloadReceipt(tx.id)}>Download Receipt</Button>
                                    </>
                                  ) : (
                                    <div className="flex gap-2 items-center">
                                      <span className="text-slate-500">No actions</span>
                                      <Button size="sm" onClick={()=>downloadReceipt(tx.id)}>Download Receipt</Button>
                                    </div>
                                  )}
                                </div>
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      <div>
        <Card>
          <div className="text-sm text-slate-500">Summary</div>
            <div className="text-lg mt-2">Income</div>
            <div className="text-2xl font-semibold">₹ {Number(summary.income || 0).toFixed(2)}</div>
            <div className="text-lg mt-3">Expense</div>
            <div className="text-2xl font-semibold">₹ {Number(summary.expense || 0).toFixed(2)}</div>
            <div className={`mt-3 px-3 py-1 inline-block rounded-lg ${(Number(summary.profit || 0))>=0? 'bg-fintech-success/10 text-fintech-success':'bg-fintech-danger/10 text-fintech-danger'}`}>Net: ₹ {Number(summary.profit || 0).toFixed(2)}</div>
        </Card>
        <Card className="mt-4">
          <div className="text-sm text-slate-500">Quick Actions</div>
          <div className="flex flex-col gap-2 mt-2">
            {activeBusiness?.role !== 'accountant' && <Button onClick={()=>setShow(true)}>New Transaction</Button>}
            <Button variant="ghost" onClick={()=>{ fetchTransactions(); fetchAvailableInventory(); }}>Refresh</Button>
          </div>
        </Card>
      </div>

      {show && (
        <TransactionModal visible={show} onClose={()=>setShow(false)} onSaved={async ()=>{ await fetchTransactions(); await fetchAvailableInventory(); const res = await api.get(`/analytics/summary/${activeBusiness.id}`); const s = res.data || { total_income:0, total_expense:0, profit:0 }; setSummary({ income: s.total_income, expense: s.total_expense, profit: s.profit }) }} />
      )}

      {viewingTx && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">Transaction Details</h4>
            <div className="flex flex-col gap-2">
              <div><strong>Type:</strong> {viewingTx.type}</div>
              <div><strong>Amount:</strong> ₹ {Number(viewingTx.amount).toFixed(2)}</div>
              <div><strong>Category:</strong> {viewingTx.category || '-'}</div>
              <div><strong>Invoice:</strong> {viewingTx.invoice_url ? <a className="text-fintech-accent" href={viewingTx.invoice_url}>View</a> : '-'}</div>
              <div><strong>Date:</strong> {new Date(viewingTx.created_at).toLocaleString()}</div>
              <div className="flex justify-end mt-3"><Button variant="ghost" onClick={()=>setViewingTx(null)}>Close</Button></div>
            </div>
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
