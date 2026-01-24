import React, { useEffect, useState } from 'react'
import 'chart.js/auto'
import { Bar, Line, Pie } from 'react-chartjs-2'

export default function AnalyticsCharts({ businessId, role, api }){
  const [weekly, setWeekly] = useState(null)
  const [monthly, setMonthly] = useState(null)
  const [categories, setCategories] = useState(null)
  const [profit, setProfit] = useState(null)
  const [loading, setLoading] = useState(false)
        const [view, setView] = useState('weekly')

  useEffect(()=>{
    if(!businessId) return
    setLoading(true)
    Promise.all([
      api.get(`/analytics/weekly/${businessId}`).then(r=>r.data).catch(()=>[]),
      api.get(`/analytics/monthly/${businessId}`).then(r=>r.data).catch(()=>[]),
      api.get(`/analytics/categories/${businessId}`).then(r=>r.data).catch(()=>[]),
      (role === 'owner' ? api.get(`/analytics/profit/${businessId}`).then(r=>r.data).catch(()=>null) : Promise.resolve(null))
    ]).then(([w,m,c,p])=>{
      setWeekly(w)
      setMonthly(m)
      setCategories(c)
      setProfit(p)
    }).finally(()=>setLoading(false))
  }, [businessId, role])

  if(loading) return <div className="text-sm text-slate-500">Loading charts...</div>

  const weeklyLabels = (weekly||[]).map(d=> d.label)
  const weeklyIncome = (weekly||[]).map(d=> d.income)
  const weeklyExpense = (weekly||[]).map(d=> d.expense)

  const monthlyLabels = (monthly||[]).map(d=> d.label)
  const monthlyIncome = (monthly||[]).map(d=> d.income)
  const monthlyExpense = (monthly||[]).map(d=> d.expense)

  const categoryLabels = (categories||[]).map(c=> c.category)
  const categoryData = (categories||[]).map(c=> c.amount)

  const profitLabels = (profit||[]).map(p=> p.month)
  const profitData = (profit||[]).map(p=> p.profit)

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      tooltip: { enabled: true }
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-md font-semibold">Income vs Expense</h4>
          <div className="inline-flex rounded-md shadow-sm" role="tablist">
            <button onClick={()=>setView('weekly')} className={`px-3 py-1 border ${view==='weekly' ? 'bg-white border-slate-300' : 'bg-slate-100'}`}>Weekly</button>
            <button onClick={()=>setView('monthly')} className={`px-3 py-1 border ${view==='monthly' ? 'bg-white border-slate-300' : 'bg-slate-100'}`}>Monthly</button>
          </div>
        </div>

        {view === 'weekly' ? (
          (weekly && weekly.length) ? (
            <div style={{height:300}}>
              <Bar options={commonOptions} data={{labels: weeklyLabels, datasets: [ {label:'Income', data: weeklyIncome, backgroundColor:'#10B981'}, {label:'Expense', data: weeklyExpense, backgroundColor:'#EF4444'} ] }} />
            </div>
          ) : <div className="text-sm text-slate-500">No data available for Weekly.</div>
        ) : (
          (monthly && monthly.length) ? (
            <div style={{height:300}}>
              <Bar options={commonOptions} data={{labels: monthlyLabels, datasets: [ {label:'Income', data: monthlyIncome, backgroundColor:'#2563EB'}, {label:'Expense', data: monthlyExpense, backgroundColor:'#F97316'} ] }} />
            </div>
          ) : <div className="text-sm text-slate-500">No data available for Monthly.</div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="text-md font-semibold mb-2">Category-wise Expenses</h4>
          {(categories && categories.length) ? (
            <div style={{height:300}}>
              <Pie options={commonOptions} data={{labels: categoryLabels, datasets:[{data: categoryData, backgroundColor: ['#60A5FA','#F97316','#F87171','#34D399','#A78BFA','#FBBF24']} ]}} />
            </div>
          ) : <div className="text-sm text-slate-500">No category expense data available.</div>}
        </div>

              {role === 'owner' ? (
                <div>
                  <h4 className="text-md font-semibold mb-2">Profit Trend (Owner only)</h4>
                  {(profit && profit.length) ? (
                    <div style={{height:300}}>
                      <Line options={commonOptions} data={{labels: profitLabels, datasets:[{label:'Profit', data: profitData, borderColor:'#0EA5A9', fill:false}]}} />
                    </div>
                  ) : <div className="text-sm text-slate-500">No profit data available.</div>}
                </div>
              ) : null}
      </div>
    </div>
  )
}
