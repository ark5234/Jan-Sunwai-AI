import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import 'leaflet/dist/leaflet.css'
import { installGlobalAxios401Interceptor } from './context/api'

installGlobalAxios401Interceptor()

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const API_ORIGIN = (() => {
  try {
    return new URL(API_BASE, window.location.origin).origin
  } catch {
    return window.location.origin
  }
})()

const nativeFetch = window.fetch.bind(window)
window.fetch = (input, init = {}) => {
  const nextInit = typeof init === 'object' && init !== null ? { ...init } : {}
  if (!Object.prototype.hasOwnProperty.call(nextInit, 'credentials')) {
    try {
      const rawUrl = input instanceof Request ? input.url : String(input)
      const requestUrl = new URL(rawUrl, window.location.origin)
      // Send cookies only to our backend origin; avoid credentialed requests to third-party APIs.
      nextInit.credentials = requestUrl.origin === API_ORIGIN ? 'include' : 'omit'
    } catch {
      nextInit.credentials = 'omit'
    }
  }
  return nativeFetch(input, nextInit)
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
