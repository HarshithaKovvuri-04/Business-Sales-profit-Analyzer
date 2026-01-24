import React, {useState, useContext} from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import { Link } from 'react-router-dom'

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
  const [role, setRole] = useState('Owner')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const navigate = useNavigate()

  const submit = async (e)=>{
    e.preventDefault()
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
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <h2 className="text-2xl font-semibold mb-4">Create an account</h2>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <Input label="Username" value={username} onChange={e=>setUsername(e.target.value)} required />
          <Input label="Password" value={password} onChange={e=>setPassword(e.target.value)} type="password" required />
          <div className="flex items-center gap-2">
            <label className="text-sm">Role</label>
            <select value={role} onChange={e=>setRole(e.target.value)} className="px-3 py-2 rounded-md bg-transparent border">
              <option>Owner</option>
              <option>Accountant</option>
              <option>Staff</option>
            </select>
          </div>
          <PasswordStrength value={password} />
          {success && <div className="text-sm text-green-600">{success}</div>}
          <div className="flex justify-end">
            <Button type="submit" disabled={loading}>{loading? 'Creating...':'Register'}</Button>
          </div>
          <div className="mt-3 text-sm">
            <span>Already have an account? </span><Link to="/login" className="text-indigo-600">Login</Link>
          </div>
        </form>
      </Card>
    </div>
  )
}
