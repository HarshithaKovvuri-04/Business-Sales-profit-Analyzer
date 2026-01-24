import React, {useState, useContext, useEffect} from 'react'
import { BusinessContext } from '../contexts/BusinessContext'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import api from '../api/axios'

export default function Inventory(){
  const { activeBusiness } = useContext(BusinessContext)
  const [items, setItems] = useState([])
  const [show, setShow] = useState(false)
  const [itemName, setItemName] = useState('')
  const [quantity, setQuantity] = useState(0)
  const [costPrice, setCostPrice] = useState(0)

  useEffect(()=>{
    if(activeBusiness) api.get(`/inventory?business_id=${activeBusiness.id}`).then(res=> setItems(res.data)).catch(()=>{})
  }, [activeBusiness])

  const save = async (e)=>{
    e.preventDefault()
    if(!activeBusiness) return alert('Select a business')
    await api.post('/inventory', {business_id: activeBusiness.id, item_name: itemName, quantity: parseInt(quantity), cost_price: parseFloat(costPrice)})
    setShow(false); setItemName(''); setQuantity(0); setCostPrice(0)
    const res = await api.get(`/inventory?business_id=${activeBusiness.id}`)
    setItems(res.data)
  }

  return (
    <div className="grid grid-cols-1 gap-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Inventory</h3>
        <Button onClick={()=>setShow(true)}>Add Item</Button>
      </div>
      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500"><th>Item</th><th>Quantity</th><th>Cost Price</th></tr>
          </thead>
          <tbody>
            {items.map(it=> (
              <tr key={it.id} className="border-t"><td>{it.item_name}</td><td>{it.quantity}</td><td>₹ {it.cost_price.toFixed(2)}</td></tr>
            ))}
          </tbody>
        </table>
      </Card>

      {show && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/30">
          <Card className="w-full max-w-md">
            <h4 className="text-lg font-semibold mb-3">Add Inventory Item</h4>
            <form onSubmit={save} className="flex flex-col gap-2">
              <input placeholder="Item name" value={itemName} onChange={e=>setItemName(e.target.value)} className="px-3 py-2 rounded border" required />
              <input placeholder="Quantity" type="number" value={quantity} onChange={e=>setQuantity(e.target.value)} className="px-3 py-2 rounded border" required />
              <input placeholder="Cost price" type="number" step="0.01" value={costPrice} onChange={e=>setCostPrice(e.target.value)} className="px-3 py-2 rounded border" required />
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
