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
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-white rounded shadow">
            <h3 className="font-medium">Net Profit</h3>
            <div className="text-3xl">${data.net_profit.toFixed(2)}</div>
          </div>
          <div className="p-4 bg-white rounded shadow">
            <h3 className="font-medium">Monthly Summary</h3>
            <div>Income: ${data.monthly_summary.total_income?.toFixed(2) || '0.00'}</div>
            <div>Expense: ${data.monthly_summary.total_expense?.toFixed(2) || '0.00'}</div>
          </div>

          <div className="p-4 bg-white rounded shadow col-span-2">
            <h3 className="font-medium">Expense Breakdown</h3>
            <ul>
              {data.expense_breakdown.map((c,i)=> (<li key={i}>{c.category}: ${c.amount.toFixed(2)}</li>))}
            </ul>
          </div>

          <div className="p-4 bg-white rounded shadow col-span-2">
            <h3 className="font-medium">P&L (Monthly)</h3>
            <div className="overflow-auto">
              <table className="w-full text-left">
                <thead><tr><th>Month</th><th>Income</th><th>Expense</th></tr></thead>
                <tbody>
                  {data.pl_monthly.map((m,idx)=> (
                    <tr key={idx}><td>{m.month}</td><td>${m.income.toFixed(2)}</td><td>${m.expense.toFixed(2)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
