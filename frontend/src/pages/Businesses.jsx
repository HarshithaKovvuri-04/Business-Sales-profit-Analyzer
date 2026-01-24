import React, {useContext, useState} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import api from '../api/axios'

export default function Businesses(){
  const { businesses, refresh } = useContext(BusinessContext)
  const [show, setShow] = useState(false)
  const [name, setName] = useState('')
  const [industry, setIndustry] = useState('')

  const create = async (e)=>{
    e.preventDefault()
    await api.post('/businesses', {name, industry})
    setShow(false); setName(''); setIndustry(''); refresh()
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="md:col-span-2">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Your Businesses</h3>
          <Button onClick={()=>setShow(true)}>Add Business</Button>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {businesses.map(b=> (
            <Card key={b.id}>
              <div className="font-semibold">{b.name}</div>
              <div className="text-sm text-slate-500">{b.industry}</div>
              <div className="text-xs text-slate-400">{new Date(b.created_at).toLocaleDateString()}</div>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <Card>
          <div className="mb-2">Quick Actions</div>
          <Button className="mb-2">Add Transaction</Button>
          <Button variant="ghost">View Finance</Button>
        </Card>
      </div>

      {show && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">Create Business</h4>
            <form onSubmit={create} className="flex flex-col gap-2">
              <Input label="Business name" value={name} onChange={e=>setName(e.target.value)} required />
              <Input label="Industry" value={industry} onChange={e=>setIndustry(e.target.value)} required />
              <div className="flex gap-2 justify-end">
                <Button type="submit">Save</Button>
                <Button variant="ghost" onClick={()=>setShow(false)}>Cancel</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
