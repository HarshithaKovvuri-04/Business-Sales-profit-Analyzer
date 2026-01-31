import React, {useContext, useEffect, useState} from 'react'
import api from '../api/axios'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'

export default function AccountantDashboard(){
  const { user } = useContext(AuthContext)
  const { activeBusiness } = useContext(BusinessContext)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(()=>{
    if(!user || user.role !== 'accountant' || !activeBusiness) return
    api.get(`/accountant/financials/overview?business_id=${activeBusiness.id}`).then(res=> setData(res.data)).catch(err=> setError(err.response?.data || {detail:'Error'}))
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
            <div className="text-3xl font-semibold mt-2">${data.net_profit.toFixed(2)}</div>
          </Card>

          <Card>
            <h3 className="font-medium text-slate-500">Monthly Summary</h3>
            <div className="mt-2">Income: ${data.monthly_summary.total_income?.toFixed(2) || '0.00'}</div>
            <div>Expense: ${data.monthly_summary.total_expense?.toFixed(2) || '0.00'}</div>
          </Card>

          <Card className="md:col-span-2">
            <h3 className="font-medium text-slate-500">Expense Breakdown</h3>
            <ul className="mt-2 space-y-2">
              {data.expense_breakdown.map((c,i)=> (<li key={i} className="flex justify-between"><span>{c.category}</span><span className="font-medium">${c.amount.toFixed(2)}</span></li>))}
            </ul>
          </Card>

          <Card className="md:col-span-2">
            <h3 className="font-medium text-slate-500">P&L (Monthly)</h3>
            <div className="overflow-auto mt-2">
              <table className="w-full text-left border-separate" style={{borderSpacing:'0 8px'}}>
                <thead><tr className="text-slate-500"><th className="p-2">Month</th><th className="p-2">Income</th><th className="p-2">Expense</th></tr></thead>
                <tbody>
                  {data.pl_monthly.map((m,idx)=> (
                    <tr key={idx} className="bg-card rounded-lg shadow-elevated"><td className="p-3">{m.month}</td><td className="p-3">${m.income.toFixed(2)}</td><td className="p-3">${m.expense.toFixed(2)}</td></tr>
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
