import React, {useContext, useEffect} from 'react'
import { useLocation } from 'react-router-dom'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Businesses from './pages/Businesses'
import Finance from './pages/Finance'
import Inventory from './pages/Inventory'
import Settings from './pages/Settings'
import AccountantDashboard from './pages/AccountantDashboard'
import StaffDashboard from './pages/StaffDashboard'
import PrivateRoute from './components/PrivateRoute'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { AuthContext } from './contexts/AuthContext'

export default function App(){
  const { user } = useContext(AuthContext)
  const location = useLocation()
  const hideShell = ['/login','/register'].includes(location.pathname)

  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-50 to-white`}>
      <div className="flex">
        {!hideShell && <Sidebar />}
        <div className="flex-1 min-h-screen">
          {!hideShell && <Topbar />}
          <main className="p-6">
            <Routes>
              <Route path="/login" element={<Login/>} />
              <Route path="/register" element={<Register/>} />
              <Route path="/" element={<PrivateRoute><Dashboard/></PrivateRoute>} />
              <Route path="/dashboard" element={<PrivateRoute><Dashboard/></PrivateRoute>} />
              <Route path="/businesses" element={<PrivateRoute><Businesses/></PrivateRoute>} />
              <Route path="/finance" element={<PrivateRoute><Finance/></PrivateRoute>} />
              <Route path="/accountant" element={<PrivateRoute><AccountantDashboard/></PrivateRoute>} />
              <Route path="/staff" element={<PrivateRoute><StaffDashboard/></PrivateRoute>} />
              <Route path="/inventory" element={<PrivateRoute><Inventory/></PrivateRoute>} />
              <Route path="/settings" element={<PrivateRoute><Settings/></PrivateRoute>} />
              <Route path="*" element={<Navigate to={user?'/dashboard':'/login'} />} />
            </Routes>
          </main>
        </div>
      </div>
    </div>
  )
}
