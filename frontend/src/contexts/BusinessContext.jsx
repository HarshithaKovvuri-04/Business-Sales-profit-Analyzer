import React, {createContext, useEffect, useState, useContext} from 'react'
import api from '../api/axios'
import { AuthContext } from './AuthContext'

export const BusinessContext = createContext(null)

export function BusinessProvider({children}){
  const { user } = useContext(AuthContext)
  const [businesses, setBusinesses] = useState([])
  const [activeBusiness, setActiveBusiness] = useState(null)

  useEffect(()=>{
    if(user){
      api.get('/businesses').then(res=>{
        setBusinesses(res.data || [])
        if(res.data && res.data.length) setActiveBusiness(res.data[0])
      }).catch(()=>setBusinesses([]))
    } else {
      setBusinesses([]); setActiveBusiness(null)
    }
  }, [user])

  const refresh = ()=>{
    if(user) api.get('/businesses').then(res=> setBusinesses(res.data || []))
  }

  return (
    <BusinessContext.Provider value={{businesses, activeBusiness, setActiveBusiness, refresh}}>
      {children}
    </BusinessContext.Provider>
  )
}
