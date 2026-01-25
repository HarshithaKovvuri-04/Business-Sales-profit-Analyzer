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
    // Do not fetch analytics at all for staff users
    if (role === 'staff'){
      setWeekly(null)
      setMonthly(null)
      setCategories(null)
      setProfit(null)
      setLoading(false)
      return
    }
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

  // Re-fetch only the analytics dataset when toggling view
  const handleToggle = (newView) => {
    if(!businessId) return
    if(newView === view) return
    setLoading(true)
    setView(newView)
    const endpoint = `/analytics/${newView}/${businessId}`
    api.get(endpoint).then(r => r.data).then(data => {
      if(newView === 'weekly') setWeekly(data)
      else setMonthly(data)
    }).catch(()=>{
      // keep previous data on error
    }).finally(()=>setLoading(false))
  }

  if(loading) return <div className="text-sm text-slate-500">Loading charts...</div>

  // Staff users should not see or fetch charts
  if (role === 'staff') return <div className="text-sm text-slate-500">Charts are not available for staff users.</div>

  // normalize backend response which may be either:
  // - array of {label,date,income,expense}
  // - object { labels: [], income: [], expense: [] }
  const extractChartData = (dataset) => {
    if (!dataset) return { labels: [], income: [], expense: [] }
    if (Array.isArray(dataset)) {
      const labels = dataset.map(d => (d && (d.label || d.date)) || '')
      const income = dataset.map(d => Number((d && d.income) || 0))
      const expense = dataset.map(d => Number((d && d.expense) || 0))
      return { labels, income, expense }
    }
    if (dataset && Array.isArray(dataset.labels)) {
      const labels = dataset.labels.map(l => l || '')
      const income = (dataset.income || []).map(x => Number(x || 0))
      const expense = (dataset.expense || []).map(x => Number(x || 0))
      const maxlen = Math.max(labels.length, income.length, expense.length)
      while (labels.length < maxlen) labels.push('')
      while (income.length < maxlen) income.push(0)
      while (expense.length < maxlen) expense.push(0)
      return { labels, income, expense }
    }
    return { labels: [], income: [], expense: [] }
  }

  const weeklyData = extractChartData(weekly)
  const monthlyData = extractChartData(monthly)

  const weeklyLabels = weeklyData.labels
  const weeklyIncome = weeklyData.income
  const weeklyExpense = weeklyData.expense

  const monthlyLabels = monthlyData.labels
  const monthlyIncome = monthlyData.income
  const monthlyExpense = monthlyData.expense

  // Use category names only; fall back to 'Uncategorized' for null/empty
  const categoryLabels = (categories||[]).map(c => (c && (c.category || 'Uncategorized')))
  const categoryData = (categories||[]).map(c => Number((c && c.amount) || 0))

  const profitLabels = (profit||[]).map(p=> p.month)
  const profitData = (profit||[]).map(p=> p.profit)

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', display: true },
      tooltip: { enabled: true }
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-md font-semibold">Income vs Expense</h4>
          <div className="inline-flex rounded-md shadow-sm" role="tablist">
            <button onClick={()=>handleToggle('weekly')} disabled={loading} className={`px-3 py-1 border ${view==='weekly' ? 'bg-white border-slate-300' : 'bg-slate-100'} ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}>
              Weekly
            </button>
            <button onClick={()=>handleToggle('monthly')} disabled={loading} className={`px-3 py-1 border ${view==='monthly' ? 'bg-white border-slate-300' : 'bg-slate-100'} ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}>
              Monthly
            </button>
          </div>
        </div>

        {view === 'weekly' ? (
          // show chart only when there are labels and at least one non-zero value
          (weeklyLabels && weeklyLabels.length && (weeklyIncome.some(v=>v!==0) || weeklyExpense.some(v=>v!==0))) ? (
            <div style={{height:320}}>
              <Bar
                options={{
                  ...commonOptions,
                  scales: {
                    x: { title: { display: true, text: 'Date' }, stacked: false },
                    y: { title: { display: true, text: 'Amount' }, beginAtZero: true }
                  }
                }}
                data={{
                  labels: weeklyLabels,
                  datasets: [
                    { label: 'Income', data: weeklyIncome, backgroundColor: '#16A34A' },
                    { label: 'Expense', data: weeklyExpense, backgroundColor: '#DC2626' }
                  ]
                }}
              />
            </div>
          ) : <div className="text-sm text-slate-500">No data available for Weekly.</div>
        ) : (
          (monthlyLabels && monthlyLabels.length && (monthlyIncome.some(v=>v!==0) || monthlyExpense.some(v=>v!==0))) ? (
            <div style={{height:320}}>
              <Bar
                options={{
                  ...commonOptions,
                  scales: {
                    x: { title: { display: true, text: 'Month' }, stacked: false },
                    y: { title: { display: true, text: 'Amount' }, beginAtZero: true }
                  }
                }}
                data={{
                  labels: monthlyLabels,
                  datasets: [
                    { label: 'Income', data: monthlyIncome, backgroundColor: '#16A34A' },
                    { label: 'Expense', data: monthlyExpense, backgroundColor: '#DC2626' }
                  ]
                }}
              />
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
