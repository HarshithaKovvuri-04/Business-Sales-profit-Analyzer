import React, {useContext} from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { AuthContext } from '../contexts/AuthContext'
import { BusinessContext } from '../contexts/BusinessContext'

export default function PrivateRoute({children}){
  const { user, authChecked } = useContext(AuthContext)
  const { businesses } = useContext(BusinessContext)
  const location = useLocation()

  // If we haven't completed the auth check yet, don't redirect prematurely.
  if(!authChecked) return null

  // Allow read-only access for unauthenticated users to main dashboards.
  if(!user){
    const publicAllowedPaths = ['/', '/dashboard', '/finance', '/inventory']
    if(!publicAllowedPaths.includes(location.pathname)) return <Navigate to="/login" replace />
    // otherwise, allow read-only rendering
  }

  // If the user is authenticated but has no businesses (no access),
  // redirect them to the Businesses page so they can create or join one.
  const businessRequiredPaths = ['/', '/dashboard', '/finance', '/inventory']
  if(businessRequiredPaths.includes(location.pathname) && (!businesses || businesses.length === 0)){
    return <Navigate to="/businesses" replace />
  }

  return children
}
