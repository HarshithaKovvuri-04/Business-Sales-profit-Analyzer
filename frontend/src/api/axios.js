import axios from 'axios'

// Default to the standardized backend dev port 8003. Can be overridden via VITE_API_BASE.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8002'

const instance = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
})

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('bizanalyzer_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default instance
