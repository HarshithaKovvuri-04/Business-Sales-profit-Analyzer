import React, {useContext} from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'

export default function PrivateRoute({children}){
  const { user } = useContext(AuthContext)
  const { businesses } = useContext(BusinessContext)
  const location = useLocation()

  if(!user) return <Navigate to="/login" replace />

  // If the user is authenticated but has no businesses (no access),
  // redirect them to the Businesses page so they can create or join one.
  const businessRequiredPaths = ['/', '/dashboard', '/finance', '/inventory']
  if(businessRequiredPaths.includes(location.pathname) && (!businesses || businesses.length === 0)){
    return <Navigate to="/businesses" replace />
  }

  return children
}
