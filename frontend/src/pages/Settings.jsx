import React, {useContext, useState} from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import api from '../api/axios'
import { AuthContext } from '../contexts/AuthContext'

export default function Settings(){
  const { user, logout } = useContext(AuthContext)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const submit = async (e)=>{
    e.preventDefault()
    setMessage(null); setError(null)
    if(newPassword !== confirmPassword){
      setError('New password and confirm do not match')
      return
    }
    setLoading(true)
    try{
      const res = await api.put('/users/me/password', { current_password: currentPassword, new_password: newPassword })
      setMessage(res.data.message || 'Password updated')
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('')
    }catch(err){
      setError(err?.response?.data?.detail || err.message || 'Failed to change password')
    }finally{ setLoading(false) }
  }

  return (
    <div className="max-w-lg">
      <Card>
        <h3 className="text-lg font-semibold mb-2">Account Details</h3>
        <div className="mb-2"><strong>Username:</strong> {user?.username}</div>
        <div className="mb-2"><strong>Role:</strong> {user?.role}</div>
        <div className="mb-4 text-sm text-slate-500"><strong>Created:</strong> {user?.created_at ? new Date(user.created_at).toLocaleString() : '-'}</div>
        <hr className="my-4" />
        <h4 className="text-lg font-semibold mb-2">Change Password</h4>
        {message && <div className="mb-2 text-green-700">{message}</div>}
        {error && <div className="mb-2 text-red-700">{error}</div>}
        <form onSubmit={submit} className="flex flex-col gap-2">
          <input type="password" placeholder="Current password" value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)} className="px-3 py-2 rounded border" required />
          <input type="password" placeholder="New password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} className="px-3 py-2 rounded border" required />
          <input type="password" placeholder="Confirm new password" value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)} className="px-3 py-2 rounded border" required />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={logout}>Logout</Button>
            <Button type="submit" disabled={loading}>{loading? 'Saving...':'Change Password'}</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
