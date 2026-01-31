import React, {useState, useContext} from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { Link } from 'react-router-dom'
import '../auth.css'

export default function Login(){
  const { login } = useContext(AuthContext)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [show, setShow] = useState(false)
  const navigate = useNavigate()

  const submit = async (e)=>{
    e.preventDefault()
    setLoading(true); setError(null)
    try{
      await login({username, password})
      navigate('/dashboard')
    }catch(err){
      setError(err.response?.data?.detail || 'Login failed')
    }finally{setLoading(false)}
  }

  return (
    <div className="auth-fullscreen">
      <Card className="auth-card">
        <div className="mb-4">
          <div className="auth-title">Welcome back!</div>
          <div className="auth-sub">Sign in to your account</div>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <Input label="Username" value={username} onChange={e=>setUsername(e.target.value)} required icon={
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16 11c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM4 20v-1a4 4 0 014-4h4"/></svg>
          } />

          <div>
            <label className="flex flex-col text-sm gap-1">
              <span className="text-slate-600">Password</span>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5 9 6.343 9 8s1.343 3 3 3z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M2 20s4-6 10-6 10 6 10 6"/></svg>
                </div>
                <input className="pl-10 pr-20 py-2 rounded-lg border border-slate-200 bg-transparent w-full focus:outline-none focus:ring-2 focus:ring-fintech-accent/30" type={show? 'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} required />
                <button type="button" onClick={()=>setShow(s=>!s)} className="absolute inset-y-0 right-0 mr-2 px-3 rounded-md bg-slate-100 text-sm flex items-center">{show? 'Hide':'Show'}</button>
              </div>
            </label>
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <div className="flex items-center justify-between">
            <Link to="/forgot" className="forgot-link">Forgot password?</Link>
            <div className="auth-action">
              <Button type="submit" disabled={loading} className="rounded-full bg-gradient-to-br from-indigo-500 to-indigo-400 hover:from-indigo-600 hover:to-indigo-500 text-white px-6 py-2">{loading? 'Signing...':'Sign In'}</Button>
            </div>
          </div>

          <div className="auth-footer">
            <span>Don't have an account? </span><Link to="/register">Sign up</Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
