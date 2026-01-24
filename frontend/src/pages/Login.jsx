import React, {useState, useContext} from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { Link } from 'react-router-dom'

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
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <h2 className="text-2xl font-semibold mb-4">Sign in to BizAnalyzer AI</h2>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <Input label="Username" value={username} onChange={e=>setUsername(e.target.value)} required />
          <div>
            <label className="flex flex-col text-sm gap-1">
              <span className="text-slate-600">Password</span>
              <div className="flex gap-2">
                <input className="px-3 py-2 rounded-md border border-slate-200 flex-1" type={show? 'text':'password'} value={password} onChange={e=>setPassword(e.target.value)} required />
                <button type="button" onClick={()=>setShow(s=>!s)} className="px-3 rounded-md bg-slate-100">{show? 'Hide':'Show'}</button>
              </div>
            </label>
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}

          <div className="flex justify-end">
            <Button type="submit" disabled={loading}>{loading? 'Signing...':'Sign In'}</Button>
          </div>
          <div className="mt-3 text-sm">
            <span>Don't have an account? </span><Link to="/register" className="text-indigo-600">Register</Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
