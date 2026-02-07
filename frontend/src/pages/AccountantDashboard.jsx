import React, {useContext, useEffect, useState} from 'react'
import api from '../api/axios'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'
import Card from '../components/ui/Card'

export default function AccountantDashboard(){
  const { user } = useContext(AuthContext)
  const { activeBusiness } = useContext(BusinessContext)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const formatCurrency = (v)=>{
    if (v === null || v === undefined) return '-'
    return `$${Number(v).toFixed(2)}`
  }

  useEffect(()=>{
    if(!user || user.role !== 'accountant' || !activeBusiness) return

    const fetchOverview = async ()=>{
      try{
        // Accountant-specific overview: use accountant-only endpoint which
        // applies the same expense logic as the owner but exposes accountant view data.
        const res = await api.get(`/accountant/financials/overview`, { params: { business_id: activeBusiness.id } })
        const d = res.data || {}
        // Normalize expense breakdown shape to ensure category and amount fields
        const normalizedCategories = (d.expense_breakdown || []).map(c => ({ category: (c && (c.category || 'Uncategorized')), amount: Number((c && c.amount) || 0) }))
        const assembled = {
          net_profit: d.net_profit,
          monthly_summary: d.monthly_summary || { total_income: 0.0, total_expense: 0.0 },
          expense_breakdown: normalizedCategories,
          pl_monthly: d.pl_monthly || [],
          summary_totals: d.summary_totals || { income: 0.0, expense: 0.0 }
        }
        setData(assembled)
        setError(null)
      }catch(err){
        setError(err.response?.data || {detail:'Error'})
      }
    }

    fetchOverview()

    const handler = ()=>{ fetchOverview() }
    // Listen for inventory/transaction changes to refresh dashboard data
    window.addEventListener('inventory:updated', handler)
    window.addEventListener('transactions:updated', handler)
    window.addEventListener('transaction:created', handler)
    window.addEventListener('transaction:updated', handler)
    window.addEventListener('transaction:deleted', handler)

    return ()=>{
      window.removeEventListener('inventory:updated', handler)
      window.removeEventListener('transactions:updated', handler)
      window.removeEventListener('transaction:created', handler)
      window.removeEventListener('transaction:updated', handler)
      window.removeEventListener('transaction:deleted', handler)
    }
  }, [user, activeBusiness])

  if(!user || user.role !== 'accountant') return <div>Access denied</div>
  if(!activeBusiness) return <div>Please select a business.</div>

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Financial Dashboard</h1>
      {error && <div className="text-red-600">{error.detail || 'Failed to load'}</div>}
      {!data && !error && <div>Loading...</div>}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <h3 className="font-medium text-slate-500">Net Profit</h3>
            <div className="text-3xl font-semibold mt-2">{formatCurrency(data.net_profit)}</div>
          </Card>

          <Card>
            <h3 className="font-medium text-slate-500">Monthly Summary</h3>
            <div className="mt-2">Income: {formatCurrency(data.monthly_summary?.total_income)}</div>
            <div>Expense: {formatCurrency(data.monthly_summary?.total_expense)}</div>
          </Card>

          <Card className="md:col-span-2">
            <h3 className="font-medium text-slate-500">Expense Breakdown</h3>
            <ul className="mt-2 space-y-2">
              {data.expense_breakdown.map((c,i)=> (<li key={i} className="flex justify-between"><span>{c.category}</span><span className="font-medium">{formatCurrency(c.amount)}</span></li>))}
            </ul>
          </Card>

          <Card className="md:col-span-2">
            <h3 className="font-medium text-slate-500">P&L (Monthly)</h3>
            <div className="overflow-auto mt-2">
              <table className="w-full text-left border-separate" style={{borderSpacing:'0 8px'}}>
                <thead><tr className="text-slate-500"><th className="p-2">Month</th><th className="p-2">Income</th><th className="p-2">Expense</th></tr></thead>
                <tbody>
                  {data.pl_monthly.map((m,idx)=> (
                    <tr key={idx} className="bg-card rounded-lg shadow-elevated"><td className="p-3">{m.month}</td><td className="p-3">{formatCurrency(m.income)}</td><td className="p-3">{formatCurrency(m.expense)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
