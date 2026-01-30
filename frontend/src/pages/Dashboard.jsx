import React, {useContext, useEffect, useState} from 'react'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import api from '../api/axios'
import AnalyticsCharts from '../components/AnalyticsCharts'

function Metric({title, value, children}){
  return (
    <Card className="flex flex-col gap-2">
      <div className="text-sm text-slate-500">{title}</div>
      <div className="text-2xl font-semibold">{value}</div>
      {children}
    </Card>
  )
}

function formatINR(v){
  const n = Number(v || 0)
  return `₹ ${n.toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2})}`
}

export default function Dashboard(){
  const { user } = useContext(AuthContext)
  const { businesses, activeBusiness } = useContext(BusinessContext)
  const [summary, setSummary] = useState({income:0, expense:0})
  const [dashboard, setDashboard] = useState(null)
  const [analyticsSummary, setAnalyticsSummary] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [predictionError, setPredictionError] = useState(null)
  const [members, setMembers] = useState([])
  const [weeklyReport, setWeeklyReport] = useState(null)
  const [monthlyReport, setMonthlyReport] = useState(null)
  const [reportsLoading, setReportsLoading] = useState(false)
  const [reportsError, setReportsError] = useState(null)
  const [invoiceFile, setInvoiceFile] = useState(null)
  const [invoiceUrl, setInvoiceUrl] = useState(null)
  const [weekly, setWeekly] = useState([])
  const [monthly, setMonthly] = useState([])
  const [lowStock, setLowStock] = useState([])
  const [lowStockLoading, setLowStockLoading] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)
  const [newMemberUsername, setNewMemberUsername] = useState('')
  const [newMemberRole, setNewMemberRole] = useState('staff')

  useEffect(()=>{
    if(!activeBusiness) return
    let cancelled = false
    // fetch dashboard first to determine user's role for this business
    api.get(`/businesses/${activeBusiness.id}/dashboard`).then(res=>{
      if(cancelled) return
      setDashboard(res.data)
      // fetch authoritative analytics summary for financial cards
      api.get(`/analytics/summary/${activeBusiness.id}`).then(r=>{
        if(!cancelled) setAnalyticsSummary(r.data || { total_income:0, total_expense:0, profit:0 })
      }).catch(()=>{ if(!cancelled) setAnalyticsSummary({ total_income:0, total_expense:0, profit:0 }) })
      // fetch ML prediction only for owners
      setPrediction(null); setPredictionError(null)
      if (res.data?.role === 'owner'){
        api.get(`/ml/predict-profit/${activeBusiness.id}`).then(r=>{
          if(cancelled) return
          setPrediction(r.data)
        }).catch(err=>{
          if(cancelled) return
          // 404 -> model not trained; other errors show generic message
          const status = err?.response?.status
          if(status === 404){
            setPredictionError('Model not trained for this business')
          } else {
            setPredictionError('Failed to load prediction')
          }
        }).finally(()=>{ if(!cancelled) setPredictionLoading(false) })
      } else {
        setPredictionLoading(false)
      }
      // load members only for owners (members API is owner-only)
      if(res.data?.role === 'owner'){
        api.get(`/businesses/${activeBusiness.id}/members`).then(r=> setMembers(r.data)).catch(()=> setMembers([]))
      } else {
        setMembers([])
      }
    }).catch(()=>{})
    // fetch analytics handled by AnalyticsCharts component
    // also fetch low-stock items for alert banner
    const fetchLow = async ()=>{
      try{
        setLowStockLoading(true)
        const r = await api.get('/inventory/low_stock', { params: { business_id: activeBusiness.id } })
        if(!cancelled) setLowStock(r.data || [])
      }catch(err){
        console.error('fetch low stock', err)
        if(!cancelled) setLowStock([])
      }finally{ if(!cancelled) setLowStockLoading(false) }
    }
    fetchLow()
    return ()=>{ cancelled = true }
  }, [activeBusiness])

  // Re-fetch low-stock when other parts of the app notify inventory changed
  useEffect(()=>{
    if(!activeBusiness) return
    const handler = ()=>{
      api.get('/inventory/low_stock', { params: { business_id: activeBusiness.id } }).then(r=> setLowStock(r.data || [])).catch(()=> setLowStock([]))
    }
    window.addEventListener('inventory:updated', handler)
    return ()=> window.removeEventListener('inventory:updated', handler)
  }, [activeBusiness])

  // fetch weekly & monthly report summaries whenever active business changes
  useEffect(()=>{
    if(!activeBusiness) return
    let cancelled = false
    setReportsLoading(true); setReportsError(null)
    // Fetch weekly and monthly reports separately to ensure distinct, time-bound values
    const fetchReports = async ()=>{
      try{
        const [wk, mo] = await Promise.all([
          api.get(`/reports/weekly/${activeBusiness.id}`),
          api.get(`/reports/monthly/${activeBusiness.id}`)
        ])
        if(cancelled) return
        console.debug('Reports fetched', { weekly: wk.data, monthly: mo.data })
        setWeeklyReport({ total_income: wk.data.total_income, total_expense: wk.data.total_expense, net_profit: wk.data.net_profit })
        setMonthlyReport({ total_income: mo.data.total_income, total_expense: mo.data.total_expense, net_profit: mo.data.net_profit })
        setReportsError(null)
      }catch(e){
        if(cancelled) return
        console.error('Report fetch error', e)
        const status = e?.response?.status
        if(status === 404){
          setReportsError(null)
          setWeeklyReport(null); setMonthlyReport(null)
        } else {
          setReportsError(e?.response?.data?.detail || 'Failed to load reports')
          setWeeklyReport(null); setMonthlyReport(null)
        }
      } finally {
        if(!cancelled) setReportsLoading(false)
      }
    }
    fetchReports()
    return ()=>{ cancelled = true }
  }, [activeBusiness])

  // Use analyticsSummary.profit as net profit when available
  const net = analyticsSummary ? analyticsSummary.profit : ((dashboard?.total_income||0) - (dashboard?.total_expense||0))

  return (
    <div>
      {/* Low-stock alert banner: visible when backend reports low-stock items */}
      {lowStock && lowStock.length > 0 && (
        <div className="mb-4 p-3 rounded bg-yellow-50 border border-yellow-200">
          <div className="font-semibold">⚠️ Low Stock Alert: {lowStock.length} item{lowStock.length>1? 's':''} below threshold</div>
          <div className="text-sm text-slate-600 mt-2">
            {lowStock.map(it=> (
              <div key={it.id} className="flex items-center justify-between">
                <div>{(it.category && it.category.trim()) ? it.category + ' – ' + it.item_name : 'Uncategorized – ' + it.item_name}</div>
                <div className="text-sm text-red-600">{it.quantity} left</div>
              </div>
            ))}
          </div>
        </div>
      )}
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {analyticsSummary ? (
        <>
          <Metric title="Total Income" value={formatINR(analyticsSummary.total_income)} />
          <Metric title="Total Expense" value={formatINR(analyticsSummary.total_expense)} />
          {dashboard?.role === 'owner' ? (
            <Metric title="Net Profit" value={formatINR(analyticsSummary.profit)}>
              <div className={`inline-block px-2 py-1 rounded text-sm ${analyticsSummary.profit>=0? 'bg-green-100 text-green-700':'bg-red-100 text-red-700'}`}>{analyticsSummary.profit>=0? 'Profit':'Loss'}</div>
            </Metric>
          ) : null }
          {/* Predicted profit card */}
          <Metric title="Predicted Profit (Next Month)" value={prediction ? formatINR(prediction.predicted_profit) : (predictionError ? '-' : 'Loading...')}>
            <div className="text-sm text-slate-500">
              {prediction ? prediction.predicted_month : (predictionError ? predictionError : 'ML-based estimate')}
            </div>
            {predictionError ? <div className="text-sm text-red-600">{predictionError}</div> : null}
          </Metric>
        </>
      ) : (
        // fallback to dashboard totals if analytics summary not yet loaded
        <>
          {dashboard?.total_income !== undefined && (<Metric title="Total Income" value={formatINR(dashboard.total_income)} />)}
          {dashboard?.total_expense !== undefined && (<Metric title="Total Expense" value={formatINR(dashboard.total_expense)} />)}
          {dashboard?.net_profit !== undefined && dashboard?.role === 'owner' && (
            <Metric title="Net Profit" value={formatINR(dashboard.net_profit)}>
              <div className={`inline-block px-2 py-1 rounded text-sm ${net>=0? 'bg-green-100 text-green-700':'bg-red-100 text-red-700'}`}>{net>=0? 'Profit':'Loss'}</div>
            </Metric>
          )}
        </>
      )}

      <Card className="md:col-span-2">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-slate-500">Active Businesses</div>
            <div className="text-xl font-semibold">{businesses.length}</div>
          </div>
          <div>
            <div className="text-sm text-slate-500">Your role</div>
            <div className="text-xl font-semibold">{user?.role}</div>
          </div>
        </div>
      </Card>

      {/* Owner-only: Manage Members */}
      {dashboard?.role === 'owner' && (
        <Card className="md:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-lg font-semibold">Manage Members</div>
            <button className="text-sm text-blue-600" onClick={()=>setShowAddMember(true)}>Add member</button>
          </div>
          <div className="space-y-2">
            {members.map(m=> (
              <div key={m.id} className="flex items-center justify-between">
                <div>{m.username || m.user_id} — {m.role}</div>
                <div>
                  <button className="text-red-600" onClick={async ()=>{
                    await api.delete(`/businesses/${activeBusiness.id}/members/${m.user_id}`)
                    setMembers(ms=>ms.filter(x=>x.id!==m.id))
                  }}>Remove</button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Invoice upload (owner or accountant) */}
      {(dashboard?.role === 'owner' || dashboard?.role === 'accountant') && (
        <Card className="md:col-span-3">
          <div className="flex items-center justify-between mb-2">
            <div className="text-lg font-semibold">Upload Invoice</div>
          </div>
          <form onSubmit={async e=>{
            e.preventDefault()
            if(!invoiceFile) return alert('Select a file')
            const fd = new FormData()
            fd.append('business_id', activeBusiness.id)
            fd.append('file', invoiceFile)
            try{
              const res = await api.post('/transactions/upload', fd, {headers: {'Content-Type': 'multipart/form-data'}})
              setInvoiceUrl(res.data.invoice_url)
              alert('Uploaded')
            }catch(err){
              alert(err?.response?.data?.detail || 'Upload failed')
            }
          }} className="flex items-center gap-2">
            <input type="file" accept="application/pdf,image/*" onChange={e=>setInvoiceFile(e.target.files[0])} />
            <Button type="submit">Upload</Button>
            {invoiceUrl && <a className="text-sm text-blue-600" href={invoiceUrl}>View invoice</a>}
          </form>
        </Card>
      )}

      {/* Reports: Weekly & Monthly (above charts) */}
      <Card className="md:col-span-3">
        <div className="mb-3">
          <div className="text-lg font-semibold">Financial Reports</div>
          <div className="text-sm text-slate-500">Summary of income and expenses</div>
        </div>

        {reportsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-4 bg-slate-100 rounded">Loading...</div>
            <div className="p-4 bg-slate-100 rounded">Loading...</div>
            <div className="p-4 bg-slate-100 rounded">Loading...</div>
          </div>
        ) : reportsError ? (
          <div className="text-sm text-red-600">{reportsError}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Weekly */}
            <div>
              <div className="text-sm text-slate-500 mb-2">Weekly Report</div>
              {weeklyReport && ((weeklyReport.total_income || 0) !== 0 || (weeklyReport.total_expense || 0) !== 0) ? (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Metric title="Total Income" value={formatINR(weeklyReport.total_income)} />
                  <Metric title="Total Expense" value={formatINR(weeklyReport.total_expense)} />
                  {dashboard?.role === 'owner' ? (
                    <Metric title="Net Profit" value={formatINR(weeklyReport.net_profit ?? (weeklyReport.total_income - weeklyReport.total_expense))} />
                  ) : null}
                </div>
              ) : (
                <div className="text-sm text-slate-500">No data available</div>
              )}
            </div>

            {/* Monthly */}
            <div>
              <div className="text-sm text-slate-500 mb-2">Monthly Report</div>
              {monthlyReport && ((monthlyReport.total_income || 0) !== 0 || (monthlyReport.total_expense || 0) !== 0) ? (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <Metric title="Total Income" value={formatINR(monthlyReport.total_income)} />
                  <Metric title="Total Expense" value={formatINR(monthlyReport.total_expense)} />
                  {dashboard?.role === 'owner' ? (
                    <Metric title="Net Profit" value={formatINR(monthlyReport.net_profit ?? (monthlyReport.total_income - monthlyReport.total_expense))} />
                  ) : null}
                </div>
              ) : (
                <div className="text-sm text-slate-500">No data available</div>
              )}
            </div>
          </div>
        )}
      </Card>

      {/* Analytics charts */}
      <Card className="md:col-span-3">
        <div className="text-lg font-semibold mb-2">Insights</div>
        <AnalyticsCharts businessId={activeBusiness?.id} role={dashboard?.role} api={api} />
      </Card>

      {showAddMember && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">Add Member</h4>
            <form onSubmit={async e=>{
              e.preventDefault()
              try{
                const res = await api.post(`/businesses/${activeBusiness.id}/members`, {username:newMemberUsername, role:newMemberRole})
                setMembers(ms=>[...ms, res.data])
                setShowAddMember(false); setNewMemberUsername('')
              }catch(err){ alert(err?.response?.data?.detail || 'Failed') }
            }} className="flex flex-col gap-2">
              <Input label="Username" value={newMemberUsername} onChange={e=>setNewMemberUsername(e.target.value)} required />
              <label className="text-sm">Role</label>
              <select value={newMemberRole} onChange={e=>setNewMemberRole(e.target.value)} className="border rounded p-2">
                <option value="staff">Staff</option>
                <option value="accountant">Accountant</option>
              </select>
              <div className="flex gap-2 justify-end">
                <Button type="submit">Add</Button>
                <Button variant="ghost" onClick={()=>setShowAddMember(false)}>Cancel</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
    </div>
  )
}
