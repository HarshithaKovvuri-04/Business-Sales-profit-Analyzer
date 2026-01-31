import React, {useState, useContext} from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { Link } from 'react-router-dom'
import '../auth.css'

function PasswordStrength({value=''}){
  const score = value.length > 8 ? 2 : value.length > 5 ? 1 : 0
  const labels = ['Weak','Medium','Strong']
  const colors = ['text-red-600','text-yellow-500','text-green-600']
  return <div className={colors[score]}>{labels[score]}</div>
}

export default function Register(){
  const { register } = useContext(AuthContext)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [role] = useState('Owner')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const submit = async (e)=>{
    e.preventDefault()
    setError(null)
    if(password !== confirm){
      setError('Passwords do not match')
      return
    }
    setLoading(true)
    try{
      await register({username, password, role})
      setSuccess('Registered successfully. You can login now.')
      setTimeout(()=> navigate('/login'), 1200)
    }catch(err){
      setSuccess(err.response?.data?.detail || 'Registration failed')
    }finally{setLoading(false)}
  }

  return (
    <div className="auth-fullscreen">
      <Card className="auth-card">
        <div className="mb-4">
          <div className="auth-title">Create your account</div>
          <div className="auth-sub">Get started with BizAnalyzer</div>
        </div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <Input label="Username" value={username} onChange={e=>setUsername(e.target.value)} required icon={
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M16 11c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM4 20v-1a4 4 0 014-4h4"/></svg>
          } />

          <Input label="Password" value={password} onChange={e=>setPassword(e.target.value)} required type="password" icon={
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5 9 6.343 9 8s1.343 3 3 3z"/><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M2 20s4-6 10-6 10 6 10 6"/></svg>
          } />

          <Input label="Confirm Password" value={confirm} onChange={e=>setConfirm(e.target.value)} required type="password" icon={
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M5 12h14"/></svg>
          } />

          <div className="flex items-center justify-end">
            <div className="mr-auto text-sm muted" />
            <div className="auth-action">
              <Button type="submit" disabled={loading}>{loading? 'Creating...':'Sign Up'}</Button>
            </div>
          </div>

          {error && <div className="text-sm text-red-600">{error}</div>}
          {success && <div className="text-sm text-green-600">{success}</div>}

          <div className="auth-footer">
            <span>Already have an account? </span><Link to="/login">Sign in</Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
