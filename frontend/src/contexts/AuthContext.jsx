import React, {createContext, useEffect, useState} from 'react'
import api from '../api/axios'

export const AuthContext = createContext(null)

export function AuthProvider({children}){
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(()=> localStorage.getItem('bizanalyzer_token'))

  useEffect(()=>{
    if(token){
      // fetch /auth/me
      api.get('/auth/me').then(res=> setUser(res.data)).catch(()=>{
        setUser(null); setToken(null); localStorage.removeItem('bizanalyzer_token')
      })
    }
  }, [token])

  const login = async ({username, password}) =>{
    const res = await api.post('/auth/login', {username, password})
    const t = res.data.access_token
    setToken(t)
    localStorage.setItem('bizanalyzer_token', t)
    const me = await api.get('/auth/me')
    setUser(me.data)
    return me.data
  }

  const register = async ({username, password, role}) =>{
    const res = await api.post('/auth/register', {username, password, role})
    return res.data
  }

  const logout = ()=>{
    setUser(null)
    setToken(null)
    localStorage.removeItem('bizanalyzer_token')
  }

  return (
    <AuthContext.Provider value={{user, token, login, logout, register}}>
      {children}
    </AuthContext.Provider>
  )
}
