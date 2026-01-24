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
  const [summary, setSummary] = useState({income:0, expense:0})
  const [invoiceFile, setInvoiceFile] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loadingTx, setLoadingTx] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editingTx, setEditingTx] = useState(null)
  const [editInvoiceFile, setEditInvoiceFile] = useState(null)
  const [updating, setUpdating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const { user } = useContext(AuthContext)
  

  useEffect(()=>{
    if(activeBusiness){
      api.get(`/summary/${activeBusiness.id}`).then(res=> setSummary(res.data)).catch(()=>{})
      fetchTransactions()
    } else {
      setTransactions([])
    }
  }, [activeBusiness])

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

      await api.post('/transactions', {business_id: activeBusiness.id, type, amount: parseFloat(amount), category, invoice_url})
      await fetchTransactions()
    }catch(err){
      console.error(err)
      alert(err?.response?.data?.detail || err.message || 'Failed to save transaction')
      setSaving(false)
      return
    }finally{ setSaving(false) }
    setShow(false); setAmount(''); setCategory('')
    setInvoiceFile(null)
    // refresh summary
    const res = await api.get(`/summary/${activeBusiness.id}`)
    setSummary(res.data)
  }

  const openEdit = (tx)=>{
    setEditingTx({...tx})
    setEditInvoiceFile(null)
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
      await api.put(`/transactions/${editingTx.id}`, { type: editingTx.type, amount: parseFloat(editingTx.amount), category: editingTx.category, invoice_url })
      await fetchTransactions()
      setEditingTx(null)
    }catch(err){
      console.error(err)
      alert(err?.response?.data?.detail || err.message || 'Failed to update transaction')
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
              <input placeholder="Amount (₹)" type="number" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)} className="px-3 py-2 rounded border" required />
              <input placeholder="Category" value={category} onChange={e=>setCategory(e.target.value)} className="px-3 py-2 rounded border" required />
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
              <input placeholder="Amount (₹)" type="number" step="0.01" value={editingTx.amount} onChange={e=>setEditingTx(et=>({...et, amount: e.target.value}))} className="px-3 py-2 rounded border" required />
              <input placeholder="Category" value={editingTx.category || ''} onChange={e=>setEditingTx(et=>({...et, category: e.target.value}))} className="px-3 py-2 rounded border" />
              <div>
                <label className="text-sm">Invoice (replace)</label>
                <input type="file" onChange={e=>setEditInvoiceFile(e.target.files[0])} className="px-3 py-2 rounded border" />
                {editingTx.invoice_url && <div className="text-sm mt-1">Current: <a className="text-blue-600" href={editingTx.invoice_url}>{editingTx.invoice_url}</a></div>}
              </div>
              <div className="flex gap-2 justify-end">
                <Button type="submit" disabled={updating}>{updating? 'Saving...':'Save'}</Button>
                <Button variant="ghost" onClick={()=>setEditingTx(null)}>Cancel</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
